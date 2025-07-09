#!/usr/bin/env python3
"""
Verification script to check if the mortgage calculator is properly configured
with all expected features before deployment.

This helps ensure that the version deployed to Render includes all required functionality.
"""
import json
import os
import sys

from VERSION import FEATURES, VERSION


def check_feature_files():
    """Check that all necessary files for features exist"""
    required_files = {
        "seller_credits": ["static/js/ui/tableUpdaters.js", "templates/index.html", "app.py"],
        "lender_credits": ["static/js/ui/tableUpdaters.js", "templates/index.html", "app.py"],
    }

    missing_files = {}

    for feature, files in required_files.items():
        if feature in FEATURES:
            for file in files:
                if not os.path.exists(file):
                    if feature not in missing_files:
                        missing_files[feature] = []
                    missing_files[feature].append(file)

    return missing_files


def check_feature_code():
    """Check that feature-specific code exists in key files"""
    checks = {
        "seller_credits": [
            {
                "file": "static/js/ui/tableUpdaters.js",
                "patterns": ["sellerCredit", "seller_credit", "updateCreditsTable"],
            },
            {
                "file": "templates/index.html",
                "patterns": ["seller_credit", "Seller Credit"],
            },
            {
                "file": "app.py",
                "patterns": ["seller_credit", "calculate_max_seller_contribution"],
            },
        ],
        "lender_credits": [
            {
                "file": "static/js/ui/tableUpdaters.js",
                "patterns": ["lenderCredit", "lender_credit"],
            },
            {
                "file": "templates/index.html",
                "patterns": ["lender_credit", "Lender Credit"],
            },
            {"file": "app.py", "patterns": ["lender_credit"]},
        ],
    }

    missing_code = {}

    for feature, check_list in checks.items():
        if feature in FEATURES:
            for check in check_list:
                if os.path.exists(check["file"]):
                    with open(check["file"], "r", encoding="utf-8") as f:
                        content = f.read()
                        missing_patterns = []
                        for pattern in check["patterns"]:
                            if pattern not in content:
                                missing_patterns.append(pattern)

                        if missing_patterns:
                            if feature not in missing_code:
                                missing_code[feature] = {}
                            missing_code[feature][check["file"]] = missing_patterns

    return missing_code


def main():
    print(f"Verifying Mortgage Calculator v{VERSION} deployment readiness")
    print(f"Checking for features: {', '.join(FEATURES)}")

    # Check for missing files
    missing_files = check_feature_files()
    if missing_files:
        print("\n❌ Missing required files:")
        for feature, files in missing_files.items():
            print(f"  - Feature '{feature}' is missing files: {', '.join(files)}")
    else:
        print("\n✅ All required files exist")

    # Check for missing code
    missing_code = check_feature_code()
    if missing_code:
        print("\n❌ Missing required code patterns:")
        for feature, file_patterns in missing_code.items():
            print(f"  - Feature '{feature}' is missing patterns:")
            for file, patterns in file_patterns.items():
                print(f"    - In {file}: {', '.join(patterns)}")
    else:
        print("\n✅ All required code patterns found")

    # Overall result
    if not missing_files and not missing_code:
        print("\n✅ Deployment verification PASSED - all features properly implemented")
        return 0
    else:
        print("\n❌ Deployment verification FAILED - missing files or code patterns")
        return 1


if __name__ == "__main__":
    sys.exit(main())
