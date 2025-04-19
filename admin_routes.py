import copy
import json
import logging
import os
from datetime import datetime
from functools import wraps
from statistics import StatisticsManager  # Correct import from the local module

from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)

from VERSION import VERSION  # Import the version number

# Create a Blueprint for admin routes
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Configure logging
logger = logging.getLogger(__name__)

# Constants
CLOSING_COSTS_FILE = "config/closing_costs.json"
SELLER_CONTRIBUTIONS_FILE = "config/seller_contributions.json"


# Helper function to add standard context variables to all admin templates
def get_admin_context(**kwargs):
    """Create a context dictionary with standard admin variables including version."""
    context = {
        "version": VERSION,
    }
    context.update(kwargs)
    return context


# Admin login check decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TEMPORARY: Auto-login for admin during development
        # Remove this line and uncomment the next section for production
        session["admin_logged_in"] = True

        # Production version - uncomment when ready
        # if not session.get("admin_logged_in"):
        #     flash("Please log in to access this page", "error")
        #     return redirect(url_for("admin.login"))
        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    """Admin login page."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Get admin credentials from config
        admin_config = current_app.config_manager.config.get("admin", {})
        valid_username = admin_config.get("username", "admin")
        valid_password = admin_config.get("password", "admin123")

        # Debug information
        print(f"Login attempt - Username: {username}, Valid username: {valid_username}")
        print(f"Login attempt - Password matches: {password == valid_password}")

        if username == valid_username and password == valid_password:
            # Set session variable and ensure it persists
            session["admin_logged_in"] = True
            session.permanent = True
            print(f"Session after login: {dict(session)}")

            flash("Successfully logged in", "success")
            return redirect(url_for("admin.dashboard"))

        error = "Invalid credentials"
        flash(error, "error")
        return render_template("admin/login.html", error=error)

    # Debug: show existing session data
    print(f"Current session data: {dict(session)}")
    return render_template("admin/login.html")


@admin_bp.route("/logout")
def logout():
    """Admin logout."""
    session.pop("admin_logged_in", None)
    flash("Successfully logged out", "success")
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
def index():
    """Redirect root to dashboard."""
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    """Admin dashboard."""
    # Initialize statistics manager if not already done
    if not hasattr(current_app, "stats_manager"):
        current_app.stats_manager = StatisticsManager()

    # Get summary statistics
    stats = current_app.stats_manager.get_summary_stats()

    return render_template(
        "admin/dashboard.html",
        active_page="dashboard",
        stats=stats,
        **get_admin_context(),
    )


@admin_bp.route("/dashboard/data", methods=["GET"])
@admin_required
def dashboard_data():
    """API endpoint for dashboard data."""
    try:
        # Get statistics
        config = current_app.config_manager.config
        health_info = current_app.config_manager.get_system_health()

        # Calculate statistics
        stats = {
            "total_calculations": len(current_app.config_manager.calculation_history),
            "active_counties": len(config.get("county_rates", {})),
            "output_templates": len(config.get("output_templates", {})),
            "total_fees": len(config.get("closing_costs", {})),
        }

        # System health checks
        health = {
            "config_files": all(health_info["config_files"].values()),
            "database": True,  # Placeholder for future database status
            "cache": True,  # Placeholder for future cache status
            "last_backup": health_info["last_backup"],
        }

        # Recent changes
        recent_changes = []
        for change in current_app.config_manager.get_recent_changes()[-5:]:
            recent_changes.append(
                {
                    "timestamp": change.get("timestamp", ""),
                    "description": change.get("description", ""),
                    "details": change.get("details", ""),
                    "user": change.get("user", "admin"),
                }
            )

        # Reverse to show newest first
        recent_changes.reverse()

        return jsonify(
            {"stats": stats, "health": health, "recent_changes": recent_changes}
        )

    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return (
            jsonify(
                {
                    "stats": {
                        "total_calculations": 0,
                        "active_counties": 0,
                        "output_templates": 0,
                        "total_fees": 0,
                    },
                    "health": {
                        "config_files": False,
                        "database": False,
                        "cache": False,
                        "last_backup": "Error",
                    },
                    "recent_changes": [],
                }
            ),
            500,
        )


@admin_bp.route("/counties")
@admin_required
def counties():
    """County rates management page."""
    county_rates = current_app.config_manager.config.get("county_rates", {})
    return render_template(
        "admin/counties.html", county_rates=county_rates, **get_admin_context()
    )


from admin_logic import (
    add_closing_cost_logic,
    add_county_logic,
    add_fee_logic,
    add_template_logic,
    delete_closing_cost_logic,
    delete_county_logic,
    delete_fee_logic,
    delete_template_logic,
    edit_county_logic,
    edit_fee_logic,
    edit_template_logic,
    update_closing_cost_logic,
    update_loan_limits_logic,
    update_mortgage_config_logic,
    update_pmi_rates_logic,
    update_prepaid_items_logic,
)


@admin_bp.route("/counties/add", methods=["POST"])
@admin_required
def add_county():
    data = request.get_json() or request.form.to_dict()
    counties = load_counties()
    updated_counties, error = add_county_logic(counties, data)
    if error:
        return jsonify({"success": False, "error": error}), 400
    save_counties(updated_counties)
    return jsonify({"success": True})


@admin_bp.route("/counties/edit/<county_name>", methods=["POST"])
@admin_required
def edit_county(county_name):
    data = request.get_json() or request.form.to_dict()
    counties = load_counties()
    updated_counties, error = edit_county_logic(counties, county_name, data)
    if error:
        return jsonify({"success": False, "error": error}), 404
    save_counties(updated_counties)
    return jsonify({"success": True})


@admin_bp.route("/counties/delete/<county_name>", methods=["POST"])
@admin_required
def delete_county(county_name):
    counties = load_counties()
    updated_counties, error = delete_county_logic(counties, county_name)
    if error:
        return jsonify({"success": False, "error": error}), 404
    save_counties(updated_counties)
    return jsonify({"success": True})


@admin_bp.route("/compliance")
@admin_required
def compliance():
    """Compliance text management page."""
    compliance_text = current_app.config_manager.config.get("compliance_text", {})
    return render_template(
        "admin/compliance.html", compliance_text=compliance_text, **get_admin_context()
    )


@admin_bp.route("/compliance/add", methods=["POST"])
@admin_required
def add_compliance_text():
    """Add a new compliance text section."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    # Get current compliance text
    compliance_text = current_app.config_manager.config.get("compliance_text", {})

    section_name = data.get("section")
    if not section_name:
        return jsonify({"success": False, "error": "Section name is required"}), 400

    if section_name in compliance_text:
        return jsonify({"success": False, "error": "Section already exists"}), 400

    # Validate required fields
    if "text" not in data:
        return jsonify({"success": False, "error": "Compliance text is required"}), 400

    # Add new section
    compliance_text[section_name] = data.get("text")

    # Save updated config
    current_app.config_manager.config["compliance_text"] = compliance_text
    current_app.config_manager.save_config()
    current_app.config_manager.add_change(
        description=f"Added compliance text: {section_name}",
        details=f"Added compliance text section: {section_name}",
        user="admin",
    )

    return jsonify({"success": True})


@admin_bp.route("/compliance/edit/<section_name>", methods=["POST"])
@admin_required
def edit_compliance_text(section_name):
    """Edit an existing compliance text section."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    # Get current compliance text
    compliance_text = current_app.config_manager.config.get("compliance_text", {})

    if section_name not in compliance_text:
        return jsonify({"success": False, "error": "Section not found"}), 404

    # Validate required fields
    if "text" not in data:
        return jsonify({"success": False, "error": "Compliance text is required"}), 400

    # Update section
    compliance_text[section_name] = data.get("text")

    # Save updated config
    current_app.config_manager.config["compliance_text"] = compliance_text
    current_app.config_manager.save_config()
    current_app.config_manager.add_change(
        description=f"Updated compliance text: {section_name}",
        details=f"Updated compliance text section: {section_name}",
        user="admin",
    )

    return jsonify({"success": True})


@admin_bp.route("/compliance/delete/<section_name>", methods=["POST"])
@admin_required
def delete_compliance_text(section_name):
    """Delete an existing compliance text section."""
    # Get current compliance text
    compliance_text = current_app.config_manager.config.get("compliance_text", {})

    if section_name not in compliance_text:
        return jsonify({"success": False, "error": "Section not found"}), 404

    # Delete section
    del compliance_text[section_name]

    # Save updated config
    current_app.config_manager.config["compliance_text"] = compliance_text
    current_app.config_manager.save_config()
    current_app.config_manager.add_change(
        description=f"Deleted compliance text: {section_name}",
        details=f"Deleted compliance text section: {section_name}",
        user="admin",
    )

    return jsonify({"success": True})


@admin_bp.route("/templates")
@admin_required
def templates():
    """Output templates management page."""
    output_templates = current_app.config_manager.config.get("output_templates", {})
    return render_template(
        "admin/templates.html", output_templates=output_templates, **get_admin_context()
    )


@admin_bp.route("/templates/add", methods=["POST"])
@admin_required
def add_template():
    """Add a new output template."""
    data = request.get_json() or request.form.to_dict()
    templates = load_templates()
    updated_templates, error = add_template_logic(templates, data)
    if error:
        return jsonify({"success": False, "error": error}), 400
    save_templates(updated_templates)
    return jsonify({"success": True})


@admin_bp.route("/templates/edit/<template_name>", methods=["POST"])
@admin_required
def edit_template(template_name):
    """Edit an existing output template."""
    data = request.get_json() or request.form.to_dict()
    templates = load_templates()
    updated_templates, error = edit_template_logic(templates, template_name, data)
    if error:
        return jsonify({"success": False, "error": error}), 404
    save_templates(updated_templates)
    return jsonify({"success": True})


@admin_bp.route("/templates/delete/<template_name>", methods=["POST"])
@admin_required
def delete_template(template_name):
    """Delete an existing output template."""
    templates = load_templates()
    updated_templates, error = delete_template_logic(templates, template_name)
    if error:
        return jsonify({"success": False, "error": error}), 404
    save_templates(updated_templates)
    return jsonify({"success": True})


@admin_bp.route("/fees", methods=["GET", "POST"])
@admin_required
def fees():
    """Fee management page."""
    if request.method == "POST":
        data = request.get_json() or request.form.to_dict()
        fees = load_fees()
        updated_fees, error = add_fee_logic(fees, data)
        if error:
            return jsonify({"success": False, "error": error}), 400
        save_fees(updated_fees)
        return jsonify({"success": True})

    closing_costs = current_app.config_manager.config.get("closing_costs", {})
    return render_template("admin/fees.html", fees=closing_costs, **get_admin_context())


@admin_bp.route("/fees/edit/<fee_type>", methods=["POST"])
@admin_required
def edit_fee(fee_type):
    """Edit an existing fee."""
    data = request.get_json() or request.form.to_dict()
    fees = load_fees()
    updated_fees, error = edit_fee_logic(fees, fee_type, data)
    if error:
        return jsonify({"success": False, "error": error}), 404
    save_fees(updated_fees)
    return jsonify({"success": True})


@admin_bp.route("/fees/delete/<fee_type>", methods=["POST"])
@admin_required
def delete_fee(fee_type):
    """Delete an existing fee."""
    fees = load_fees()
    updated_fees, error = delete_fee_logic(fees, fee_type)
    if error:
        return jsonify({"success": False, "error": error}), 404
    save_fees(updated_fees)
    return jsonify({"success": True})


@admin_bp.route("/maintenance")
@admin_required
def maintenance():
    """System maintenance page."""
    # Get system health information
    health_info = current_app.config_manager.get_system_health()

    # Basic stats
    stats = {
        "calculation_count": health_info.get("calculation_count", 0),
        "total_backups": health_info.get("total_backups", 0),
        "config_files": health_info.get("config_files", {}),
    }

    return render_template(
        "admin/maintenance.html",
        health_info=health_info,
        stats=stats,
        **get_admin_context(),
    )


@admin_bp.route("/maintenance/backup", methods=["POST"])
@admin_required
def create_backup():
    """Create a configuration backup."""
    try:
        success = current_app.config_manager.backup_config()
        if success:
            flash("Backup created successfully", "success")
            return jsonify({"success": True})
        else:
            flash("Error creating backup", "error")
            return jsonify({"success": False, "error": "Error creating backup"}), 500
    except Exception as e:
        logger.error(f"Error in backup process: {str(e)}")
        flash(f"Error: {str(e)}", "error")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/statistics")
@admin_required
def statistics():
    """Usage statistics page."""
    # Initialize statistics manager if needed
    if not hasattr(current_app, "stats_manager"):
        current_app.stats_manager = StatisticsManager()

    # Get summary statistics for template rendering
    stats = current_app.stats_manager.get_summary_stats()

    return render_template("admin/statistics.html", stats=stats, **get_admin_context())


@admin_bp.route("/api/statistics/data", methods=["GET"])
@admin_required
def statistics_data():
    """API endpoint for statistics chart data."""
    # Initialize statistics manager if needed
    if not hasattr(current_app, "stats_manager"):
        current_app.stats_manager = StatisticsManager()

    try:
        # Get chart data from statistics manager
        chart_data = current_app.stats_manager.get_chart_data()
        insights = current_app.stats_manager.generate_insights()

        return jsonify(
            {"success": True, "chart_data": chart_data, "insights": insights}
        )
    except Exception as e:
        logger.error(f"Error getting statistics data: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/statistics/export", methods=["GET"])
@admin_required
def export_statistics():
    """Export statistics as CSV."""
    # Initialize statistics manager if needed
    if not hasattr(current_app, "stats_manager"):
        current_app.stats_manager = StatisticsManager()

    try:
        # Generate CSV report
        csv_data = current_app.stats_manager.generate_csv_report()

        if not csv_data:
            return (
                jsonify({"success": False, "error": "No data available for export"}),
                400,
            )

        # Create timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mortgage_stats_{timestamp}.csv"

        # Create a temporary file
        temp_file = os.path.join(
            current_app.config.get("TEMP_FOLDER", "/tmp"), filename
        )

        with open(temp_file, "w") as f:
            f.write(csv_data)

        return send_file(
            temp_file, mimetype="text/csv", as_attachment=True, download_name=filename
        )
    except Exception as e:
        logger.error(f"Error exporting statistics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/statistics/purge", methods=["POST"])
@admin_required
def purge_statistics():
    """Purge old statistics data."""
    # Initialize statistics manager if needed
    if not hasattr(current_app, "stats_manager"):
        current_app.stats_manager = StatisticsManager()

    try:
        # Get number of days from request, default to 365
        days = request.json.get("days", 365)

        # Validate days parameter
        try:
            days = int(days)
            if days < 1:
                raise ValueError("Days must be positive")
        except ValueError as e:
            return jsonify({"success": False, "error": str(e)}), 400

        # Purge old data
        purged_count = current_app.stats_manager.purge_old_data(days)

        return jsonify(
            {
                "success": True,
                "message": f"Purged {purged_count} records older than {days} days",
                "purged_count": purged_count,
            }
        )
    except Exception as e:
        logger.error(f"Error purging statistics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/closing-costs")
@admin_required
def closing_costs():
    """Display and manage closing costs."""
    costs = load_closing_costs()
    return render_template(
        "admin/closing_costs.html",
        active_page="closing_costs",
        closing_costs=costs,
        **get_admin_context(),
    )


@admin_bp.route("/closing-costs/<name>")
@admin_required
def get_closing_cost(name):
    """Get a specific closing cost."""
    costs = load_closing_costs()
    if name in costs:
        return jsonify(costs[name])
    return jsonify({"error": "Cost not found"}), 404


@admin_bp.route("/closing-costs/add", methods=["POST"])
@admin_required
def add_closing_cost():
    """Add a new closing cost."""
    data = request.get_json() or request.form.to_dict()
    costs = load_closing_costs()
    updated_costs, error = add_closing_cost_logic(costs, data)
    if error:
        return jsonify({"success": False, "error": error}), 400
    save_closing_costs(updated_costs)
    return jsonify({"success": True})


@admin_bp.route("/closing-costs/<n>", methods=["DELETE"])
@admin_required
def delete_closing_cost(n):
    """Delete a closing cost."""
    costs = load_closing_costs()
    updated_costs, error = delete_closing_cost_logic(costs, n)
    if error:
        return jsonify({"success": False, "error": error}), 404
    save_closing_costs(updated_costs)
    return jsonify({"success": True})


@admin_bp.route(
    "/closing-costs/<n>", methods=["PUT", "POST"]
)  # Support both PUT and POST methods
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
        return jsonify({"success": False, "error": "Invalid data"}), 400

    current_app.logger.info(f"Updating closing cost {n} with data: {data}")
    costs = load_closing_costs()

    updated_costs, error = update_closing_cost_logic(costs, n, data)
    if error:
        status = 404 if error == "Cost not found" else 400
        return jsonify({"success": False, "error": error}), status

    save_closing_costs(updated_costs)
    return jsonify({"success": True})


@admin_bp.route("/mortgage-config")
@admin_required
def mortgage_config():
    """Mortgage configuration management page."""
    # Get mortgage configuration from config
    mortgage_config = {
        "loan_types": current_app.config_manager.config.get("loan_types", {}),
        "limits": current_app.config_manager.config.get("loan_limits", {}),
        "prepaid_items": current_app.config_manager.config.get("prepaid_items", {}),
    }

    # Load seller contributions data
    seller_contributions = {}
    try:
        if os.path.exists(SELLER_CONTRIBUTIONS_FILE):
            with open(SELLER_CONTRIBUTIONS_FILE, "r") as f:
                seller_contributions = json.load(f)
    except Exception as e:
        logger.error(f"Error loading seller contributions: {e}")
        flash(f"Error loading seller contributions: {e}", "error")

    return render_template(
        "admin/mortgage_config.html",
        mortgage_config=mortgage_config,
        seller_contributions=seller_contributions,
        active_page="mortgage_config",
        **get_admin_context(),
    )


@admin_bp.route("/mortgage-config/update", methods=["POST"])
@admin_required
def update_mortgage_config():
    """Update mortgage configuration."""
    data = request.get_json() or request.form.to_dict()
    config = current_app.config_manager.config
    updated_config, error = update_mortgage_config_logic(config, data)
    if error:
        return jsonify({"success": False, "error": error}), 400
    current_app.config_manager.config = updated_config
    current_app.config_manager.save_config()
    return jsonify({"success": True})


@admin_bp.route("/mortgage-config/prepaid/update", methods=["POST"])
@admin_required
def update_prepaid_items():
    """Update prepaid items configuration."""
    data = request.get_json() or request.form.to_dict()
    config = current_app.config_manager.config
    updated_config, error = update_prepaid_items_logic(
        config, data.get("prepaid_items")
    )
    if error:
        return jsonify({"success": False, "error": error}), 400
    current_app.config_manager.config = updated_config
    current_app.config_manager.save_config()
    return jsonify({"success": True})


@admin_bp.route("/mortgage-config/limits/update", methods=["POST"])
@admin_required
def update_loan_limits():
    """Update loan limits configuration."""
    data = request.get_json() or request.form.to_dict()
    config = current_app.config_manager.config
    updated_config, error = update_loan_limits_logic(config, data.get("loan_limits"))
    if error:
        return jsonify({"success": False, "error": error}), 400
    current_app.config_manager.config = updated_config
    current_app.config_manager.save_config()
    return jsonify({"success": True})


@admin_bp.route("/pmi-rates")
@admin_required
def pmi_rates():
    """PMI rates management page."""
    # Get PMI rates from config
    pmi_rates = current_app.config_manager.config.get("pmi_rates", {})

    # Ensure each loan type has the expected structure
    for loan_type in pmi_rates:
        if loan_type == "va":
            # Special structure for VA loans with funding fee
            if "funding_fee" not in pmi_rates[loan_type]:
                pmi_rates[loan_type]["funding_fee"] = {
                    "active": {
                        "less_than_5": {"first": 2.3, "subsequent": 3.6},
                        "5_to_10": {"first": 1.65, "subsequent": 1.65},
                        "10_or_more": {"first": 1.4, "subsequent": 1.4},
                    },
                    "reserves": {
                        "less_than_5": {"first": 2.3, "subsequent": 3.6},
                        "5_to_10": {"first": 1.65, "subsequent": 1.65},
                        "10_or_more": {"first": 1.4, "subsequent": 1.4},
                    },
                    "disability_exempt": True,
                }
        elif loan_type == "fha":
            # Special structure for FHA loans with upfront and annual MIP
            if "upfront_mip_rate" not in pmi_rates[loan_type]:
                pmi_rates[loan_type]["upfront_mip_rate"] = 1.75

            if "annual_mip" not in pmi_rates[loan_type]:
                pmi_rates[loan_type]["annual_mip"] = {
                    "long_term": {
                        "standard_amount": {"low_ltv": 0.50, "high_ltv": 0.55},
                        "high_amount": {"low_ltv": 0.70, "high_ltv": 0.75},
                    },
                    "short_term": {
                        "standard_amount": {"low_ltv": 0.15, "high_ltv": 0.40},
                        "high_amount": {
                            "very_low_ltv": 0.15,
                            "low_ltv": 0.40,
                            "high_ltv": 0.65,
                        },
                    },
                }

            if "standard_loan_limit" not in pmi_rates[loan_type]:
                pmi_rates[loan_type]["standard_loan_limit"] = 726200

            if "high_cost_loan_limit" not in pmi_rates[loan_type]:
                pmi_rates[loan_type]["high_cost_loan_limit"] = 1089300
        else:
            # Standard structure for conventional, etc.
            if "ltv_ranges" not in pmi_rates[loan_type]:
                pmi_rates[loan_type]["ltv_ranges"] = {}
            if "credit_score_adjustments" not in pmi_rates[loan_type]:
                pmi_rates[loan_type]["credit_score_adjustments"] = {}
            # Note: we don't initialize 'annual' as it's format varies by loan type

    # Initialize VA loan type if not present
    if "va" not in pmi_rates:
        pmi_rates["va"] = {
            "funding_fee": {
                "active": {
                    "less_than_5": {"first": 2.3, "subsequent": 3.6},
                    "5_to_10": {"first": 1.65, "subsequent": 1.65},
                    "10_or_more": {"first": 1.4, "subsequent": 1.4},
                },
                "reserves": {
                    "less_than_5": {"first": 2.3, "subsequent": 3.6},
                    "5_to_10": {"first": 1.65, "subsequent": 1.65},
                    "10_or_more": {"first": 1.4, "subsequent": 1.4},
                },
                "disability_exempt": True,
            }
        }

    # Initialize FHA loan type if not present
    if "fha" not in pmi_rates:
        pmi_rates["fha"] = {
            "upfront_mip_rate": 1.75,
            "annual_mip": {
                "long_term": {
                    "standard_amount": {"low_ltv": 0.50, "high_ltv": 0.55},
                    "high_amount": {"low_ltv": 0.70, "high_ltv": 0.75},
                },
                "short_term": {
                    "standard_amount": {"low_ltv": 0.15, "high_ltv": 0.40},
                    "high_amount": {
                        "very_low_ltv": 0.15,
                        "low_ltv": 0.40,
                        "high_ltv": 0.65,
                    },
                },
            },
            "standard_loan_limit": 726200,
            "high_cost_loan_limit": 1089300,
        }

    return render_template(
        "admin/pmi_rates.html",
        pmi_rates=pmi_rates,
        active_page="pmi_rates",
        **get_admin_context(),
    )


@admin_bp.route("/pmi-rates/data")
@admin_required
def get_pmi_rates():
    """Get PMI rates data as JSON."""
    pmi_rates = current_app.config_manager.config.get("pmi_rates", {})
    return jsonify({"success": True, "pmi_rates": pmi_rates})


@admin_bp.route("/pmi-rates/update", methods=["POST"])
@admin_required
def update_pmi_rates():
    """Update PMI rates."""
    current_app.logger.info("PMI rates update request received")

    try:
        data = request.get_json()
        if not data:
            current_app.logger.error("No data provided in PMI rates update")
            return jsonify({"success": False, "error": "No data provided"}), 400

        existing_pmi_rates = copy.deepcopy(
            current_app.config_manager.config.get("pmi_rates", {})
        )
        current_app.logger.info(
            f"Existing PMI rates before update: {existing_pmi_rates}"
        )

        updated_pmi_rates, error = update_pmi_rates_logic(existing_pmi_rates, data)
        if error:
            current_app.logger.error(f"Error in PMI rates logic: {error}")
            return jsonify({"success": False, "error": error}), 400

        current_app.logger.info(f"Final PMI rates structure: {updated_pmi_rates}")
        current_app.config_manager.config["pmi_rates"] = updated_pmi_rates
        current_app.logger.info("Saving config to disk")
        current_app.config_manager.save_config()
        current_app.logger.info("Adding change record")
        current_app.config_manager.add_change(
            description="Updated PMI rates",
            details="Updated PMI rates configuration",
            user="admin",
        )
        current_app.logger.info("PMI rates updated successfully")
        return jsonify({"success": True})
    except Exception as e:
        import traceback

        tb = traceback.format_exc()
        current_app.logger.error(f"Error updating PMI rates: {str(e)}")
        current_app.logger.error(f"Traceback: {tb}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/save_seller_contributions", methods=["POST"])
@admin_required
def save_seller_contributions():
    """Save seller contribution limits."""
    try:
        data = request.json
        loan_type = data.get("loan_type")
        contributions = data.get("contributions", {})

        if not loan_type:
            return jsonify({"success": False, "error": "Loan type is required"}), 400

        # Load current seller contributions
        seller_contributions = {}
        if os.path.exists(SELLER_CONTRIBUTIONS_FILE):
            with open(SELLER_CONTRIBUTIONS_FILE, "r") as f:
                seller_contributions = json.load(f)

        # Update the specific loan type's contributions
        seller_contributions[loan_type] = contributions

        # Save back to file
        with open(SELLER_CONTRIBUTIONS_FILE, "w") as f:
            json.dump(seller_contributions, f, indent=2)

        logger.info(f"Updated seller contributions for {loan_type}")
        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Error saving seller contributions: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/conventional-pmi", methods=["GET"])
@admin_required
def conventional_pmi_page():
    """Dedicated page for conventional PMI rates management."""
    pmi_rates = current_app.config_manager.config.get("pmi_rates", {})
    conventional_rates = pmi_rates.get("conventional", {})
    return render_template(
        "admin/conventional_pmi.html",
        pmi_rates=conventional_rates,
        version=current_app.config.get("VERSION", "1.0"),
    )


@admin_bp.route("/conventional-pmi/update", methods=["POST"])
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
            if key.startswith("ltv_range_"):
                # Extract the index from the key (ltv_range_1, ltv_range_2, etc.)
                index = key.split("_")[-1]
                range_value = value.strip()
                rate_key = f"ltv_rate_{index}"

                # Get the corresponding rate
                if rate_key in data:
                    try:
                        rate_value = float(data[rate_key])
                        if range_value and rate_value >= 0:
                            ltv_ranges[range_value] = round(rate_value, 3)
                            current_app.logger.info(
                                f"Added LTV range: {range_value} = {rate_value}"
                            )
                    except ValueError:
                        current_app.logger.warning(
                            f"Invalid rate value for {rate_key}: {data[rate_key]}"
                        )

        # Get existing PMI rates
        existing_pmi_rates = copy.deepcopy(
            current_app.config_manager.config.get("pmi_rates", {})
        )

        # Ensure conventional exists
        if "conventional" not in existing_pmi_rates:
            existing_pmi_rates["conventional"] = {}

        # Update the LTV ranges
        existing_pmi_rates["conventional"]["ltv_ranges"] = ltv_ranges

        # Ensure credit_score_adjustments exists
        if "credit_score_adjustments" not in existing_pmi_rates["conventional"]:
            existing_pmi_rates["conventional"]["credit_score_adjustments"] = {}

        # Update the config
        current_app.logger.info(f"Updating PMI rates: {existing_pmi_rates}")
        current_app.config_manager.config["pmi_rates"] = existing_pmi_rates
        current_app.config_manager.save_config()

        return jsonify({"success": True})
    except Exception as e:
        current_app.logger.error(f"Error updating conventional PMI rates: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


# --- Title Insurance Configuration Routes ---

from decimal import Decimal, InvalidOperation


@admin_bp.route("/title-insurance", methods=["GET"])
@admin_required
def title_insurance_config():
    """Display title insurance configuration management page."""
    try:
        # Deep copy to avoid modifying the loaded config directly if template manipulates it
        title_config = copy.deepcopy(
            current_app.config_manager.config.get("title_insurance", {})
        )
        logger.debug(f"Loaded title insurance config for admin page: {title_config}")
        return render_template(
            "admin/title_insurance.html",
            active_page="title_insurance",  # For sidebar highlighting
            title_config=title_config,
            **get_admin_context(),
        )
    except Exception as e:
        logger.error(f"Error loading title insurance config page: {e}")
        flash("Error loading title insurance configuration.", "error")
        return redirect(url_for("admin.dashboard"))


@admin_bp.route("/title-insurance/update", methods=["POST"])
@admin_required
def update_title_insurance_config():
    """Update title insurance configuration."""
    try:
        logger.info("Received request to update title insurance configuration.")
        form_data = request.form
        logger.debug(f"Form data received: {form_data}")

        # Extract single values
        simultaneous_issuance_fee = Decimal(
            form_data.get("simultaneous_issuance_fee", "0.0")
        )
        lender_rate_waiver_multiplier = Decimal(
            form_data.get("lender_rate_waiver_multiplier", "1.0")
        )

        # Extract tiered rates (Total)
        total_tiers = []
        total_tier_indices = sorted(
            list(
                set(
                    key.split("_")[-1]
                    for key in form_data
                    if key.startswith("total_tier_up_to_")
                )
            )
        )
        for index in total_tier_indices:
            up_to_str = form_data.get(f"total_tier_up_to_{index}")
            rate_str = form_data.get(f"total_tier_rate_{index}")

            if up_to_str is None or rate_str is None:
                continue  # Skip incomplete tiers

            # Handle 'infinity' or empty string for the last tier's 'up_to'
            up_to_val = (
                None
                if up_to_str.lower() == "infinity" or up_to_str == ""
                else int(up_to_str)
            )
            rate_val = Decimal(rate_str) / Decimal("100")  # Store as decimal fraction

            total_tiers.append(
                {"up_to": up_to_val, "rate_percentage": float(rate_val * 100)}
            )  # Store percentage back

        # Extract tiered rates (Lender Simultaneous)
        lender_tiers = []
        lender_tier_indices = sorted(
            list(
                set(
                    key.split("_")[-1]
                    for key in form_data
                    if key.startswith("lender_tier_up_to_")
                )
            )
        )
        for index in lender_tier_indices:
            up_to_str = form_data.get(f"lender_tier_up_to_{index}")
            rate_str = form_data.get(f"lender_tier_rate_{index}")

            if up_to_str is None or rate_str is None:
                continue  # Skip incomplete tiers

            up_to_val = (
                None
                if up_to_str.lower() == "infinity" or up_to_str == ""
                else int(up_to_str)
            )
            rate_val = Decimal(rate_str) / Decimal("100")  # Store as decimal fraction

            lender_tiers.append(
                {"up_to": up_to_val, "rate_percentage": float(rate_val * 100)}
            )

        # Sort tiers by 'up_to' (None/infinity last)
        total_tiers.sort(
            key=lambda x: x["up_to"] if x["up_to"] is not None else float("inf")
        )
        lender_tiers.sort(
            key=lambda x: x["up_to"] if x["up_to"] is not None else float("inf")
        )

        # Construct the updated config section
        updated_config = {
            "simultaneous_issuance_fee": float(simultaneous_issuance_fee),
            "lender_rate_waiver_multiplier": float(lender_rate_waiver_multiplier),
            "total_rates_tiers": total_tiers,
            "lender_rates_simultaneous_tiers": lender_tiers,
        }

        # Update the config in the config manager
        current_app.config_manager.config["title_insurance"] = updated_config
        current_app.config_manager.save_config()

        logger.info("Successfully updated title insurance configuration.")
        flash("Title insurance configuration updated successfully.", "success")

    except InvalidOperation as e:
        logger.error(
            f"Invalid decimal operation during title insurance update: {e} - Data: {form_data}"
        )
        flash(
            f"Invalid number format submitted. Please check your inputs. Error: {e}",
            "error",
        )
    except ValueError as e:
        logger.error(
            f"Invalid integer conversion during title insurance update: {e} - Data: {form_data}"
        )
        flash(
            f"Invalid number format for tier limit. Please check your inputs. Error: {e}",
            "error",
        )
    except Exception as e:
        logger.exception(
            f"Error updating title insurance configuration: {e}"
        )  # Use exception for stack trace
        flash(
            f"An unexpected error occurred while updating title insurance configuration: {e}",
            "error",
        )

    return redirect(url_for("admin.title_insurance_config"))


# --- End Title Insurance Configuration Routes ---


def load_closing_costs():
    """Load closing costs from JSON file."""
    try:
        with open(CLOSING_COSTS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def load_fees():
    """Load fees from the config manager (assume closing_costs is the fee list)."""
    return current_app.config_manager.config.get("closing_costs", {})


def save_closing_costs(costs):
    """Save closing costs to JSON file."""
    os.makedirs(os.path.dirname(CLOSING_COSTS_FILE), exist_ok=True)
    with open(CLOSING_COSTS_FILE, "w") as f:
        json.dump(costs, f, indent=4)


def save_fees(fees):
    """Save fees to the config manager."""
    current_app.config_manager.config["closing_costs"] = fees
    current_app.config_manager.save_config()
