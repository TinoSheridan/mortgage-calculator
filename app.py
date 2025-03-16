from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from datetime import timedelta
from dotenv import load_dotenv
from functools import wraps
import os
import json
import logging
from calculator import MortgageCalculator
from config_manager import ConfigManager
from forms import LoginForm
from admin_routes import admin_bp, load_closing_costs, save_closing_costs
from chat_routes import chat_bp
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')
app.config['WTF_CSRF_ENABLED'] = True
CORS(app)

# Add response header to prevent caching
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
app.permanent_session_lifetime = timedelta(days=5)

# Load calculator configuration
calculator = MortgageCalculator()
config_manager = ConfigManager()
config_manager.load_config()  # Load the config
config = config_manager.get_config()  # Get the loaded config

# Register admin blueprint
app.register_blueprint(admin_bp)
# Register chat blueprint
app.register_blueprint(chat_bp)
app.config_manager = config_manager

# Admin authentication
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Render the main calculator page."""
    # Get configuration limits
    limits = config.get('limits', {})
    
    # Default parameters
    params = {
        'purchase_price': 400000,
        'down_payment_percentage': 20,
        'annual_rate': 6.5,  # Using the consistent parameter name from calculator.calculate_all
        'loan_term': 30,
        'annual_tax_rate': 1.0,
        'annual_insurance_rate': 0.35,
        'credit_score': 740,
        'loan_type': 'conventional',
        'hoa_fee': 0,
        'seller_credit': 0,
        'lender_credit': 0,
        'discount_points': 0
    }
    
    # Get min/max values for validation
    min_purchase = limits.get('min_purchase_price', 50000)
    max_purchase = limits.get('max_purchase_price', 2000000)
    max_rate = limits.get('max_interest_rate', 15.0)
    
    return render_template('index.html', 
                          params=params,
                          min_purchase=min_purchase,
                          max_purchase=max_purchase,
                          max_rate=max_rate)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Handle admin login."""
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Hard-coded admin credentials (replace with proper auth in production)
        if username == 'admin' and password == 'password':
            session['admin_logged_in'] = True
            session.permanent = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    
    return render_template('admin/login.html', form=form)

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Admin dashboard."""
    # Get configuration for display
    parameters = {
        'Loan Types': config.get('loan_types', {}),
        'Loan Limits': config.get('limits', {}),
        'PMI Rates': config.get('pmi_rates', {}),
        'Closing Costs': config.get('closing_costs', {}),
        'Prepaid Items': config.get('prepaid_items', {})
    }
    
    return render_template('admin/dashboard.html',
                         parameters=parameters,
                         active_page='dashboard')

@app.route('/admin/logout')
def admin_logout():
    """Handle admin logout."""
    session.pop('admin_logged_in', None)
    flash('Successfully logged out!', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/closing-costs')
@admin_required
def admin_closing_costs():
    """Admin closing costs management page."""
    app.logger.info("Loading closing costs for admin page")
    
    # Extract closing costs from config and transform for template
    closing_costs = {}
    
    # Get raw data from configuration
    costs_data = config.get('closing_costs', {})
    app.logger.info(f"Found {len(costs_data)} closing costs in configuration")
    
    # Transform for template
    for cost_id, cost_details in costs_data.items():
        closing_costs[cost_id] = {
            'name': cost_id.replace('_', ' ').title(),
            'amount': cost_details.get('value', 0),
            'is_percentage': 'percentage' if cost_details.get('type') == 'percentage' else 'fixed',
            'calculation_base': cost_details.get('calculation_base', 'fixed'),
            'description': cost_details.get('description', '')
        }
    
    # If no closing costs found, provide default examples
    if not closing_costs:
        app.logger.warning("No closing costs found in config, using defaults")
        closing_costs = {
            'origination_fee': {
                'name': 'Origination Fee',
                'amount': 1.0,
                'is_percentage': 'percentage',
                'calculation_base': 'loan_amount',
                'description': 'Fee charged by the lender for processing the loan'
            },
            'appraisal_fee': {
                'name': 'Appraisal Fee',
                'amount': 500,
                'is_percentage': 'fixed',
                'calculation_base': 'fixed',
                'description': 'Fee for professional property appraisal'
            }
        }
    
    return render_template('admin/closing_costs.html', closing_costs=closing_costs, active_page='closing_costs')

@app.route('/admin/update', methods=['POST'])
def admin_update():
    """Update configuration values."""
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'error': 'Not authorized'}), 401
        
    try:
        data = request.get_json()
        section = data.get('section')
        updates = data.get('updates', {})
        
        if section in config:
            # Update the specified section in the configuration
            if isinstance(config[section], dict):
                config[section].update(updates)
            else:
                config[section] = updates
        else:
            return jsonify({'success': False, 'error': 'Invalid section'}), 400
            
        config_manager.save_config(config)
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error updating configuration: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/closing-costs/add', methods=['POST'])
@admin_required
def admin_add_closing_cost():
    """Add a new closing cost to the configuration."""
    try:
        app.logger.info("Adding new closing cost")
        app.logger.debug(f"Request data: {request.form}")
        app.logger.debug(f"Request JSON: {request.get_json(silent=True)}")
        app.logger.debug(f"Request headers: {request.headers}")
        
        # Get data from either form data or JSON
        data = {}
        if request.form:
            # Handle form data
            data = request.form.to_dict()
            app.logger.info(f"Received form data: {data}")
        elif request.is_json:
            # Handle JSON data
            data = request.get_json()
            app.logger.info(f"Received JSON data: {data}")
        else:
            app.logger.warning("No data received in request")
            return jsonify({'error': 'No data received'}), 400
            
        app.logger.debug(f"Processing data: {data}")
        
        # Validate required fields
        required_fields = ['name', 'value', 'type', 'calculation_base']
        for field in required_fields:
            if field not in data or not data[field]:
                app.logger.warning(f"Missing required field: {field}")
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Convert inputs to appropriate types
        try:
            value = float(data['value'])
        except (ValueError, TypeError):
            app.logger.warning(f"Invalid value format: {data['value']}")
            return jsonify({'error': 'Amount must be a valid number'}), 400
        
        # Create cost ID from name (lowercase with underscores)
        cost_id = data['name'].lower().replace(' ', '_')
        
        # Get current closing costs
        costs = config.get('closing_costs', {})
        
        # Check if cost already exists
        if cost_id in costs:
            app.logger.warning(f"Cost already exists: {cost_id}")
            return jsonify({'error': f'A closing cost with this name already exists'}), 400
        
        # Add new cost using the correct format that matches the configuration file
        costs[cost_id] = {
            'type': data['type'],
            'value': value,
            'calculation_base': data['calculation_base'],
            'description': data.get('description', '')
        }
        
        # Save to configuration
        config['closing_costs'] = costs
        config_manager.save_config(config)
        app.logger.info(f"Added new closing cost: {cost_id}")
        
        return jsonify({'success': True, 'message': 'Closing cost added successfully'}), 200
    except Exception as e:
        app.logger.error(f"Error adding closing cost: {str(e)}", exc_info=True)
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/admin/closing-costs/update/<cost_name>', methods=['POST'])
@admin_required
def admin_update_closing_cost(cost_name):
    """Update an existing closing cost."""
    try:
        app.logger.info(f"Updating closing cost: {cost_name}")
        app.logger.debug(f"Request data: {request.form}")
        app.logger.debug(f"Request JSON: {request.get_json(silent=True)}")
        app.logger.debug(f"Request headers: {request.headers}")
        
        # Get data from either form data or JSON
        data = {}
        if request.form:
            # Handle form data
            data = request.form.to_dict()
            app.logger.info(f"Received form data: {data}")
        elif request.is_json:
            # Handle JSON data
            data = request.get_json()
            app.logger.info(f"Received JSON data: {data}")
        else:
            app.logger.warning("No data received in request")
            return jsonify({'error': 'No data received'}), 400
            
        app.logger.debug(f"Processing data: {data}")
        
        # Validate required fields
        required_fields = ['name', 'value', 'type', 'calculation_base']
        for field in required_fields:
            if field not in data or not data[field]:
                app.logger.warning(f"Missing required field: {field}")
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Convert inputs to appropriate types
        try:
            value = float(data['value'])
        except (ValueError, TypeError):
            app.logger.warning(f"Invalid value format: {data['value']}")
            return jsonify({'error': 'Amount must be a valid number'}), 400
            
        # Get current closing costs from the dedicated file using admin_routes function
        costs = load_closing_costs()
        
        # Check if cost exists
        if cost_name not in costs:
            app.logger.warning(f"Cost not found: {cost_name}")
            return jsonify({'error': f'Closing cost not found: {cost_name}'}), 404
        
        # Update cost - using the correct JSON structure matching the configuration file
        costs[cost_name] = {
            'type': data['type'],
            'value': value,
            'calculation_base': data['calculation_base'],
            'description': data.get('description', '')
        }
        
        # Save to the dedicated closing costs file
        save_closing_costs(costs)
        app.logger.info(f"Updated closing cost: {cost_name}")
        
        return jsonify({'success': True, 'message': 'Closing cost updated successfully'}), 200
    except Exception as e:
        app.logger.error(f"Error updating closing cost: {str(e)}", exc_info=True)
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/admin/closing-costs/delete/<cost_name>', methods=['POST'])
@admin_required
def admin_delete_closing_cost(cost_name):
    """Delete a closing cost."""
    try:
        app.logger.info(f"Deleting closing cost: {cost_name}")
        
        # Get current closing costs from the dedicated file
        costs = load_closing_costs()
        
        # Check if cost exists
        if cost_name not in costs:
            app.logger.warning(f"Cost not found: {cost_name}")
            return jsonify({'error': 'Cost not found'}), 404
            
        # Remove the cost
        del costs[cost_name]
        
        # Save updated costs
        save_closing_costs(costs)
        app.logger.info(f"Deleted closing cost: {cost_name}")
        
        return jsonify({'success': True, 'message': 'Closing cost deleted successfully'}), 200
    except Exception as e:
        app.logger.error(f"Error deleting closing cost: {str(e)}", exc_info=True)
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/admin/fees')
@admin_required
def admin_fees():
    """Admin fee configuration page."""
    return render_template('admin/fees.html',
                         fees=config.get('fees', {}),
                         active_page='fees')

@app.route('/admin/counties')
@admin_required
def admin_counties():
    """Admin county rates management page."""
    return render_template('admin/counties.html',
                         county_rates=config.get('county_rates', {}),
                         active_page='counties')

@app.route('/admin/compliance')
@admin_required
def admin_compliance():
    """Admin compliance text management page."""
    return render_template('admin/compliance.html',
                         compliance_text=config.get('compliance_text', {}),
                         active_page='compliance')

@app.route('/admin/templates')
@admin_required
def admin_templates():
    """Admin output templates management page."""
    return render_template('admin/templates.html',
                         output_templates=config.get('output_templates', {}),
                         active_page='templates')

@app.route('/admin/fees/update', methods=['POST'])
@admin_required
def admin_update_fees():
    """Update fee configuration."""
    try:
        data = request.get_json()
        fee_updates = data.get('fees', {})
        
        if not isinstance(fee_updates, dict):
            return jsonify({'success': False, 'error': 'Invalid fee data format'}), 400
            
        config['fees'] = fee_updates
        config_manager.save_config(config)
        
        app.logger.info(f"Updated fee configuration: {fee_updates}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error updating fees: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/counties/update', methods=['POST'])
@admin_required
def admin_update_county_rates():
    """Update county-specific rates."""
    try:
        data = request.get_json()
        county = data.get('county')
        rates = data.get('rates', {})
        
        if not county or not isinstance(rates, dict):
            return jsonify({'success': False, 'error': 'Invalid county rate data'}), 400
            
        if 'county_rates' not in config:
            config['county_rates'] = {}
            
        config['county_rates'][county] = rates
        config_manager.save_config(config)
        
        app.logger.info(f"Updated rates for county {county}: {rates}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error updating county rates: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/compliance/update', methods=['POST'])
@admin_required
def admin_update_compliance():
    """Update compliance text."""
    try:
        data = request.get_json()
        section = data.get('section')
        text = data.get('text')
        
        if not section or not text:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        if 'compliance_text' not in config:
            config['compliance_text'] = {}
            
        config['compliance_text'][section] = text
        config_manager.save_config(config)
        
        app.logger.info(f"Updated compliance text for section {section}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error updating compliance text: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/templates/update', methods=['POST'])
@admin_required
def admin_update_templates():
    """Update output templates."""
    try:
        data = request.get_json()
        template_name = data.get('name')
        template_content = data.get('content')
        
        if not template_name or not template_content:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        if 'output_templates' not in config:
            config['output_templates'] = {}
            
        config['output_templates'][template_name] = template_content
        config_manager.save_config(config)
        
        app.logger.info(f"Updated template: {template_name}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error updating template: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/counties/add', methods=['POST'])
@admin_required
def admin_add_county():
    """Add a new county configuration."""
    try:
        data = request.get_json()
        county = data.get('county')
        property_tax_rate = float(data.get('property_tax_rate', 0))
        insurance_rate = float(data.get('insurance_rate', 0))
        min_hoa = float(data.get('min_hoa', 0))
        max_hoa = float(data.get('max_hoa', 0))
        
        if not county:
            return jsonify({'success': False, 'error': 'Missing county name'}), 400
            
        if 'county_rates' not in config:
            config['county_rates'] = {}
            
        if county in config['county_rates']:
            return jsonify({'success': False, 'error': 'County already exists'}), 400
            
        config['county_rates'][county] = {
            'property_tax_rate': property_tax_rate,
            'insurance_rate': insurance_rate,
            'min_hoa': min_hoa,
            'max_hoa': max_hoa
        }
        
        config_manager.save_config(config)
        app.logger.info(f"Added new county configuration: {county}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error adding county: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/counties/delete/<county>', methods=['POST'])
@admin_required
def admin_delete_county(county):
    """Delete a county configuration."""
    try:
        if county not in config.get('county_rates', {}):
            return jsonify({'success': False, 'error': 'County not found'}), 404
            
        del config['county_rates'][county]
        config_manager.save_config(config)
        
        app.logger.info(f"Deleted county configuration: {county}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error deleting county: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/compliance/add', methods=['POST'])
@admin_required
def admin_add_compliance():
    """Add a new compliance text section."""
    try:
        data = request.get_json()
        section = data.get('section')
        text = data.get('text')
        
        if not section or not text:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        if 'compliance_text' not in config:
            config['compliance_text'] = {}
            
        if section in config['compliance_text']:
            return jsonify({'success': False, 'error': 'Section already exists'}), 400
            
        config['compliance_text'][section] = text
        config_manager.save_config(config)
        
        app.logger.info(f"Added new compliance section: {section}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error adding compliance section: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/compliance/delete/<section>', methods=['POST'])
@admin_required
def admin_delete_compliance(section):
    """Delete a compliance text section."""
    try:
        if section not in config.get('compliance_text', {}):
            return jsonify({'success': False, 'error': 'Section not found'}), 404
            
        del config['compliance_text'][section]
        config_manager.save_config(config)
        
        app.logger.info(f"Deleted compliance section: {section}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error deleting compliance section: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/templates/add', methods=['POST'])
@admin_required
def admin_add_template():
    """Add a new output template."""
    try:
        data = request.get_json()
        name = data.get('name')
        content = data.get('content')
        
        if not name or not content:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        if 'output_templates' not in config:
            config['output_templates'] = {}
            
        if name in config['output_templates']:
            return jsonify({'success': False, 'error': 'Template already exists'}), 400
            
        config['output_templates'][name] = content
        config_manager.save_config(config)
        
        app.logger.info(f"Added new output template: {name}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error adding template: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/templates/delete/<template_name>', methods=['POST'])
@admin_required
def admin_delete_template(template_name):
    """Delete an output template."""
    try:
        if template_name not in config.get('output_templates', {}):
            return jsonify({'success': False, 'error': 'Template not found'}), 404
            
        del config['output_templates'][template_name]
        config_manager.save_config(config)
        
        app.logger.info(f"Deleted output template: {template_name}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error deleting template: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/counties/edit/<county>', methods=['POST'])
@admin_required
def admin_edit_county(county):
    """Edit a county configuration."""
    try:
        if county not in config.get('county_rates', {}):
            return jsonify({'success': False, 'error': 'County not found'}), 404
            
        data = request.get_json()
        property_tax_rate = float(data.get('property_tax_rate', 0))
        insurance_rate = float(data.get('insurance_rate', 0))
        min_hoa = float(data.get('min_hoa', 0))
        max_hoa = float(data.get('max_hoa', 0))
        
        config['county_rates'][county] = {
            'property_tax_rate': property_tax_rate,
            'insurance_rate': insurance_rate,
            'min_hoa': min_hoa,
            'max_hoa': max_hoa
        }
        
        config_manager.save_config(config)
        app.logger.info(f"Updated county configuration: {county}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error updating county: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/compliance/edit/<section>', methods=['POST'])
@admin_required
def admin_edit_compliance(section):
    """Edit a compliance text section."""
    try:
        if section not in config.get('compliance_text', {}):
            return jsonify({'success': False, 'error': 'Section not found'}), 404
            
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        config['compliance_text'][section] = text
        config_manager.save_config(config)
        
        app.logger.info(f"Updated compliance section: {section}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error updating compliance section: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/templates/edit/<template_name>', methods=['POST'])
@admin_required
def admin_edit_template(template_name):
    """Edit an output template."""
    try:
        if template_name not in config.get('output_templates', {}):
            return jsonify({'success': False, 'error': 'Template not found'}), 404
            
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
        config['output_templates'][template_name] = content
        config_manager.save_config(config)
        
        app.logger.info(f"Updated output template: {template_name}")
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error updating template: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@csrf.exempt
@app.route('/calculate', methods=['POST'])
def calculate():
    """Main calculation endpoint that returns complete mortgage details."""
    try:
        data = request.get_json()
        app.logger.info(f"Received calculation request with data: {data}")
        
        # Extract parameters
        purchase_price = float(data.get('purchase_price', 0))
        down_payment_percentage = float(data.get('down_payment_percentage', 0))
        annual_rate = float(data.get('annual_rate', 0))
        loan_term = int(data.get('loan_term', 30))
        annual_tax_rate = float(data.get('annual_tax_rate', 0))
        annual_insurance_rate = float(data.get('annual_insurance_rate', 0))
        credit_score = int(data.get('credit_score', 740))
        loan_type = data.get('loan_type', 'conventional')
        monthly_hoa_fee = float(data.get('monthly_hoa_fee', 0))
        seller_credit = float(data.get('seller_credit', 0))
        lender_credit = float(data.get('lender_credit', 0))
        discount_points = float(data.get('discount_points', 0))
        
        # Get optional closing date
        closing_date_str = data.get('closing_date')
        closing_date = None
        if closing_date_str:
            try:
                # Parse ISO format date string (YYYY-MM-DD)
                closing_date = datetime.strptime(closing_date_str, '%Y-%m-%d').date()
                app.logger.info(f"Using closing date: {closing_date}")
            except Exception as e:
                app.logger.warning(f"Could not parse closing date '{closing_date_str}': {e}")
        
        # Extract specific parameters for different loan types
        va_params = {}
        if loan_type.lower() == 'va':
            app.logger.info(f"Processing VA loan with parameters: service_type={data.get('va_service_type')}, "
                            f"usage={data.get('va_usage')}, "
                            f"disability_exempt={data.get('va_disability_exempt')}")
            
            va_params = {
                'va_service_type': data.get('va_service_type', 'active'),
                'va_usage': data.get('va_usage', 'first'),
                'va_disability_exempt': data.get('va_disability_exempt', False)
            }
        
        # Create a fresh calculator instance with latest config
        calculator = MortgageCalculator()
        # Force reload of configuration to ensure latest changes are used
        calculator.config_manager.load_config()
        calculator.config = calculator.config_manager.get_config()
        app.logger.info("Using freshly loaded configuration for main calculation")
        
        # Convert down payment percentage to amount
        down_payment_amount = purchase_price * (down_payment_percentage / 100)
        
        # Calculate results
        result = calculator.calculate_all(
            purchase_price=purchase_price,
            down_payment=down_payment_amount,
            annual_rate=annual_rate,
            loan_term=loan_term,
            annual_tax_rate=annual_tax_rate,
            annual_insurance_rate=annual_insurance_rate,
            credit_score=credit_score,
            loan_type=loan_type,
            hoa_fee=monthly_hoa_fee,
            seller_credit=seller_credit,
            lender_credit=lender_credit,
            discount_points=discount_points,
            closing_date=closing_date,
            **va_params
        )
        
        # Format the response for the frontend
        formatted_result = {
            'success': True,
            'monthly_payment': result['monthly_payment']['total'],
            'loan_amount': result['loan_details']['loan_amount'],
            'down_payment': result['loan_details']['down_payment'],
            'monthly_mortgage': result['monthly_payment']['principal_and_interest'],
            'monthly_tax': result['monthly_payment']['property_tax'],
            'monthly_insurance': result['monthly_payment']['home_insurance'],
            'monthly_pmi': result['monthly_payment']['mortgage_insurance'],
            'monthly_hoa': result['monthly_payment']['hoa_fee'],
            'closing_costs': result['closing_costs'],
            'prepaids': result['prepaid_items'],  
            'monthly_breakdown': {
                'principal_interest': result['monthly_payment']['principal_and_interest'],
                'property_tax': result['monthly_payment']['property_tax'],
                'home_insurance': result['monthly_payment']['home_insurance'],
                'mortgage_insurance': result['monthly_payment']['mortgage_insurance'],
                'hoa_fee': result['monthly_payment']['hoa_fee'],
                'total': result['monthly_payment']['total']
            },
            'loan_details': result['loan_details'],
            'credits': {
                'seller_credit': seller_credit,
                'lender_credit': lender_credit,
                'total': seller_credit + lender_credit
            },
            # Calculate total cash needed if not in the result, making sure to subtract credits
            'total_cash_needed': result.get('cash_to_close', 
                                          result['loan_details']['down_payment'] + 
                                          result['closing_costs'].get('total', 0) + 
                                          result['prepaid_items'].get('total', 0) - 
                                          (seller_credit + lender_credit))
        }
        
        return jsonify(formatted_result)
    except ValueError as e:
        app.logger.error(f"Value error in calculate: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error in calculate: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

@app.route('/admin/dashboard/data')
@admin_required
def admin_dashboard_data():
    """Get dashboard statistics and system health data."""
    try:
        # Gather statistics
        stats = {
            'total_calculations': len(config_manager.get_calculation_history()),
            'active_counties': len(config.get('county_rates', {})),
            'output_templates': len(config.get('output_templates', {})),
            'total_fees': len(config.get('closing_costs', {}))
        }

        # Get recent changes
        recent_changes = config_manager.get_recent_changes()

        # Check system health
        health = {
            'config_files': all([
                os.path.exists(os.path.join(config_manager.config_dir, 'mortgage_config.json')),
                os.path.exists(os.path.join(config_manager.config_dir, 'pmi_rates.json')),
                os.path.exists(os.path.join(config_manager.config_dir, 'closing_costs.json')),
                os.path.exists(os.path.join(config_manager.config_dir, 'county_rates.json')),
                os.path.exists(os.path.join(config_manager.config_dir, 'compliance_text.json')),
                os.path.exists(os.path.join(config_manager.config_dir, 'output_templates.json'))
            ]),
            'database': True,  # Placeholder for future database health check
            'cache': True,     # Placeholder for future cache health check
            'last_backup': config_manager.get_last_backup_time()
        }

        return jsonify({
            'stats': stats,
            'recent_changes': recent_changes,
            'health': health
        })
    except Exception as e:
        app.logger.error(f"Error getting dashboard data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/quick_calc')
def quick_calc():
    return render_template('quick_calc.html')

@csrf.exempt
@app.route('/api/quick_calculate', methods=['POST'])
def quick_calculate():
    """API endpoint for quick mortgage calculations."""
    try:
        data = request.get_json()
        app.logger.info(f"Received quick_calculate request with data: {data}")
        
        purchase_price = float(data.get('purchase_price', 0))
        down_payment = float(data.get('down_payment', 0))
        annual_rate = float(data.get('annual_rate', 0))
        loan_term = int(data.get('loan_term', 30))
        annual_tax_rate = float(data.get('annual_tax_rate', 0))
        annual_insurance_rate = float(data.get('annual_insurance_rate', 0))
        credit_score = int(data.get('credit_score', 740))
        hoa_fee = float(data.get('hoa_fee', 0))
        loan_type = data.get('loan_type', 'conventional')
        seller_credit = float(data.get('seller_credit', 0))
        lender_credit = float(data.get('lender_credit', 0))
        discount_points = float(data.get('discount_points', 0))
        
        # Extract specific parameters for different loan types
        va_params = {}
        if loan_type.lower() == 'va':
            app.logger.info(f"Processing VA loan with parameters: service_type={data.get('va_service_type')}, "
                            f"usage={data.get('va_usage')}, "
                            f"disability_exempt={data.get('va_disability_exempt')}")
            
            va_params = {
                'va_service_type': data.get('va_service_type', 'active'),
                'va_usage': data.get('va_usage', 'first'),
                'va_disability_exempt': data.get('va_disability_exempt', False)
            }
            
            # Validate VA parameters
            if not va_params['va_service_type'] or not va_params['va_usage']:
                error_msg = f"Missing required VA parameters: service_type={va_params['va_service_type']}, usage={va_params['va_usage']}"
                app.logger.error(error_msg)
                return jsonify({'error': error_msg})
        
        # Note: USDA doesn't require special parameters as the rates are fixed
        
        # Create a fresh calculator instance with latest config
        calculator = MortgageCalculator()
        # Force reload of configuration to ensure latest changes are used
        calculator.config_manager.load_config()
        calculator.config = calculator.config_manager.get_config()
        app.logger.info("Using freshly loaded configuration for calculation")
        
        result = calculator.calculate_all(
            purchase_price=purchase_price,
            down_payment=down_payment,
            annual_rate=annual_rate,
            loan_term=loan_term,
            annual_tax_rate=annual_tax_rate,
            annual_insurance_rate=annual_insurance_rate,
            credit_score=credit_score,
            loan_type=loan_type,
            hoa_fee=hoa_fee,
            seller_credit=seller_credit,
            lender_credit=lender_credit,
            discount_points=discount_points,
            **va_params
        )
        
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Error in quick_calculate: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

if __name__ == '__main__':
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Start the Mortgage Calculator web application')
    parser.add_argument('--port', type=int, default=8036, help='Port to run the server on')
    args = parser.parse_args()
    
    try:
        app.logger.info(f"Starting server on port {args.port}")
        app.run(host='127.0.0.1', port=args.port, debug=True, use_reloader=False)
    except OSError as e:
        if "Address already in use" in str(e):
            app.logger.error(f"Port {args.port} is already in use. Please specify a different port using --port.")
        else:
            app.logger.error(f"Error starting server: {e}")
