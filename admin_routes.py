"""
Admin routes for managing counties, fees, closing costs, templates, compliance text, and admin dashboard.

All endpoints are protected and require admin authentication.
"""
import copy
import json
import logging
import os
import time
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import wraps
from statistics import StatisticsManager

from flask import (
    Blueprint,
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

import admin_logic
from admin_logic import (
    add_closing_cost_logic,
    add_fee_logic,
    add_template_logic,
    delete_closing_cost_logic,
    delete_fee_logic,
    delete_template_logic,
    edit_fee_logic,
    edit_template_logic,
    update_closing_cost_logic,
    update_loan_limits_logic,
    update_mortgage_config_logic,
    update_pmi_rates_logic,
    update_prepaid_items_logic,
)

# Import version directly
from VERSION import VERSION

# Rate limiting for login attempts
login_attempts = defaultdict(list)
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 5 minutes


def is_rate_limited(ip_address):
    """Check if IP is rate limited for login attempts."""
    now = time.time()
    # Clean old attempts
    login_attempts[ip_address] = [
        attempt for attempt in login_attempts[ip_address] if now - attempt < LOCKOUT_DURATION
    ]

    return len(login_attempts[ip_address]) >= MAX_LOGIN_ATTEMPTS


def record_login_attempt(ip_address):
    """Record a failed login attempt."""
    login_attempts[ip_address].append(time.time())


def log_admin_action(action, details, user="admin", ip_address=None):
    """Log admin actions for audit trail."""
    from datetime import datetime

    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "ip_address": ip_address
        or request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr),
        "action": action,
        "details": details,
        "user_agent": request.headers.get("User-Agent", "Unknown"),
    }

    # Log to application logger
    logger.info(f"AUDIT: {action} by {user} from {audit_entry['ip_address']} - {details}")

    # Store in config manager if available
    try:
        if hasattr(current_app, "config_manager"):
            current_app.config_manager.add_change(
                description=f"AUDIT: {action}", details=details, user=user
            )
    except Exception as e:
        logger.error(f"Failed to store audit log: {str(e)}")

    return audit_entry


def create_error_response(message, status_code=400, log_message=None):
    """Create standardized error response."""
    if log_message:
        logger.error(log_message)
    return jsonify({"success": False, "error": message}), status_code


def create_success_response(data=None, message="Operation completed successfully"):
    """Create standardized success response."""
    response = {"success": True, "message": message}
    if data:
        response["data"] = data
    return jsonify(response)


def validate_config_update(config_data, config_type="general"):
    """Validate configuration data before saving."""
    if not isinstance(config_data, dict):
        return False, "Configuration data must be a dictionary"

    # Basic structure validation
    if not config_data:
        return False, "Configuration data cannot be empty"

    # Type-specific validation
    if config_type == "closing_costs":
        required_keys = ["type", "value", "calculation_base"]
        for cost_name, cost_data in config_data.items():
            if not isinstance(cost_data, dict):
                return False, f"Cost '{cost_name}' must be a dictionary"
            for key in required_keys:
                if key not in cost_data:
                    return False, f"Cost '{cost_name}' missing required field '{key}'"
            if cost_data["type"] not in ["fixed", "percentage"]:
                return False, f"Cost '{cost_name}' has invalid type"

    elif config_type == "pmi_rates":
        for loan_type, rates in config_data.items():
            if not isinstance(rates, dict):
                return False, f"PMI rates for '{loan_type}' must be a dictionary"

    elif config_type == "counties":
        for county, data in config_data.items():
            if not isinstance(data, dict):
                return False, f"County '{county}' data must be a dictionary"
            if "tax_rate" not in data:
                return False, f"County '{county}' missing tax_rate"

    return True, None


# Create a Blueprint for admin routes
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Configure logging
logger = logging.getLogger(__name__)

# Constants
CLOSING_COSTS_FILE = "config/closing_costs.json"
SELLER_CONTRIBUTIONS_FILE = "config/seller_contributions.json"


def load_templates():
    """Return templates from the config manager."""
    return current_app.config_manager.config.get("output_templates", {})


def save_templates(templates):
    """Save templates to the config manager."""
    current_app.config_manager.config["output_templates"] = templates


def load_closing_costs():
    """Load closing costs data from storage."""
    try:
        with open(CLOSING_COSTS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_closing_costs(costs):
    """Save closing costs data to storage."""
    os.makedirs(os.path.dirname(CLOSING_COSTS_FILE), exist_ok=True)
    with open(CLOSING_COSTS_FILE, "w") as f:
        json.dump(costs, f, indent=4)


def load_fees():
    """Load fees from the config manager (assume closing_costs is the fee list)."""
    return current_app.config_manager.config.get("closing_costs", {})


def save_fees(fees):
    """Save fees to the config manager with validation."""
    # Validate before saving
    is_valid, error_msg = validate_config_update(fees, "closing_costs")
    if not is_valid:
        logger.error(f"Closing costs validation failed: {error_msg}")
        raise ValueError(f"Validation failed: {error_msg}")

    current_app.config_manager.config["closing_costs"] = fees
    current_app.config_manager.save_config()


def get_admin_context(**kwargs):
    """Return context dictionary for admin pages, including the app version and any extra kwargs."""
    context = {
        "version": VERSION,
    }
    context.update(kwargs)
    return context


# Admin login check decorator
def admin_required(f):
    """
    Decorator that requires admin authentication for a route with session timeout handling.

    Features:
    - Checks if user is logged in
    - Implements 30-minute inactivity timeout
    - Updates last activity timestamp on each request
    - Redirects to login page if authentication fails
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in
        if not session.get("admin_logged_in"):
            logger.warning(f"Unauthorized admin access attempt to {request.path}")
            return redirect(url_for("admin.login"))

        # Check session timeout (30 minutes of inactivity)
        from datetime import datetime, timedelta

        last_activity = session.get("admin_last_activity")
        session_timeout = timedelta(minutes=30)

        if last_activity:
            try:
                last_activity_time = datetime.fromisoformat(last_activity)
                if datetime.now() - last_activity_time > session_timeout:
                    logger.info("Admin session expired due to inactivity")
                    session.clear()
                    flash("Your session has expired. Please log in again.", "warning")
                    return redirect(url_for("admin.login"))
            except (ValueError, TypeError):
                # Invalid timestamp, clear session
                logger.warning("Invalid session timestamp detected, clearing session")
                session.clear()
                return redirect(url_for("admin.login"))

        # Update last activity time
        session["admin_last_activity"] = datetime.now().isoformat()
        session.permanent = True

        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route("/test-login", methods=["GET", "POST"])
def test_login():
    """Simple test login without complex features."""
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Simple credential check
        if username == "admin" and password == "secure123!":
            session["admin_logged_in"] = True
            flash("Test login successful!", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid credentials", "error")

    return render_template("admin/login.html")


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Admin login page and authentication handler.

    Security features:
    - Rate limiting (5 attempts per 5 minutes per IP)
    - Input validation and length checks
    - Audit logging of all login attempts
    - Secure credential handling
    """
    if request.method == "POST":
        # Check rate limiting
        client_ip = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
        if is_rate_limited(client_ip):
            logger.warning(f"Rate limited login attempt from IP: {client_ip}")
            flash("Too many failed login attempts. Please try again in 5 minutes.", "error")
            return render_template("admin/login.html")

        username = request.form.get("username")
        password = request.form.get("password")

        # Basic input validation
        if not username or not password:
            logger.warning(f"Login attempt with missing credentials from IP: {client_ip}")
            flash("Username and password are required", "error")
            return render_template("admin/login.html")

        # Prevent username enumeration by checking length
        if len(username) > 50 or len(password) > 100:
            logger.warning(f"Login attempt with excessively long credentials from IP: {client_ip}")
            record_login_attempt(client_ip)
            flash("Invalid credentials", "error")
            return render_template("admin/login.html")

        # Get admin credentials from environment variables (more secure)
        valid_username = os.getenv("ADMIN_USERNAME")
        valid_password = os.getenv("ADMIN_PASSWORD")

        # Fallback to config only if env vars not set (for backward compatibility)
        if not valid_username or not valid_password:
            admin_config = current_app.config_manager.config.get("admin", {})
            valid_username = admin_config.get("username")
            valid_password = admin_config.get("password")

        # SECURITY: Never log passwords or credentials
        logger.info(f"Admin login attempt for user: {username}")

        # Validate credentials exist
        if not valid_username or not valid_password:
            logger.error("Admin credentials not configured - access denied")
            flash("System configuration error - contact administrator", "error")
            return render_template("admin/login.html")

        if username == valid_username and password == valid_password:
            # Set session variable and ensure it persists
            from datetime import datetime

            session["admin_logged_in"] = True
            session["admin_last_activity"] = datetime.now().isoformat()
            session.permanent = True
            logger.info(f"Successful admin login for user: {username}")

            # Audit log successful login (temporarily disabled for debugging)
            # log_admin_action("LOGIN_SUCCESS", f"Admin user {username} logged in successfully", user=username)

            flash("Successfully logged in", "success")
            return redirect(url_for("admin.dashboard"))

        # SECURITY: Log failed login attempts and record for rate limiting
        logger.warning(f"Failed admin login attempt for user: {username} from IP: {client_ip}")
        record_login_attempt(client_ip)

        # Audit log failed login (temporarily disabled for debugging)
        # log_admin_action("LOGIN_FAILED", f"Failed login attempt for user: {username}", user=username)

        error = "Invalid credentials"
        flash(error, "error")
        return render_template("admin/login.html", error=error)

    return render_template("admin/login.html")


@admin_bp.route("/logout")
def logout():
    """Log out the current admin user."""
    # Audit log logout before clearing session
    if session.get("admin_logged_in"):
        log_admin_action("LOGOUT", "Admin user logged out")

    session.pop("admin_logged_in", None)
    session.pop("admin_last_activity", None)
    flash("Successfully logged out", "success")
    return redirect(url_for("admin.login"))


@admin_bp.route("/")
def index():
    """Admin index page (redirects to dashboard)."""
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    """Admin dashboard page."""
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
    """Return JSON data for admin dashboard statistics."""
    try:
        # Get statistics
        config = current_app.config_manager.config
        health_info = current_app.config_manager.get_system_health()

        # Calculate statistics
        stats = {
            "total_calculations": len(current_app.config_manager.calculation_history),
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

        return jsonify({"stats": stats, "health": health, "recent_changes": recent_changes})

    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return (
            jsonify(
                {
                    "stats": {
                        "total_calculations": 0,
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


@admin_bp.route("/compliance")
@admin_required
def compliance():
    """Admin page for compliance text management."""
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

    # Audit log the action
    log_admin_action("COMPLIANCE_ADD", f"Added compliance text section: {section_name}")

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

    # Validate before saving
    is_valid, error_msg = validate_config_update(compliance_text, "compliance")
    if not is_valid:
        logger.error(f"Configuration validation failed: {error_msg}")
        return jsonify({"success": False, "error": f"Validation failed: {error_msg}"}), 400

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
    """Delete a compliance text section."""
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
    """Admin page for managing output templates."""
    output_templates = current_app.config_manager.config.get("output_templates", {})
    return render_template(
        "admin/templates.html", output_templates=output_templates, **get_admin_context()
    )


@admin_bp.route("/templates/add", methods=["POST"])
@admin_required
def add_template():
    """Add a new output template via the admin interface."""
    data = request.get_json() or request.form.to_dict()
    templates = load_templates()
    updated_templates, error = admin_logic.add_template_logic(templates, data)
    if error:
        return jsonify({"success": False, "error": error}), 400
    save_templates(updated_templates)
    return jsonify({"success": True})


@admin_bp.route("/templates/edit/<template_name>", methods=["POST"])
@admin_required
def edit_template(template_name):
    """Edit an existing output template via the admin interface."""
    data = request.get_json() or request.form.to_dict()
    templates = load_templates()
    updated_templates, error = admin_logic.edit_template_logic(templates, template_name, data)
    if error:
        return jsonify({"success": False, "error": error}), 404
    save_templates(updated_templates)
    return jsonify({"success": True})


@admin_bp.route("/templates/delete/<template_name>", methods=["POST"])
@admin_required
def delete_template(template_name):
    """Delete an output template via the admin interface."""
    templates = load_templates()
    updated_templates, error = admin_logic.delete_template_logic(templates, template_name)
    if error:
        return jsonify({"success": False, "error": error}), 404
    save_templates(updated_templates)
    return jsonify({"success": True})


@admin_bp.route("/fees", methods=["GET", "POST"])
@admin_required
def fees():
    """Admin page for managing fees."""
    if request.method == "POST":
        data = request.get_json() or request.form.to_dict()
        fees = load_fees()
        updated_fees, error = admin_logic.add_fee_logic(fees, data)
        if error:
            return jsonify({"success": False, "error": error}), 400
        save_fees(updated_fees)
        return jsonify({"success": True})

    closing_costs = current_app.config_manager.config.get("closing_costs", {})
    return render_template("admin/fees.html", fees=closing_costs, **get_admin_context())


@admin_bp.route("/fees/edit/<fee_type>", methods=["POST"])
@admin_required
def edit_fee(fee_type):
    """Edit an existing fee via the admin interface."""
    data = request.get_json() or request.form.to_dict()
    fees = load_fees()
    updated_fees, error = admin_logic.edit_fee_logic(fees, fee_type, data)
    if error:
        return jsonify({"success": False, "error": error}), 404
    save_fees(updated_fees)
    return jsonify({"success": True})


@admin_bp.route("/fees/delete/<fee_type>", methods=["POST"])
@admin_required
def delete_fee(fee_type):
    """Delete a fee via the admin interface."""
    fees = load_fees()
    updated_fees, error = admin_logic.delete_fee_logic(fees, fee_type)
    if error:
        return jsonify({"success": False, "error": error}), 404
    save_fees(updated_fees)
    return jsonify({"success": True})


@admin_bp.route("/maintenance")
@admin_required
def maintenance():
    """Admin maintenance and backup page."""
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
    """Create a backup of the application data."""
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
    """Admin statistics page."""
    # Initialize statistics manager if needed
    if not hasattr(current_app, "stats_manager"):
        current_app.stats_manager = StatisticsManager()

    # Get summary statistics for template rendering
    stats = current_app.stats_manager.get_summary_stats()

    return render_template("admin/statistics.html", stats=stats, **get_admin_context())


@admin_bp.route("/api/statistics/data", methods=["GET"])
@admin_required
def statistics_data():
    """Return JSON data for admin statistics."""
    # Initialize statistics manager if needed
    if not hasattr(current_app, "stats_manager"):
        current_app.stats_manager = StatisticsManager()

    try:
        # Get chart data from statistics manager
        chart_data = current_app.stats_manager.get_chart_data()
        insights = current_app.stats_manager.generate_insights()

        return jsonify({"success": True, "chart_data": chart_data, "insights": insights})
    except Exception as e:
        logger.error(f"Error getting statistics data: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/statistics/export", methods=["GET"])
@admin_required
def export_statistics():
    """Export statistics data as a downloadable file."""
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
        temp_file = os.path.join(current_app.config.get("TEMP_FOLDER", "/tmp"), filename)

        with open(temp_file, "w") as f:
            f.write(csv_data)

        return send_file(temp_file, mimetype="text/csv", as_attachment=True, download_name=filename)
    except Exception as e:
        logger.error(f"Error exporting statistics: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route("/api/statistics/purge", methods=["POST"])
@admin_required
def purge_statistics():
    """Delete all statistics data."""
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
    """Admin page for managing closing costs."""
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
    """Get a specific closing cost by name via the admin interface."""
    costs = load_closing_costs()
    if name in costs:
        return jsonify(costs[name])
    return jsonify({"error": "Cost not found"}), 404


@admin_bp.route("/closing-costs/add", methods=["POST"])
@admin_required
def add_closing_cost():
    """Add a new closing cost via the admin interface."""
    data = request.get_json() or request.form.to_dict()
    costs = load_closing_costs()
    updated_costs, error = admin_logic.add_closing_cost_logic(costs, data)
    if error:
        return jsonify({"success": False, "error": error}), 400
    save_closing_costs(updated_costs)
    return jsonify({"success": True})


@admin_bp.route("/closing-costs/<n>", methods=["DELETE"])
@admin_required
def delete_closing_cost(n):
    """Delete a closing cost via the admin interface."""
    costs = load_closing_costs()
    updated_costs, error = admin_logic.delete_closing_cost_logic(costs, n)
    if error:
        return jsonify({"success": False, "error": error}), 404
    save_closing_costs(updated_costs)
    return jsonify({"success": True})


@admin_bp.route("/closing-costs/<n>", methods=["PUT", "POST"])  # Support both PUT and POST methods
@admin_required
def update_closing_cost(n):
    """Update an existing closing cost via the admin interface."""
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

    updated_costs, error = admin_logic.update_closing_cost_logic(costs, n, data)
    if error:
        status = 404 if error == "Cost not found" else 400
        return jsonify({"success": False, "error": error}), status

    save_closing_costs(updated_costs)
    return jsonify({"success": True})


@admin_bp.route("/mortgage-config")
@admin_required
def mortgage_config():
    """Admin page for viewing and editing mortgage configuration."""
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
    """Update mortgage configuration via the admin interface."""
    data = request.get_json() or request.form.to_dict()
    config = current_app.config_manager.config
    updated_config, error = admin_logic.update_mortgage_config_logic(config, data)
    if error:
        return jsonify({"success": False, "error": error}), 400
    current_app.config_manager.config = updated_config
    current_app.config_manager.save_config()
    return jsonify({"success": True})


@admin_bp.route("/mortgage-config/prepaid/update", methods=["POST"])
@admin_required
def update_prepaid_items():
    """Update prepaid items in the mortgage configuration via the admin interface."""
    data = request.get_json() or request.form.to_dict()
    config = current_app.config_manager.config
    updated_config, error = admin_logic.update_prepaid_items_logic(
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
    """Update loan limits in the mortgage configuration via the admin interface."""
    data = request.get_json() or request.form.to_dict()
    config = current_app.config_manager.config
    updated_config, error = admin_logic.update_loan_limits_logic(config, data.get("loan_limits"))
    if error:
        return jsonify({"success": False, "error": error}), 400
    current_app.config_manager.config = updated_config
    current_app.config_manager.save_config()
    return jsonify({"success": True})


@admin_bp.route("/pmi-rates")
@admin_required
def pmi_rates():
    """Admin page for managing PMI rates."""
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
    """Get PMI rates data via the admin interface."""
    pmi_rates = current_app.config_manager.config.get("pmi_rates", {})
    return jsonify({"success": True, "pmi_rates": pmi_rates})


@admin_bp.route("/pmi-rates/update", methods=["POST"])
@admin_required
def update_pmi_rates():
    """Update PMI rates via the admin interface."""
    current_app.logger.info("PMI rates update request received")

    try:
        data = request.get_json()
        if not data:
            current_app.logger.error("No data provided in PMI rates update")
            return jsonify({"success": False, "error": "No data provided"}), 400

        existing_pmi_rates = copy.deepcopy(current_app.config_manager.config.get("pmi_rates", {}))
        current_app.logger.info(f"Existing PMI rates before update: {existing_pmi_rates}")

        updated_pmi_rates, error = admin_logic.update_pmi_rates_logic(existing_pmi_rates, data)
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
    """Save seller contribution data via the admin interface."""
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


# --- Title Insurance Configuration Routes ---


@admin_bp.route("/title-insurance", methods=["GET"])
@admin_required
def title_insurance_config():
    """Display title insurance configuration management page."""
    try:
        # Deep copy to avoid modifying the loaded config directly if template manipulates it
        title_config = copy.deepcopy(current_app.config_manager.config.get("title_insurance", {}))
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
        simultaneous_issuance_fee = Decimal(form_data.get("simultaneous_issuance_fee", "0.0"))
        lender_rate_waiver_multiplier = Decimal(
            form_data.get("lender_rate_waiver_multiplier", "1.0")
        )

        # Extract tiered rates (Total)
        total_tiers = []
        total_tier_indices = sorted(
            list(
                set(key.split("_")[-1] for key in form_data if key.startswith("total_tier_up_to_"))
            )
        )
        for index in total_tier_indices:
            up_to_str = form_data.get(f"total_tier_up_to_{index}")
            rate_key = f"total_tier_rate_{index}"

            # Get the corresponding rate
            if rate_key in form_data:
                try:
                    rate_value = float(form_data[rate_key])
                    if up_to_str and rate_value >= 0:
                        total_tiers.append(
                            {"up_to": int(up_to_str), "rate_percentage": round(rate_value, 3)}
                        )
                        logger.info(f"Added LTV range: {up_to_str} = {rate_value}")
                except ValueError:
                    logger.warning(f"Invalid rate value for {rate_key}: {form_data[rate_key]}")

        # Extract tiered rates (Lender Simultaneous)
        lender_tiers = []
        lender_tier_indices = sorted(
            list(
                set(key.split("_")[-1] for key in form_data if key.startswith("lender_tier_up_to_"))
            )
        )
        for index in lender_tier_indices:
            up_to_str = form_data.get(f"lender_tier_up_to_{index}")
            rate_key = f"lender_tier_rate_{index}"

            # Get the corresponding rate
            if rate_key in form_data:
                try:
                    rate_value = float(form_data[rate_key])
                    if up_to_str and rate_value >= 0:
                        lender_tiers.append(
                            {"up_to": int(up_to_str), "rate_percentage": round(rate_value, 3)}
                        )
                        logger.info(f"Added LTV range: {up_to_str} = {rate_value}")
                except ValueError:
                    logger.warning(f"Invalid rate value for {rate_key}: {form_data[rate_key]}")

        # Sort tiers by 'up_to' (None/infinity last)
        total_tiers.sort(key=lambda x: x["up_to"] if x["up_to"] is not None else float("inf"))
        lender_tiers.sort(key=lambda x: x["up_to"] if x["up_to"] is not None else float("inf"))

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


# --- Configuration Validation Routes ---


@admin_bp.route("/validation")
@admin_required
def validation_dashboard():
    """Admin page for viewing configuration validation status."""
    try:
        # Get validation report
        report = current_app.config_manager.get_validation_report()

        return render_template(
            "admin/validation.html", validation_report=report, **get_admin_context()
        )
    except Exception as e:
        logger.error(f"Error loading validation dashboard: {e}")
        flash(f"Error loading validation dashboard: {e}", "error")
        return redirect(url_for("admin.dashboard"))


@admin_bp.route("/validation/run", methods=["POST"])
@admin_required
def run_validation():
    """Run configuration validation and return results."""
    try:
        # Run validation
        is_valid = current_app.config_manager.validate_configuration()
        report = current_app.config_manager.get_validation_report()

        # Count errors and successes
        total_files = report.get("summary", {}).get("total_files", 0)
        valid_files = report.get("summary", {}).get("valid_files", 0)
        total_errors = report.get("summary", {}).get("total_errors", 0)

        response_data = {
            "success": True,
            "validation_passed": is_valid,
            "total_files": total_files,
            "valid_files": valid_files,
            "total_errors": total_errors,
            "report": report,
        }

        if is_valid:
            logger.info("Configuration validation passed")
            message = f"✅ All {total_files} configuration files are valid"
        else:
            logger.warning(f"Configuration validation failed with {total_errors} errors")
            message = (
                f"❌ {total_errors} validation errors found in {total_files - valid_files} files"
            )

        response_data["message"] = message
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Error running validation: {e}")
        return jsonify({"success": False, "error": f"Error running validation: {str(e)}"}), 500


@admin_bp.route("/validation/details/<filename>", methods=["GET"])
@admin_required
def validation_file_details(filename):
    """Get detailed validation information for a specific file."""
    try:
        if not current_app.config_manager._validation_enabled:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Validation is disabled - jsonschema package not available",
                    }
                ),
                400,
            )

        # Validate the specific file
        is_valid, errors = current_app.config_manager.validator.validate_config_file(filename)

        return jsonify(
            {
                "success": True,
                "filename": filename,
                "is_valid": is_valid,
                "errors": errors,
                "error_count": len(errors),
            }
        )

    except Exception as e:
        logger.error(f"Error getting validation details for {filename}: {e}")
        return (
            jsonify({"success": False, "error": f"Error getting validation details: {str(e)}"}),
            500,
        )


@admin_bp.route("/validation/schema/<filename>", methods=["GET"])
@admin_required
def get_config_schema(filename):
    """Get the JSON schema for a specific configuration file."""
    try:
        from config_schemas import CONFIG_SCHEMAS

        if filename not in CONFIG_SCHEMAS:
            return jsonify({"success": False, "error": f"No schema defined for {filename}"}), 404

        schema = CONFIG_SCHEMAS[filename]

        return jsonify({"success": True, "filename": filename, "schema": schema})

    except Exception as e:
        logger.error(f"Error getting schema for {filename}: {e}")
        return jsonify({"success": False, "error": f"Error getting schema: {str(e)}"}), 500


@admin_bp.route("/validation/fix-suggestions", methods=["POST"])
@admin_required
def get_validation_fix_suggestions():
    """Get suggestions for fixing validation errors."""
    try:
        data = request.get_json()
        filename = data.get("filename")
        error_message = data.get("error")

        if not filename or not error_message:
            return (
                jsonify({"success": False, "error": "filename and error parameters are required"}),
                400,
            )

        # Generate fix suggestions based on common error patterns
        suggestions = []

        if "required" in error_message.lower():
            suggestions.append("Add the missing required field to your configuration")
            suggestions.append("Check the field name for typos")

        elif "type" in error_message.lower():
            suggestions.append("Check the data type - ensure numbers are not quoted")
            suggestions.append("Verify boolean values are true/false (not strings)")

        elif "enum" in error_message.lower():
            suggestions.append("Check allowed values in the schema")
            suggestions.append("Verify the field value matches one of the permitted options")

        elif "pattern" in error_message.lower():
            suggestions.append(
                "Check field name format - use letters, numbers, and underscores only"
            )
            suggestions.append("Remove special characters except underscores")

        elif "minimum" in error_message.lower() or "maximum" in error_message.lower():
            suggestions.append("Check the numeric value is within allowed range")
            suggestions.append("Ensure the value is positive if required")

        else:
            suggestions.append("Check the configuration file format and structure")
            suggestions.append("Compare with a working configuration file")

        return jsonify(
            {
                "success": True,
                "filename": filename,
                "error": error_message,
                "suggestions": suggestions,
            }
        )

    except Exception as e:
        logger.error(f"Error generating fix suggestions: {e}")
        return jsonify({"success": False, "error": f"Error generating suggestions: {str(e)}"}), 500


# --- End Configuration Validation Routes ---
