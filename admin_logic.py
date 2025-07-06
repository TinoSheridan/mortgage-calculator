"""
Admin logic functions for managing fees, counties, closing costs, templates, and configuration.

Each function returns a tuple of (updated_data, error_message) or (updated_data, None) on success.
"""


def update_closing_cost_logic(costs, n, data):
    """Update an existing closing cost in the costs dict. Returns (updated_costs, error_message)."""
    if n not in costs:
        return costs, "Cost not found"

    new_name = data.pop("name").lower().replace(" ", "_")
    if new_name != n and new_name in costs:
        return costs, "New name already exists"

    if new_name != n:
        costs.pop(n)

    costs[new_name] = {
        "type": data["type"],
        "value": float(data["value"]),
        "calculation_base": data["calculation_base"],
        "description": data["description"],
    }
    return costs, None


def update_pmi_rates_logic(existing_pmi_rates, data):
    """Update PMI rates structure in memory. Returns (updated_pmi_rates, error_message)."""
    # Extract loan_type from the request - this is now a required field
    loan_type = data.get("loan_type")
    if not loan_type:
        return existing_pmi_rates, "No loan_type provided"

    # Initialize if loan type doesn't exist yet
    if loan_type not in existing_pmi_rates:
        existing_pmi_rates[loan_type] = {}

    # Handle the data based on loan type
    if loan_type == "conventional" and "ltv_ranges" in data:
        # Convert string rates to float for consistency
        for key, value in data["ltv_ranges"].items():
            if isinstance(value, str) and value.strip():
                try:
                    data["ltv_ranges"][key] = round(float(value), 3)
                except ValueError:
                    data["ltv_ranges"][key] = 0.0
            elif value is None or (isinstance(value, str) and not value.strip()):
                data["ltv_ranges"][key] = 0.0
            else:
                data["ltv_ranges"][key] = round(float(value), 3)
        # Update just the ltv_ranges for conventional loans, preserve other data
        existing_pmi_rates["conventional"]["ltv_ranges"] = data["ltv_ranges"]
        # Ensure credit_score_adjustments exists
        if "credit_score_adjustments" not in existing_pmi_rates["conventional"]:
            existing_pmi_rates["conventional"]["credit_score_adjustments"] = {}
    else:
        # For other loan types, copy all fields except loan_type
        update_data = {k: v for k, v in data.items() if k != "loan_type"}
        existing_pmi_rates[loan_type].update(update_data)
    return existing_pmi_rates, None


def add_fee_logic(fees, data):
    """Add a new fee to the fees dict. Returns (updated_fees, error_message)."""
    name = data["name"].lower().replace(" ", "_")
    if name in fees:
        return fees, "Fee already exists"
    fees[name] = {
        "type": data["type"],
        "value": float(data["value"]),
        "calculation_base": data["calculation_base"],
        "description": data["description"],
    }
    return fees, None


def edit_fee_logic(fees, fee_type, data):
    """Edit an existing fee in the fees dict. Returns (updated_fees, error_message)."""
    if fee_type not in fees:
        return fees, "Fee not found"
    fees[fee_type].update(
        {
            "type": data["type"],
            "value": float(data["value"]),
            "calculation_base": data["calculation_base"],
            "description": data["description"],
        }
    )
    return fees, None


def delete_fee_logic(fees, fee_type):
    """Delete a fee from the fees dict. Returns (updated_fees, error_message)."""
    if fee_type not in fees:
        return fees, "Fee not found"
    fees.pop(fee_type)
    return fees, None


def add_closing_cost_logic(costs, data):
    """Add a new closing cost to the costs dict. Returns (updated_costs, error_message)."""
    name = data["name"].lower().replace(" ", "_")
    if name in costs:
        return costs, "Closing cost already exists"
    costs[name] = {
        "type": data["type"],
        "value": float(data["value"]),
        "calculation_base": data["calculation_base"],
        "description": data["description"],
    }
    return costs, None


def delete_closing_cost_logic(costs, name):
    """Delete a closing cost from the costs dict. Returns (updated_costs, error_message)."""
    if name not in costs:
        return costs, "Closing cost not found"
    costs.pop(name)
    return costs, None


def add_county_logic(counties, data):
    """Add a new county to the counties dict. Returns (updated_counties, error_message)."""
    name = data["name"].lower().replace(" ", "_")
    if name in counties:
        return counties, "County already exists"
    counties[name] = {
        "rate": float(data["rate"]),
        "state": data["state"],
        "description": data.get("description", ""),
    }
    return counties, None


def edit_county_logic(counties, county_name, data):
    """Edit an existing county in the counties dict. Returns (updated_counties, error_message)."""
    if county_name not in counties:
        return counties, "County not found"
    counties[county_name].update(
        {
            "rate": float(data["rate"]),
            "state": data["state"],
            "description": data.get("description", ""),
        }
    )
    return counties, None


def delete_county_logic(counties, county_name):
    """Delete a county from the counties dict. Returns (updated_counties, error_message)."""
    if county_name not in counties:
        return counties, "County not found"
    counties.pop(county_name)
    return counties, None


def add_template_logic(templates, data):
    """Add a new template to the templates dict. Returns (updated_templates, error_message)."""
    name = data["name"].lower().replace(" ", "_")
    if name in templates:
        return templates, "Template already exists"
    templates[name] = {
        "content": data["content"],
        "description": data.get("description", ""),
    }
    return templates, None


def edit_template_logic(templates, template_name, data):
    """Edit an existing template in the templates dict. Returns (updated_templates, error_message)."""
    if template_name not in templates:
        return templates, "Template not found"
    templates[template_name].update(
        {
            "content": data["content"],
            "description": data.get("description", ""),
        }
    )
    return templates, None


def delete_template_logic(templates, template_name):
    """Delete a template from the templates dict. Returns (updated_templates, error_message)."""
    if template_name not in templates:
        return templates, "Template not found"
    templates.pop(template_name)
    return templates, None


def update_mortgage_config_logic(config, data):
    """Update allowed fields in the mortgage config dict. Returns (updated_config, error_message)."""
    # Example: update allowed fields only
    allowed_fields = [
        "max_loan_amount",
        "min_down_payment",
        "interest_rate",
        "prepaid_items",
    ]
    for field in allowed_fields:
        if field in data:
            config[field] = data[field]
    return config, None


def update_prepaid_items_logic(config, prepaid_items):
    """Update prepaid items in the config dict. Returns (updated_config, error_message)."""
    config["prepaid_items"] = prepaid_items
    return config, None


def update_loan_limits_logic(config, loan_limits):
    """Update loan limits in the config dict. Returns (updated_config, error_message)."""
    config["loan_limits"] = loan_limits
    return config, None
