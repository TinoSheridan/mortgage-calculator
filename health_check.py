"""
Health check endpoint for monitoring application status on Render
"""
import os
from datetime import datetime

from flask import Blueprint, jsonify

from VERSION import FEATURES, LAST_UPDATED, VERSION

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint that returns application status and version information
    """
    return (
        jsonify(
            {
                "status": "healthy",
                "version": VERSION,
                "features": FEATURES,
                "last_updated": LAST_UPDATED,
                "environment": os.environ.get("FLASK_ENV", "development"),
                "timestamp": datetime.now().isoformat(),
            }
        ),
        200,
    )
