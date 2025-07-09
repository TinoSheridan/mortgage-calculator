"""
JSON Schema definitions for mortgage calculator configuration files.

This module defines the validation schemas for all configuration files
to ensure data integrity and prevent runtime errors from malformed configs.
"""

# Mortgage Configuration Schema
MORTGAGE_CONFIG_SCHEMA = {
    "type": "object",
    "required": ["loan_types", "limits", "prepaid_items", "title_insurance"],
    "properties": {
        "loan_types": {
            "type": "object",
            "required": ["conventional", "fha", "va", "usda"],
            "properties": {
                "conventional": {
                    "type": "object",
                    "required": ["min_down_payment", "max_ltv", "description"],
                    "properties": {
                        "min_down_payment": {"type": "number", "minimum": 0, "maximum": 100},
                        "max_ltv": {"type": "number", "minimum": 50, "maximum": 100},
                        "description": {"type": "string", "minLength": 1}
                    }
                },
                "fha": {
                    "type": "object",
                    "required": ["min_down_payment", "max_ltv", "upfront_mip_rate", "annual_mip_rate", "description"],
                    "properties": {
                        "min_down_payment": {"type": "number", "minimum": 0, "maximum": 100},
                        "max_ltv": {"type": "number", "minimum": 50, "maximum": 100},
                        "upfront_mip_rate": {"type": "number", "minimum": 0, "maximum": 10},
                        "annual_mip_rate": {"type": "number", "minimum": 0, "maximum": 5},
                        "description": {"type": "string", "minLength": 1}
                    }
                },
                "va": {
                    "type": "object",
                    "required": ["min_down_payment", "max_ltv", "funding_fee_rates", "description"],
                    "properties": {
                        "min_down_payment": {"type": "number", "minimum": 0, "maximum": 100},
                        "max_ltv": {"type": "number", "minimum": 50, "maximum": 100},
                        "funding_fee_rates": {
                            "type": "object",
                            "required": ["funding_fee"],
                            "properties": {
                                "funding_fee": {
                                    "type": "object",
                                    "required": ["active", "reserves"],
                                    "properties": {
                                        "active": {"$ref": "#/definitions/va_service_rates"},
                                        "reserves": {"$ref": "#/definitions/va_service_rates"}
                                    }
                                }
                            }
                        },
                        "description": {"type": "string", "minLength": 1}
                    }
                },
                "usda": {
                    "type": "object",
                    "required": ["min_down_payment", "max_ltv", "upfront_fee_rate", "annual_fee_rate", "description"],
                    "properties": {
                        "min_down_payment": {"type": "number", "minimum": 0, "maximum": 100},
                        "max_ltv": {"type": "number", "minimum": 50, "maximum": 100},
                        "upfront_fee_rate": {"type": "number", "minimum": 0, "maximum": 10},
                        "annual_fee_rate": {"type": "number", "minimum": 0, "maximum": 5},
                        "description": {"type": "string", "minLength": 1}
                    }
                },
                "jumbo": {
                    "type": "object",
                    "required": ["min_down_payment", "max_ltv", "description"],
                    "properties": {
                        "min_down_payment": {"type": "number", "minimum": 0, "maximum": 100},
                        "max_ltv": {"type": "number", "minimum": 50, "maximum": 100},
                        "description": {"type": "string", "minLength": 1}
                    }
                }
            },
            "additionalProperties": False
        },
        "limits": {
            "type": "object",
            "required": ["max_interest_rate", "max_loan_term", "min_purchase_price", "max_purchase_price"],
            "properties": {
                "max_interest_rate": {"type": "number", "minimum": 1, "maximum": 50},
                "max_loan_term": {"type": "integer", "minimum": 5, "maximum": 50},
                "min_purchase_price": {"type": "number", "minimum": 1000},
                "max_purchase_price": {"type": "number", "minimum": 100000},
                "max_seller_credit_percentage": {"type": "number", "minimum": 0, "maximum": 20},
                "max_lender_credit_percentage": {"type": "number", "minimum": 0, "maximum": 20},
                "max_points": {"type": "number", "minimum": 0, "maximum": 10}
            }
        },
        "prepaid_items": {
            "type": "object",
            "required": ["months_insurance_prepaid", "months_tax_prepaid"],
            "properties": {
                "months_insurance_prepaid": {"type": "number", "minimum": 0, "maximum": 24},
                "months_tax_prepaid": {"type": "number", "minimum": 0, "maximum": 24},
                "months_insurance_escrow": {"type": "number", "minimum": 0, "maximum": 12},
                "months_tax_escrow": {"type": "number", "minimum": 0, "maximum": 12},
                "days_interest_prepaid": {"type": "integer", "minimum": 0, "maximum": 365}
            }
        },
        "title_insurance": {
            "type": "object",
            "required": ["simultaneous_issuance_fee", "total_rates_tiers", "lender_rates_simultaneous_tiers"],
            "properties": {
                "simultaneous_issuance_fee": {"type": "number", "minimum": 0},
                "lender_rate_waiver_multiplier": {"type": "number", "minimum": 0.5, "maximum": 5},
                "comment": {"type": "string"},
                "total_rates_tiers": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"$ref": "#/definitions/rate_tier"}
                },
                "lender_rates_simultaneous_tiers": {
                    "type": "array",
                    "minItems": 1,
                    "items": {"$ref": "#/definitions/rate_tier"}
                }
            }
        }
    },
    "definitions": {
        "va_service_rates": {
            "type": "object",
            "required": ["less_than_5", "5_to_10", "10_or_more"],
            "properties": {
                "less_than_5": {"$ref": "#/definitions/va_usage_rates"},
                "5_to_10": {"$ref": "#/definitions/va_usage_rates"},
                "10_or_more": {"$ref": "#/definitions/va_usage_rates"}
            }
        },
        "va_usage_rates": {
            "type": "object",
            "required": ["first", "subsequent"],
            "properties": {
                "first": {"type": "number", "minimum": 0, "maximum": 10},
                "subsequent": {"type": "number", "minimum": 0, "maximum": 10}
            }
        },
        "rate_tier": {
            "type": "object",
            "required": ["rate_percentage"],
            "properties": {
                "up_to": {"type": ["number", "null"], "minimum": 0},
                "rate_percentage": {"type": "number", "minimum": 0, "maximum": 5}
            }
        }
    }
}

# Closing Costs Configuration Schema
CLOSING_COSTS_SCHEMA = {
    "type": "object",
    "patternProperties": {
        "^[a-zA-Z_']+$": {  # Allow apostrophes in field names
            "type": "object",
            "required": ["type", "value", "calculation_base", "description", "applies_to"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["fixed", "percentage"]
                },
                "value": {
                    "type": "number",
                    "minimum": 0
                },
                "calculation_base": {
                    "type": "string",
                    "enum": ["fixed", "loan_amount", "purchase_price", "appraised_value"]
                },
                "description": {
                    "type": "string",
                    "minLength": 1
                },
                "applies_to": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["Purchase", "Refinance", "Cash-Out"]
                    },
                    "minItems": 1
                }
            },
            "additionalProperties": False
        }
    },
    "additionalProperties": False
}

# PMI Rates Configuration Schema
PMI_RATES_SCHEMA = {
    "type": "object",
    "required": ["conventional", "fha"],
    "properties": {
        "conventional": {
            "type": "object",
            "required": ["ltv_ranges"],
            "properties": {
                "ltv_ranges": {
                    "type": "object",
                    "patternProperties": {
                        "^[0-9.]+\\-[0-9.]+$": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 5
                        }
                    }
                },
                "credit_score_adjustments": {
                    "type": "object"
                }
            }
        },
        "fha": {
            "type": "object",
            "required": ["upfront_mip_rate", "annual_mip"],
            "properties": {
                "upfront_mip_rate": {"type": "number", "minimum": 0, "maximum": 10},
                "annual_mip": {
                    "type": "object",
                    "required": ["long_term", "short_term"],
                    "properties": {
                        "long_term": {"$ref": "#/definitions/mip_structure"},
                        "short_term": {"$ref": "#/definitions/mip_structure"}
                    }
                },
                "standard_loan_limit": {"type": "number", "minimum": 100000},
                "high_cost_loan_limit": {"type": "number", "minimum": 100000}
            }
        },
        "usda": {
            "type": "object",
            "required": ["upfront_guarantee_fee", "annual_fee"],
            "properties": {
                "upfront_guarantee_fee": {"type": "number", "minimum": 0, "maximum": 10},
                "annual_fee": {"type": "number", "minimum": 0, "maximum": 5},
                "ltv_ranges": {"type": "object"},
                "credit_score_adjustments": {"type": "object"}
            }
        },
        "va": {
            "type": "object",
            "required": ["funding_fee"],
            "properties": {
                "funding_fee": {
                    "type": "object",
                    "required": ["active", "reserves"],
                    "properties": {
                        "active": {"$ref": "#/definitions/va_down_payment_ranges"},
                        "reserves": {"$ref": "#/definitions/va_down_payment_ranges"},
                        "disability_exempt": {"type": "boolean"}
                    }
                }
            }
        }
    },
    "definitions": {
        "mip_structure": {
            "type": "object",
            "properties": {
                "standard_amount": {
                    "type": "object",
                    "properties": {
                        "low_ltv": {"type": "number", "minimum": 0, "maximum": 5},
                        "high_ltv": {"type": "number", "minimum": 0, "maximum": 5},
                        "very_low_ltv": {"type": "number", "minimum": 0, "maximum": 5}
                    }
                },
                "high_amount": {
                    "type": "object",
                    "properties": {
                        "low_ltv": {"type": "number", "minimum": 0, "maximum": 5},
                        "high_ltv": {"type": "number", "minimum": 0, "maximum": 5},
                        "very_low_ltv": {"type": "number", "minimum": 0, "maximum": 5}
                    }
                }
            }
        },
        "va_down_payment_ranges": {
            "type": "object",
            "required": ["less_than_5", "5_to_10", "10_or_more"],
            "properties": {
                "less_than_5": {"$ref": "#/definitions/va_usage_rates"},
                "5_to_10": {"$ref": "#/definitions/va_usage_rates"},
                "10_or_more": {"$ref": "#/definitions/va_usage_rates"}
            }
        },
        "va_usage_rates": {
            "type": "object",
            "required": ["first", "subsequent"],
            "properties": {
                "first": {"type": "number", "minimum": 0, "maximum": 10},
                "subsequent": {"type": "number", "minimum": 0, "maximum": 10}
            }
        }
    }
}


# Compliance Text Schema (optional file)
COMPLIANCE_TEXT_SCHEMA = {
    "type": "object",
    "properties": {
        "disclosures": {
            "type": "object",
            "properties": {
                "truth_in_lending": {"type": "string"},
                "good_faith_estimate": {"type": "string"},
                "privacy_notice": {"type": "string"}
            }
        },
        "disclaimers": {
            "type": "object",
            "properties": {
                "estimate_disclaimer": {"type": "string"},
                "rate_disclaimer": {"type": "string"}
            }
        }
    }
}

# Output Templates Schema (optional file)
OUTPUT_TEMPLATES_SCHEMA = {
    "type": "object",
    "properties": {
        "loan_estimate": {
            "type": "object",
            "properties": {
                "template": {"type": "string"},
                "fields": {"type": "object"}
            }
        },
        "closing_disclosure": {
            "type": "object",
            "properties": {
                "template": {"type": "string"},
                "fields": {"type": "object"}
            }
        }
    }
}

# Map of config file names to their schemas
CONFIG_SCHEMAS = {
    "mortgage_config.json": MORTGAGE_CONFIG_SCHEMA,
    "closing_costs.json": CLOSING_COSTS_SCHEMA,
    "pmi_rates.json": PMI_RATES_SCHEMA,
    "compliance_text.json": COMPLIANCE_TEXT_SCHEMA,
    "output_templates.json": OUTPUT_TEMPLATES_SCHEMA
}

# Required configuration files (must exist and validate)
REQUIRED_CONFIG_FILES = [
    "mortgage_config.json",
    "closing_costs.json", 
    "pmi_rates.json"
]

# Optional configuration files (may not exist)
OPTIONAL_CONFIG_FILES = [
    "compliance_text.json",
    "output_templates.json"
]