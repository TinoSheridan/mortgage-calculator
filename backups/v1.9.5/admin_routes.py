from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app, send_file
from functools import wraps
import logging
import json
import os
from datetime import datetime
from statistics import StatisticsManager  # Correct import from the local module
from VERSION import VERSION  # Import the version number
import copy

# Create a Blueprint for admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Configure logging
logger = logging.getLogger(__name__)

# Constants
CLOSING_COSTS_FILE = 'config/closing_costs.json'
SELLER_CONTRIBUTIONS_FILE = 'config/seller_contributions.json'

# Helper function to add standard context variables to all admin templates
def get_admin_context(**kwargs):
    """Create a context dictionary with standard admin variables including version."""
    context = {
        'version': VERSION,
    }
    context.update(kwargs)
    return context

# Admin login check decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access this page', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Get admin credentials from config
        admin_config = current_app.config_manager.config.get('admin', {})
        valid_username = admin_config.get('username', 'admin')
        valid_password = admin_config.get('password', 'admin123')
        
        if username == valid_username and password == valid_password:
            session['admin_logged_in'] = True
            flash('Successfully logged in', 'success')
            return redirect(url_for('admin.dashboard'))
        
        error = 'Invalid credentials'
        flash(error, 'error')
        return render_template('admin/login.html', error=error)
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Admin logout."""
    session.pop('admin_logged_in', None)
    flash('Successfully logged out', 'success')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
def index():
    """Redirect root to dashboard."""
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard."""
    # Initialize statistics manager if not already done
    if not hasattr(current_app, 'stats_manager'):
        current_app.stats_manager = StatisticsManager()
    
    # Get summary statistics 
    stats = current_app.stats_manager.get_summary_stats()
    
    return render_template('admin/dashboard.html', 
                         active_page='dashboard',
                         stats=stats,
                         **get_admin_context())

@admin_bp.route('/dashboard/data', methods=['GET'])
@admin_required
def dashboard_data():
    """API endpoint for dashboard data."""
    try:
        # Get statistics
        config = current_app.config_manager.config
        health_info = current_app.config_manager.get_system_health()
        
        # Calculate statistics
        stats = {
            'total_calculations': len(current_app.config_manager.calculation_history),
            'active_counties': len(config.get('county_rates', {})),
            'output_templates': len(config.get('output_templates', {})),
            'total_fees': len(config.get('closing_costs', {}))
        }
        
        # System health checks
        health = {
            'config_files': all(health_info['config_files'].values()),
            'database': True,  # Placeholder for future database status
            'cache': True,     # Placeholder for future cache status
            'last_backup': health_info['last_backup']
        }
        
        # Recent changes
        recent_changes = []
        for change in current_app.config_manager.get_recent_changes()[-5:]:
            recent_changes.append({
                'timestamp': change.get('timestamp', ''),
                'description': change.get('description', ''),
                'details': change.get('details', ''),
                'user': change.get('user', 'admin')
            })
        
        # Reverse to show newest first
        recent_changes.reverse()
        
        return jsonify({
            'stats': stats,
            'health': health,
            'recent_changes': recent_changes
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({
            'stats': {'total_calculations': 0, 'active_counties': 0, 'output_templates': 0, 'total_fees': 0},
            'health': {'config_files': False, 'database': False, 'cache': False, 'last_backup': 'Error'},
            'recent_changes': []
        }), 500

@admin_bp.route('/counties')
@admin_required
def counties():
    """County rates management page."""
    county_rates = current_app.config_manager.config.get('county_rates', {})
    return render_template('admin/counties.html', county_rates=county_rates, **get_admin_context())

@admin_bp.route('/counties/add', methods=['POST'])
@admin_required
def add_county():
    """Add a new county."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    # Get current county rates
    county_rates = current_app.config_manager.config.get('county_rates', {})
    
    county_name = data.get('county')
    if not county_name:
        return jsonify({'success': False, 'error': 'County name is required'}), 400
    
    if county_name in county_rates:
        return jsonify({'success': False, 'error': 'County already exists'}), 400
    
    # Validate required fields
    required_fields = ['property_tax_rate', 'insurance_rate']
    for field in required_fields:
        if field not in data:
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    # Add new county
    county_rates[county_name] = {
        'property_tax_rate': float(data.get('property_tax_rate')),
        'insurance_rate': float(data.get('insurance_rate')),
        'min_hoa': float(data.get('min_hoa', 0)),
        'max_hoa': float(data.get('max_hoa', 0))
    }
    
    # Save updated config
    current_app.config_manager.config['county_rates'] = county_rates
    current_app.config_manager.save_config()
    current_app.config_manager.add_change(
        description=f"Added county: {county_name}",
        details=f"Added {county_name} with tax rate {data.get('property_tax_rate')}% and insurance rate {data.get('insurance_rate')}%",
        user="admin"
    )
    
    return jsonify({'success': True})

@admin_bp.route('/counties/edit/<county_name>', methods=['POST'])
@admin_required
def edit_county(county_name):
    """Edit an existing county."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    # Get current county rates
    county_rates = current_app.config_manager.config.get('county_rates', {})
    
    if county_name not in county_rates:
        return jsonify({'success': False, 'error': 'County not found'}), 404
    
    # Update county data
    county_rates[county_name] = {
        'property_tax_rate': float(data.get('property_tax_rate', county_rates[county_name]['property_tax_rate'])),
        'insurance_rate': float(data.get('insurance_rate', county_rates[county_name]['insurance_rate'])),
        'min_hoa': float(data.get('min_hoa', county_rates[county_name].get('min_hoa', 0))),
        'max_hoa': float(data.get('max_hoa', county_rates[county_name].get('max_hoa', 0)))
    }
    
    # Save updated config
    current_app.config_manager.config['county_rates'] = county_rates
    current_app.config_manager.save_config()
    current_app.config_manager.add_change(
        description=f"Updated county: {county_name}",
        details=f"Updated {county_name} with tax rate {data.get('property_tax_rate')}% and insurance rate {data.get('insurance_rate')}%",
        user="admin"
    )
    
    return jsonify({'success': True})

@admin_bp.route('/counties/delete/<county_name>', methods=['POST'])
@admin_required
def delete_county(county_name):
    """Delete an existing county."""
    # Get current county rates
    county_rates = current_app.config_manager.config.get('county_rates', {})
    
    if county_name not in county_rates:
        return jsonify({'success': False, 'error': 'County not found'}), 404
    
    # Delete county
    del county_rates[county_name]
    
    # Save updated config
    current_app.config_manager.config['county_rates'] = county_rates
    current_app.config_manager.save_config()
    current_app.config_manager.add_change(
        description=f"Deleted county: {county_name}",
        details=f"Deleted {county_name} county",
        user="admin"
    )
    
    return jsonify({'success': True})

@admin_bp.route('/compliance')
@admin_required
def compliance():
    """Compliance text management page."""
    compliance_text = current_app.config_manager.config.get('compliance_text', {})
    return render_template('admin/compliance.html', compliance_text=compliance_text, **get_admin_context())

@admin_bp.route('/compliance/add', methods=['POST'])
@admin_required
def add_compliance_text():
    """Add a new compliance text section."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    # Get current compliance text
    compliance_text = current_app.config_manager.config.get('compliance_text', {})
    
    section_name = data.get('section')
    if not section_name:
        return jsonify({'success': False, 'error': 'Section name is required'}), 400
    
    if section_name in compliance_text:
        return jsonify({'success': False, 'error': 'Section already exists'}), 400
    
    # Validate required fields
    if 'text' not in data:
        return jsonify({'success': False, 'error': 'Compliance text is required'}), 400
    
    # Add new section
    compliance_text[section_name] = data.get('text')
    
    # Save updated config
    current_app.config_manager.config['compliance_text'] = compliance_text
    current_app.config_manager.save_config()
    current_app.config_manager.add_change(
        description=f"Added compliance text: {section_name}",
        details=f"Added compliance text section: {section_name}",
        user="admin"
    )
    
    return jsonify({'success': True})

@admin_bp.route('/compliance/edit/<section_name>', methods=['POST'])
@admin_required
def edit_compliance_text(section_name):
    """Edit an existing compliance text section."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    # Get current compliance text
    compliance_text = current_app.config_manager.config.get('compliance_text', {})
    
    if section_name not in compliance_text:
        return jsonify({'success': False, 'error': 'Section not found'}), 404
    
    # Validate required fields
    if 'text' not in data:
        return jsonify({'success': False, 'error': 'Compliance text is required'}), 400
    
    # Update section
    compliance_text[section_name] = data.get('text')
    
    # Save updated config
    current_app.config_manager.config['compliance_text'] = compliance_text
    current_app.config_manager.save_config()
    current_app.config_manager.add_change(
        description=f"Updated compliance text: {section_name}",
        details=f"Updated compliance text section: {section_name}",
        user="admin"
    )
    
    return jsonify({'success': True})

@admin_bp.route('/compliance/delete/<section_name>', methods=['POST'])
@admin_required
def delete_compliance_text(section_name):
    """Delete an existing compliance text section."""
    # Get current compliance text
    compliance_text = current_app.config_manager.config.get('compliance_text', {})
    
    if section_name not in compliance_text:
        return jsonify({'success': False, 'error': 'Section not found'}), 404
    
    # Delete section
    del compliance_text[section_name]
    
    # Save updated config
    current_app.config_manager.config['compliance_text'] = compliance_text
    current_app.config_manager.save_config()
    current_app.config_manager.add_change(
        description=f"Deleted compliance text: {section_name}",
        details=f"Deleted compliance text section: {section_name}",
        user="admin"
    )
    
    return jsonify({'success': True})

@admin_bp.route('/templates')
@admin_required
def templates():
    """Output templates management page."""
    output_templates = current_app.config_manager.config.get('output_templates', {})
    return render_template('admin/templates.html', output_templates=output_templates, **get_admin_context())

@admin_bp.route('/templates/add', methods=['POST'])
@admin_required
def add_template():
    """Add a new output template."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    # Get current templates
    output_templates = current_app.config_manager.config.get('output_templates', {})
    
    template_name = data.get('name')
    if not template_name:
        return jsonify({'success': False, 'error': 'Template name is required'}), 400
    
    if template_name in output_templates:
        return jsonify({'success': False, 'error': 'Template already exists'}), 400
    
    # Validate required fields
    if 'content' not in data:
        return jsonify({'success': False, 'error': 'Template content is required'}), 400
    
    # Add new template
    output_templates[template_name] = {
        'content': data.get('content'),
        'description': data.get('description', ''),
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    # Save updated config
    current_app.config_manager.config['output_templates'] = output_templates
    current_app.config_manager.save_config()
    current_app.config_manager.add_change(
        description=f"Added template: {template_name}",
        details=f"Added output template: {template_name}",
        user="admin"
    )
    
    return jsonify({'success': True})

@admin_bp.route('/templates/edit/<template_name>', methods=['POST'])
@admin_required
def edit_template(template_name):
    """Edit an existing output template."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    # Get current templates
    output_templates = current_app.config_manager.config.get('output_templates', {})
    
    if template_name not in output_templates:
        return jsonify({'success': False, 'error': 'Template not found'}), 404
    
    # Validate required fields
    if 'content' not in data:
        return jsonify({'success': False, 'error': 'Template content is required'}), 400
    
    # Make sure content is not too short
    if len(data.get('content', '').strip()) < 10:
        return jsonify({'success': False, 'error': 'Template content must be at least 10 characters'}), 400
    
    # Get existing template data
    template_data = output_templates.get(template_name, {})
    if isinstance(template_data, str):
        # Convert old format (plain string) to dictionary format
        template_data = {
            'content': template_data,
            'created_at': datetime.now().isoformat()
        }

    # Update template
    template_data.update({
        'content': data.get('content'),
        'description': data.get('description', template_data.get('description', '')),
        'updated_at': datetime.now().isoformat()
    })
    
    output_templates[template_name] = template_data
    
    # Save updated config
    current_app.config_manager.config['output_templates'] = output_templates
    current_app.config_manager.save_config()
    current_app.config_manager.add_change(
        description=f"Updated template: {template_name}",
        details=f"Updated output template: {template_name}",
        user="admin"
    )
    
    return jsonify({'success': True})

@admin_bp.route('/templates/delete/<template_name>', methods=['POST'])
@admin_required
def delete_template(template_name):
    """Delete an existing output template."""
    # Get current templates
    output_templates = current_app.config_manager.config.get('output_templates', {})
    
    if template_name not in output_templates:
        return jsonify({'success': False, 'error': 'Template not found'}), 404
    
    # Delete template
    del output_templates[template_name]
    
    # Save updated config
    current_app.config_manager.config['output_templates'] = output_templates
    current_app.config_manager.save_config()
    current_app.config_manager.add_change(
        description=f"Deleted template: {template_name}",
        details=f"Deleted output template: {template_name}",
        user="admin"
    )
    
    return jsonify({'success': True})

@admin_bp.route('/fees', methods=['GET', 'POST'])
@admin_required
def fees():
    """Fee management page."""
    if request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Get current closing costs
        closing_costs = current_app.config_manager.config.get('closing_costs', {})
        
        # Add new fee
        fee_type = data.get('fee_type')
        if not fee_type:
            return jsonify({'success': False, 'error': 'Fee type is required'}), 400
            
        if fee_type in closing_costs:
            return jsonify({'success': False, 'error': 'Fee already exists'}), 400
        
        closing_costs[fee_type] = {
            'amount': float(data.get('amount', 0)),
            'is_percentage': data.get('is_percentage', 'fixed'),
            'description': data.get('description', '')
        }
        
        # Save updated config
        current_app.config_manager.config['closing_costs'] = closing_costs
        current_app.config_manager.save_config()
        current_app.config_manager.add_change(
            description=f"Added fee: {fee_type}",
            details=f"Added {fee_type} fee with amount {data.get('amount')}",
            user="admin"
        )
        
        return jsonify({'success': True})
    
    closing_costs = current_app.config_manager.config.get('closing_costs', {})
    return render_template('admin/fees.html', fees=closing_costs, **get_admin_context())

@admin_bp.route('/fees/edit/<fee_type>', methods=['POST'])
@admin_required
def edit_fee(fee_type):
    """Edit an existing fee."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    # Get current closing costs
    closing_costs = current_app.config_manager.config.get('closing_costs', {})
    
    if fee_type not in closing_costs:
        return jsonify({'success': False, 'error': 'Fee not found'}), 404
    
    # Update fee
    closing_costs[fee_type] = {
        'amount': float(data.get('amount', closing_costs[fee_type]['amount'])),
        'is_percentage': data.get('is_percentage', closing_costs[fee_type]['is_percentage']),
        'description': data.get('description', closing_costs[fee_type]['description'])
    }
    
    # Save updated config
    current_app.config_manager.config['closing_costs'] = closing_costs
    current_app.config_manager.save_config()
    current_app.config_manager.add_change(
        description=f"Updated fee: {fee_type}",
        details=f"Updated {fee_type} fee with amount {data.get('amount')}",
        user="admin"
    )
    
    return jsonify({'success': True})

@admin_bp.route('/fees/delete/<fee_type>', methods=['POST'])
@admin_required
def delete_fee(fee_type):
    """Delete an existing fee."""
    # Get current closing costs
    closing_costs = current_app.config_manager.config.get('closing_costs', {})
    
    if fee_type not in closing_costs:
        return jsonify({'success': False, 'error': 'Fee not found'}), 404
    
    # Delete fee
    del closing_costs[fee_type]
    
    # Save updated config
    current_app.config_manager.config['closing_costs'] = closing_costs
    current_app.config_manager.save_config()
    current_app.config_manager.add_change(
        description=f"Deleted fee: {fee_type}",
        details=f"Deleted {fee_type} fee",
        user="admin"
    )
    
    return jsonify({'success': True})

@admin_bp.route('/maintenance')
@admin_required
def maintenance():
    """System maintenance page."""
    # Get system health information
    health_info = current_app.config_manager.get_system_health()
    
    # Basic stats
    stats = {
        'calculation_count': health_info.get('calculation_count', 0),
        'total_backups': health_info.get('total_backups', 0),
        'config_files': health_info.get('config_files', {})
    }
    
    return render_template('admin/maintenance.html',
                         health_info=health_info,
                         stats=stats,
                         **get_admin_context())

@admin_bp.route('/maintenance/backup', methods=['POST'])
@admin_required
def create_backup():
    """Create a configuration backup."""
    try:
        success = current_app.config_manager.backup_config()
        if success:
            flash('Backup created successfully', 'success')
            return jsonify({'success': True})
        else:
            flash('Error creating backup', 'error')
            return jsonify({'success': False, 'error': 'Error creating backup'}), 500
    except Exception as e:
        logger.error(f"Error in backup process: {str(e)}")
        flash(f"Error: {str(e)}", 'error')
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/statistics')
@admin_required
def statistics():
    """Usage statistics page."""
    # Initialize statistics manager if needed
    if not hasattr(current_app, 'stats_manager'):
        current_app.stats_manager = StatisticsManager()
    
    # Get summary statistics for template rendering
    stats = current_app.stats_manager.get_summary_stats()
    
    return render_template('admin/statistics.html', stats=stats, **get_admin_context())

@admin_bp.route('/api/statistics/data', methods=['GET'])
@admin_required
def statistics_data():
    """API endpoint for statistics chart data."""
    # Initialize statistics manager if needed
    if not hasattr(current_app, 'stats_manager'):
        current_app.stats_manager = StatisticsManager()
    
    try:
        # Get chart data from statistics manager
        chart_data = current_app.stats_manager.get_chart_data()
        insights = current_app.stats_manager.generate_insights()
        
        return jsonify({
            'success': True,
            'chart_data': chart_data,
            'insights': insights
        })
    except Exception as e:
        logger.error(f"Error getting statistics data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/api/statistics/export', methods=['GET'])
@admin_required
def export_statistics():
    """Export statistics as CSV."""
    # Initialize statistics manager if needed
    if not hasattr(current_app, 'stats_manager'):
        current_app.stats_manager = StatisticsManager()
    
    try:
        # Generate CSV report
        csv_data = current_app.stats_manager.generate_csv_report()
        
        if not csv_data:
            return jsonify({
                'success': False,
                'error': 'No data available for export'
            }), 400
        
        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mortgage_stats_{timestamp}.csv"
        
        # Create a temporary file
        temp_file = os.path.join(current_app.config.get('TEMP_FOLDER', '/tmp'), filename)
        
        with open(temp_file, 'w') as f:
            f.write(csv_data)
        
        return send_file(
            temp_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error exporting statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/api/statistics/purge', methods=['POST'])
@admin_required
def purge_statistics():
    """Purge old statistics data."""
    # Initialize statistics manager if needed
    if not hasattr(current_app, 'stats_manager'):
        current_app.stats_manager = StatisticsManager()
    
    try:
        # Get number of days from request, default to 365
        days = request.json.get('days', 365)
        
        # Validate days parameter
        try:
            days = int(days)
            if days < 1:
                raise ValueError("Days must be positive")
        except ValueError as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400
        
        # Purge old data
        purged_count = current_app.stats_manager.purge_old_data(days)
        
        return jsonify({
            'success': True,
            'message': f"Purged {purged_count} records older than {days} days",
            'purged_count': purged_count
        })
    except Exception as e:
        logger.error(f"Error purging statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@admin_bp.route('/closing-costs')
@admin_required
def closing_costs():
    """Display and manage closing costs."""
    costs = load_closing_costs()
    return render_template('admin/closing_costs.html', 
                         active_page='closing_costs',
                         closing_costs=costs, 
                         **get_admin_context())

@admin_bp.route('/closing-costs/<name>')
@admin_required
def get_closing_cost(name):
    """Get a specific closing cost."""
    costs = load_closing_costs()
    if name in costs:
        return jsonify(costs[name])
    return jsonify({'error': 'Cost not found'}), 404

@admin_bp.route('/closing-costs', methods=['POST'])
@admin_required
def add_closing_cost():
    """Add a new closing cost."""
    data = request.get_json()
    costs = load_closing_costs()
    
    name = data.pop('name').lower().replace(' ', '_')
    if name in costs:
        return jsonify({'success': False, 'error': 'Cost already exists'}), 400
    
    costs[name] = {
        'type': data['type'],
        'value': float(data['value']),
        'calculation_base': data['calculation_base'],
        'description': data['description']
    }
    
    save_closing_costs(costs)
    return jsonify({'success': True})

@admin_bp.route('/closing-costs/<n>', methods=['PUT', 'POST'])  # Support both PUT and POST methods
@admin_required
def update_closing_cost(n):
    """Update an existing closing cost."""
    # Handle both JSON and form data for better compatibility
    if request.is_json:
        data = request.get_json()
        current_app.logger.info(f"Received JSON data: {data}")
    else:
        data = request.form.to_dict()
        current_app.logger.info(f"Received form data: {data}")
        
    if not data:
        current_app.logger.error("Failed to parse data for closing cost update")
        return jsonify({'success': False, 'error': 'Invalid data'}), 400
        
    current_app.logger.info(f"Updating closing cost {n} with data: {data}")
    costs = load_closing_costs()
    
    if n not in costs:
        return jsonify({'success': False, 'error': 'Cost not found'}), 404
    
    new_name = data.pop('name').lower().replace(' ', '_')
    if new_name != n and new_name in costs:
        return jsonify({'success': False, 'error': 'New name already exists'}), 400
    
    if new_name != n:
        costs.pop(n)
    
    costs[new_name] = {
        'type': data['type'],
        'value': float(data['value']),
        'calculation_base': data['calculation_base'],
        'description': data['description']
    }
    
    save_closing_costs(costs)
    return jsonify({'success': True})

@admin_bp.route('/closing-costs/delete/<n>', methods=['POST'])
@admin_required
def delete_closing_cost(n):
    """Delete a closing cost."""
    try:
        costs = load_closing_costs()
        
        if n not in costs:
            return jsonify({'success': False, 'error': 'Cost not found'}), 404
        
        costs.pop(n)
        save_closing_costs(costs)
        return jsonify({'success': True})
    except Exception as e:
        logging.error(f"Error deleting closing cost: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/mortgage-config')
@admin_required
def mortgage_config():
    """Mortgage configuration management page."""
    # Get mortgage configuration from config
    mortgage_config = {
        "loan_types": current_app.config_manager.config.get('loan_types', {}),
        "limits": current_app.config_manager.config.get('loan_limits', {}),
        "prepaid_items": current_app.config_manager.config.get('prepaid_items', {})
    }
    
    # Load seller contributions data
    seller_contributions = {}
    try:
        if os.path.exists(SELLER_CONTRIBUTIONS_FILE):
            with open(SELLER_CONTRIBUTIONS_FILE, 'r') as f:
                seller_contributions = json.load(f)
    except Exception as e:
        logger.error(f"Error loading seller contributions: {e}")
        flash(f"Error loading seller contributions: {e}", "error")
    
    return render_template('admin/mortgage_config.html', 
                          mortgage_config=mortgage_config, 
                          seller_contributions=seller_contributions,
                          active_page='mortgage_config',
                          **get_admin_context())

@admin_bp.route('/mortgage-config/update', methods=['POST'])
@admin_required
def update_mortgage_config():
    """Update mortgage configuration."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    config = current_app.config_manager.config
    
    # Update loan types
    if 'loan_types' in data:
        config['loan_types'] = data['loan_types']
    
    # Update loan limits
    if 'limits' in data:
        config['loan_limits'] = data['limits']
    
    # Update prepaid items
    if 'prepaid_items' in data:
        # Preserve the days_interest_prepaid field from the existing config
        # Even though it's not displayed or editable in the UI anymore
        if 'days_interest_prepaid' not in data['prepaid_items'] and 'days_interest_prepaid' in config['prepaid_items']:
            current_value = config['prepaid_items']['days_interest_prepaid']
            data['prepaid_items']['days_interest_prepaid'] = current_value
            current_app.logger.info(f"Preserved days_interest_prepaid value ({current_value}) in config update")
        
        config['prepaid_items'] = data['prepaid_items']
    
    # Save the updated config
    current_app.config_manager.save_config()
    current_app.config_manager.add_change(
        description="Updated mortgage configuration",
        details="Updated mortgage configuration settings",
        user="admin"
    )
    
    return jsonify({'success': True})

@admin_bp.route('/mortgage-config/prepaid/update', methods=['POST'])
@admin_required
def update_prepaid_items():
    """Update prepaid items configuration."""
    try:
        # Extract form data
        prepaid_items = {}
        
        # Process all form fields for prepaid items
        for key in request.form:
            if key != 'csrf_token':  # Skip CSRF token
                try:
                    # Convert numeric values to float
                    prepaid_items[key] = float(request.form[key])
                except ValueError:
                    return jsonify({
                        'success': False, 
                        'error': f'Invalid value for {key}: must be a number'
                    }), 400
        
        # Get current config and preserve days_interest_prepaid if not in form
        current_config = current_app.config_manager.config
        if 'days_interest_prepaid' not in prepaid_items and 'days_interest_prepaid' in current_config['prepaid_items']:
            prepaid_items['days_interest_prepaid'] = current_config['prepaid_items']['days_interest_prepaid']
            current_app.logger.info(f"Preserved days_interest_prepaid value in prepaid items update")
        
        # Update the configuration
        current_config['prepaid_items'] = prepaid_items
        current_app.config_manager.save_config()
        
        # Log the change
        current_app.config_manager.add_change(
            description="Updated prepaid items configuration",
            details=f"Updated prepaid items: {', '.join(prepaid_items.keys())}",
            user="admin"
        )
        
        return jsonify({'success': True})
    
    except Exception as e:
        current_app.logger.error(f"Error updating prepaid items: {str(e)}")
        return jsonify({'success': False, 'error': f'An error occurred: {str(e)}'}), 500

@admin_bp.route('/mortgage-config/limits/update', methods=['POST'])
@admin_required
def update_loan_limits():
    """Update loan limits configuration."""
    try:
        # Extract form data
        limits = {}
        
        # Process all form fields for limits
        for key in request.form:
            if key != 'csrf_token':  # Skip CSRF token
                try:
                    # Convert numeric values to float
                    limits[key] = float(request.form[key])
                except ValueError:
                    return jsonify({
                        'success': False, 
                        'error': f'Invalid value for {key}: must be a number'
                    }), 400
        
        # Update the configuration
        current_app.config_manager.config['loan_limits'] = limits
        current_app.config_manager.save_config()
        
        # Log the change
        current_app.config_manager.add_change(
            description="Updated loan limits configuration",
            details=f"Updated loan limits: {', '.join(limits.keys())}",
            user="admin"
        )
        
        return jsonify({'success': True})
    
    except Exception as e:
        current_app.logger.error(f"Error updating loan limits: {str(e)}")
        return jsonify({'success': False, 'error': f'An error occurred: {str(e)}'}), 500

@admin_bp.route('/pmi-rates')
@admin_required
def pmi_rates():
    """PMI rates management page."""
    # Get PMI rates from config
    pmi_rates = current_app.config_manager.config.get('pmi_rates', {})
    
    # Ensure each loan type has the expected structure
    for loan_type in pmi_rates:
        if loan_type == 'va':
            # Special structure for VA loans with funding fee
            if 'funding_fee' not in pmi_rates[loan_type]:
                pmi_rates[loan_type]['funding_fee'] = {
                    'active': {
                        'less_than_5': {'first': 2.3, 'subsequent': 3.6},
                        '5_to_10': {'first': 1.65, 'subsequent': 1.65},
                        '10_or_more': {'first': 1.4, 'subsequent': 1.4}
                    },
                    'reserves': {
                        'less_than_5': {'first': 2.3, 'subsequent': 3.6},
                        '5_to_10': {'first': 1.65, 'subsequent': 1.65},
                        '10_or_more': {'first': 1.4, 'subsequent': 1.4}
                    },
                    'disability_exempt': True
                }
        elif loan_type == 'fha':
            # Special structure for FHA loans with upfront and annual MIP
            if 'upfront_mip_rate' not in pmi_rates[loan_type]:
                pmi_rates[loan_type]['upfront_mip_rate'] = 1.75
            
            if 'annual_mip' not in pmi_rates[loan_type]:
                pmi_rates[loan_type]['annual_mip'] = {
                    'long_term': {
                        'standard_amount': {
                            'low_ltv': 0.50,
                            'high_ltv': 0.55
                        },
                        'high_amount': {
                            'low_ltv': 0.70,
                            'high_ltv': 0.75
                        }
                    },
                    'short_term': {
                        'standard_amount': {
                            'low_ltv': 0.15,
                            'high_ltv': 0.40
                        },
                        'high_amount': {
                            'very_low_ltv': 0.15,
                            'low_ltv': 0.40,
                            'high_ltv': 0.65
                        }
                    }
                }
            
            if 'standard_loan_limit' not in pmi_rates[loan_type]:
                pmi_rates[loan_type]['standard_loan_limit'] = 726200
                
            if 'high_cost_loan_limit' not in pmi_rates[loan_type]:
                pmi_rates[loan_type]['high_cost_loan_limit'] = 1089300
        else:
            # Standard structure for conventional, etc.
            if 'ltv_ranges' not in pmi_rates[loan_type]:
                pmi_rates[loan_type]['ltv_ranges'] = {}
            if 'credit_score_adjustments' not in pmi_rates[loan_type]:
                pmi_rates[loan_type]['credit_score_adjustments'] = {}
            # Note: we don't initialize 'annual' as it's format varies by loan type
    
    # Initialize VA loan type if not present
    if 'va' not in pmi_rates:
        pmi_rates['va'] = {
            'funding_fee': {
                'active': {
                    'less_than_5': {'first': 2.3, 'subsequent': 3.6},
                    '5_to_10': {'first': 1.65, 'subsequent': 1.65},
                    '10_or_more': {'first': 1.4, 'subsequent': 1.4}
                },
                'reserves': {
                    'less_than_5': {'first': 2.3, 'subsequent': 3.6},
                    '5_to_10': {'first': 1.65, 'subsequent': 1.65},
                    '10_or_more': {'first': 1.4, 'subsequent': 1.4}
                },
                'disability_exempt': True
            }
        }
    
    # Initialize FHA loan type if not present
    if 'fha' not in pmi_rates:
        pmi_rates['fha'] = {
            'upfront_mip_rate': 1.75,
            'annual_mip': {
                'long_term': {
                    'standard_amount': {
                        'low_ltv': 0.50,
                        'high_ltv': 0.55
                    },
                    'high_amount': {
                        'low_ltv': 0.70,
                        'high_ltv': 0.75
                    }
                },
                'short_term': {
                    'standard_amount': {
                        'low_ltv': 0.15,
                        'high_ltv': 0.40
                    },
                    'high_amount': {
                        'very_low_ltv': 0.15,
                        'low_ltv': 0.40,
                        'high_ltv': 0.65
                    }
                }
            },
            'standard_loan_limit': 726200,
            'high_cost_loan_limit': 1089300
        }
    
    return render_template('admin/pmi_rates.html', pmi_rates=pmi_rates, active_page='pmi_rates', **get_admin_context())

@admin_bp.route('/pmi-rates/data')
@admin_required
def get_pmi_rates():
    """Get PMI rates data as JSON."""
    pmi_rates = current_app.config_manager.config.get('pmi_rates', {})
    return jsonify({'success': True, 'pmi_rates': pmi_rates})

@admin_bp.route('/pmi-rates/update', methods=['POST'])
@admin_required
def update_pmi_rates():
    """Update PMI rates."""
    current_app.logger.info("PMI rates update request received")
    
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            current_app.logger.error("No data provided in PMI rates update")
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Log the incoming data for debugging
        current_app.logger.info(f"Raw data received: {request.data.decode('utf-8')}")
        current_app.logger.info(f"Parsed JSON data: {data}")
        
        # Extract loan_type from the request - this is now a required field
        loan_type = data.get('loan_type')
        if not loan_type:
            current_app.logger.error("No loan_type provided in PMI rates update")
            return jsonify({'success': False, 'error': 'No loan_type provided'}), 400
        
        # Make a deep copy of the existing PMI rates to avoid reference issues
        existing_pmi_rates = copy.deepcopy(current_app.config_manager.config.get('pmi_rates', {}))
        current_app.logger.info(f"Existing PMI rates before update: {existing_pmi_rates}")
        
        # Initialize if loan type doesn't exist yet
        if loan_type not in existing_pmi_rates:
            existing_pmi_rates[loan_type] = {}
            current_app.logger.info(f"Creating new entry for loan type: {loan_type}")
        
        # Handle the data based on loan type
        if loan_type == 'conventional' and 'ltv_ranges' in data:
            current_app.logger.info(f"Updating conventional loan LTV ranges: {data['ltv_ranges']}")
            
            # Convert string rates to float for consistency
            for key, value in data['ltv_ranges'].items():
                current_app.logger.info(f"Processing LTV range {key} with value {value} (type: {type(value).__name__})")
                if isinstance(value, str) and value.strip():
                    try:
                        # Convert to float and round to 3 decimal places
                        data['ltv_ranges'][key] = round(float(value), 3)
                    except ValueError:
                        current_app.logger.warning(f"Could not convert value '{value}' to float for range '{key}'")
                        data['ltv_ranges'][key] = 0.0
                elif value is None or (isinstance(value, str) and not value.strip()):
                    current_app.logger.warning(f"Empty value for range '{key}', defaulting to 0.0")
                    data['ltv_ranges'][key] = 0.0
                else:
                    # Ensure existing float values are also rounded to 3 decimal places
                    data['ltv_ranges'][key] = round(float(value), 3)
            
            # Update just the ltv_ranges for conventional loans, preserve other data
            existing_pmi_rates['conventional']['ltv_ranges'] = data['ltv_ranges']
            
            # Ensure credit_score_adjustments exists
            if 'credit_score_adjustments' not in existing_pmi_rates['conventional']:
                existing_pmi_rates['conventional']['credit_score_adjustments'] = {}
        else:
            # For other loan types, copy all fields except loan_type
            update_data = {k: v for k, v in data.items() if k != 'loan_type'}
            
            # Update the existing data
            existing_pmi_rates[loan_type].update(update_data)
            current_app.logger.info(f"Updated {loan_type} with data: {update_data}")
        
        # Update PMI rates in the config
        current_app.logger.info(f"Final PMI rates structure: {existing_pmi_rates}")
        current_app.config_manager.config['pmi_rates'] = existing_pmi_rates
        
        # Save the updated config
        current_app.logger.info("Saving config to disk")
        current_app.config_manager.save_config()
        
        current_app.logger.info("Adding change record")
        current_app.config_manager.add_change(
            description="Updated PMI rates",
            details="Updated PMI rates configuration",
            user="admin"
        )
        
        current_app.logger.info("PMI rates updated successfully")
        return jsonify({'success': True})
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        current_app.logger.error(f"Error updating PMI rates: {str(e)}")
        current_app.logger.error(f"Traceback: {tb}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/save_seller_contributions', methods=['POST'])
@admin_required
def save_seller_contributions():
    """Save seller contribution limits."""
    try:
        data = request.json
        loan_type = data.get('loan_type')
        contributions = data.get('contributions', {})
        
        if not loan_type:
            return jsonify({'success': False, 'error': 'Loan type is required'}), 400
            
        # Load current seller contributions
        seller_contributions = {}
        if os.path.exists(SELLER_CONTRIBUTIONS_FILE):
            with open(SELLER_CONTRIBUTIONS_FILE, 'r') as f:
                seller_contributions = json.load(f)
        
        # Update the specific loan type's contributions
        seller_contributions[loan_type] = contributions
        
        # Save back to file
        with open(SELLER_CONTRIBUTIONS_FILE, 'w') as f:
            json.dump(seller_contributions, f, indent=2)
            
        logger.info(f"Updated seller contributions for {loan_type}")
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Error saving seller contributions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@admin_bp.route('/conventional-pmi', methods=['GET'])
@admin_required
def conventional_pmi_page():
    """Dedicated page for conventional PMI rates management."""
    pmi_rates = current_app.config_manager.config.get('pmi_rates', {})
    conventional_rates = pmi_rates.get('conventional', {})
    return render_template('admin/conventional_pmi.html', 
                          pmi_rates=conventional_rates,
                          version=current_app.config.get('VERSION', '1.0'))

@admin_bp.route('/conventional-pmi/update', methods=['POST'])
@admin_required
def update_conventional_pmi():
    """Update just the conventional PMI rates."""
    current_app.logger.info("Conventional PMI rates update request received")
    
    try:
        # Get form data directly
        data = request.form.to_dict()
        current_app.logger.info(f"Raw form data: {data}")
        
        # Initialize the rates structure
        ltv_ranges = {}
        
        # Process each LTV range/rate pair
        for key, value in data.items():
            if key.startswith('ltv_range_'):
                # Extract the index from the key (ltv_range_1, ltv_range_2, etc.)
                index = key.split('_')[-1]
                range_value = value.strip()
                rate_key = f'ltv_rate_{index}'
                
                # Get the corresponding rate
                if rate_key in data:
                    try:
                        rate_value = float(data[rate_key])
                        if range_value and rate_value >= 0:
                            ltv_ranges[range_value] = round(rate_value, 3)
                            current_app.logger.info(f"Added LTV range: {range_value} = {rate_value}")
                    except ValueError:
                        current_app.logger.warning(f"Invalid rate value for {rate_key}: {data[rate_key]}")
        
        # Get existing PMI rates
        existing_pmi_rates = copy.deepcopy(current_app.config_manager.config.get('pmi_rates', {}))
        
        # Ensure conventional exists
        if 'conventional' not in existing_pmi_rates:
            existing_pmi_rates['conventional'] = {}
        
        # Update the LTV ranges
        existing_pmi_rates['conventional']['ltv_ranges'] = ltv_ranges
        
        # Ensure credit_score_adjustments exists
        if 'credit_score_adjustments' not in existing_pmi_rates['conventional']:
            existing_pmi_rates['conventional']['credit_score_adjustments'] = {}
        
        # Update the config
        current_app.logger.info(f"Updating PMI rates: {existing_pmi_rates}")
        current_app.config_manager.config['pmi_rates'] = existing_pmi_rates
        current_app.config_manager.save_config()
        
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f"Error updating conventional PMI rates: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def load_closing_costs():
    """Load closing costs from JSON file."""
    try:
        with open(CLOSING_COSTS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_closing_costs(costs):
    """Save closing costs to JSON file."""
    os.makedirs(os.path.dirname(CLOSING_COSTS_FILE), exist_ok=True)
    with open(CLOSING_COSTS_FILE, 'w') as f:
        json.dump(costs, f, indent=4)
