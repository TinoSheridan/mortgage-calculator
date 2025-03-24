"""Beta testing routes and functions for the mortgage calculator."""
import json
import os
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

# Create a blueprint for beta testing features
beta_bp = Blueprint("beta", __name__, url_prefix="/beta")


@beta_bp.route("/feedback", methods=["POST"])
def submit_feedback():
    """Handle feedback submission from beta testers."""
    if not current_app.config.get("BETA_ENABLED", False):
        return (
            jsonify({"status": "error", "message": "Beta testing is not enabled"}),
            404,
        )

    try:
        feedback_data = request.form.to_dict()
        feedback_data["timestamp"] = datetime.now().isoformat()
        feedback_data["user_agent"] = request.headers.get("User-Agent", "")
        feedback_data["ip_address"] = request.remote_addr

        # Ensure feedback directory exists
        os.makedirs("data", exist_ok=True)

        # Load existing feedback
        feedback_file = "data/beta_feedback.json"
        try:
            with open(feedback_file, "r") as f:
                feedback_list = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            feedback_list = []

        # Add new feedback
        feedback_list.append(feedback_data)

        # Save feedback
        with open(feedback_file, "w") as f:
            json.dump(feedback_list, f, indent=2)

        current_app.logger.info(
            f"Beta feedback received: {feedback_data.get('feedback_type')} from {feedback_data.get('user_email', 'anonymous')}"
        )

        return jsonify(
            {"status": "success", "message": "Feedback submitted successfully"}
        )
    except Exception as e:
        current_app.logger.error(f"Error processing feedback: {str(e)}")
        return jsonify({"status": "error", "message": "Error processing feedback"}), 500
