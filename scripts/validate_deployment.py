#!/usr/bin/env python3
"""
Deployment validation script to catch common issues before they cause server errors.
Run this script before deploying to catch format specifier errors, missing env vars, etc.
"""
import ast
import os
import re
import sys
from pathlib import Path

def check_environment_variables():
    """Check that required environment variables are set or documented."""
    print("🔍 Checking environment variables...")
    
    # Check for .env file locally
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("❌ .env file missing but .env.example exists")
        print("   Create .env file from .env.example")
        return False
    
    # Check that SECRET_KEY is set
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        print("❌ SECRET_KEY environment variable not set")
        return False
    
    print("✅ Environment variables OK")
    return True

def check_format_specifiers():
    """Check Python files for invalid format specifiers."""
    print("🔍 Checking f-string format specifiers...")
    
    issues = []
    python_files = Path(".").glob("**/*.py")
    
    # Pattern to find f-strings with potential format specifier issues
    # Look for patterns like :, .2f (space after comma)
    invalid_pattern = re.compile(r'{\w+:\s*,\s+\.\d+f}')
    
    for file_path in python_files:
        if "venv" in str(file_path) or "__pycache__" in str(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for invalid format specifiers
            matches = invalid_pattern.findall(content)
            if matches:
                issues.append(f"{file_path}: {matches}")
                
        except Exception as e:
            print(f"⚠️  Could not read {file_path}: {e}")
    
    if issues:
        print("❌ Invalid format specifiers found:")
        for issue in issues:
            print(f"   {issue}")
        print("   Fix by removing spaces: use ':,.2f' not ':, .2f'")
        return False
    
    print("✅ Format specifiers OK")
    return True

def check_dependency_consistency():
    """Check that dependency versions are consistent across files."""
    print("🔍 Checking dependency version consistency...")
    
    # Check gunicorn version in requirements.txt vs start.sh
    requirements_file = Path("requirements.txt")
    start_script = Path("start.sh")
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    # Extract gunicorn version from requirements.txt
    requirements_content = requirements_file.read_text()
    gunicorn_req = None
    for line in requirements_content.split('\n'):
        if line.startswith('gunicorn=='):
            gunicorn_req = line.strip()
            break
    
    if not gunicorn_req:
        print("⚠️  Gunicorn version not specified in requirements.txt")
        return True
    
    # Check start.sh if it exists
    if start_script.exists():
        start_content = start_script.read_text()
        if 'pip install gunicorn==' in start_content:
            # Extract version from start.sh
            import re
            pattern = r'pip install gunicorn==([0-9\.]+)'
            match = re.search(pattern, start_content)
            if match:
                start_version = match.group(1)
                req_version = gunicorn_req.split('==')[1]
                if start_version != req_version:
                    print(f"❌ Gunicorn version mismatch:")
                    print(f"   requirements.txt: {req_version}")
                    print(f"   start.sh: {start_version}")
                    return False
    
    print("✅ Dependency versions OK")
    return True

def check_critical_imports():
    """Check that critical imports are available."""
    print("🔍 Checking critical imports...")
    
    try:
        import flask
        import decimal
        import logging
        print("✅ Critical imports OK")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Run all validation checks."""
    print("🚀 Running deployment validation checks...\n")
    
    checks = [
        check_environment_variables,
        check_format_specifiers, 
        check_dependency_consistency,
        check_critical_imports
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()  # Add spacing between checks
    
    if all_passed:
        print("🎉 All validation checks passed! Safe to deploy.")
        return 0
    else:
        print("💥 Some validation checks failed. Fix issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())