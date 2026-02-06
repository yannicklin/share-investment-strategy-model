#!/usr/bin/env python3
"""
Pre-Deployment Validation Script

Runs comprehensive checks before deploying to Koyeb:
1. Import validation (all dependencies resolvable)
2. Database model validation (schema correctness)
3. Environment variable checks
4. API route validation
5. Configuration validation

Usage:
    python scripts/validate_deployment.py
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def check_imports():
    """Validate all critical imports"""
    print("=" * 70)
    print("1. CHECKING IMPORTS")
    print("=" * 70)

    checks = []

    # Core dependencies
    try:
        import flask

        checks.append(("Flask", flask.__version__, "✅"))
    except ImportError as e:
        checks.append(("Flask", str(e), "❌"))

    try:
        import flask_sqlalchemy

        checks.append(("Flask-SQLAlchemy", flask_sqlalchemy.__version__, "✅"))
    except ImportError as e:
        checks.append(("Flask-SQLAlchemy", str(e), "❌"))

    try:
        import sqlalchemy

        checks.append(("SQLAlchemy", sqlalchemy.__version__, "✅"))
    except ImportError as e:
        checks.append(("SQLAlchemy", str(e), "❌"))

    try:
        import psycopg2

        checks.append(("psycopg2", psycopg2.__version__, "✅"))
    except ImportError as e:
        checks.append(("psycopg2", str(e), "❌"))

    # Market data
    try:
        import yfinance

        checks.append(("yfinance", yfinance.__version__, "✅"))
    except ImportError as e:
        checks.append(("yfinance", str(e), "❌"))

    try:
        import pandas

        checks.append(("pandas", pandas.__version__, "✅"))
    except ImportError as e:
        checks.append(("pandas", str(e), "❌"))

    try:
        import numpy

        checks.append(("numpy", numpy.__version__, "✅"))
    except ImportError as e:
        checks.append(("numpy", str(e), "❌"))

    # AI/ML
    try:
        import sklearn

        checks.append(("scikit-learn", sklearn.__version__, "✅"))
    except ImportError as e:
        checks.append(("scikit-learn", str(e), "❌"))

    try:
        import catboost

        checks.append(("catboost", catboost.__version__, "✅"))
    except ImportError as e:
        checks.append(("catboost", str(e), "❌"))

    # Notifications
    try:
        import requests

        checks.append(("requests", requests.__version__, "✅"))
    except ImportError as e:
        checks.append(("requests", str(e), "❌"))

    # Display results
    for name, version, status in checks:
        print(f"{status} {name:20s} {version}")

    failures = [c for c in checks if c[2] == "❌"]
    if failures:
        print(f"\n❌ {len(failures)} import(s) failed")
        return False

    print(f"\n✅ All {len(checks)} imports successful")
    return True


def check_app_structure():
    """Validate Flask app structure"""
    print("\n" + "=" * 70)
    print("2. CHECKING APP STRUCTURE")
    print("=" * 70)

    checks = []

    # Check app factory
    try:
        from app.bot import create_app

        app = create_app()
        checks.append(("Flask app factory", f"App created: {app.name}", "✅"))
    except Exception as e:
        checks.append(("Flask app factory", str(e), "❌"))
        for name, result, status in checks:
            print(f"{status} {name:30s} {result}")
        return False

    # Check database initialization
    try:
        from app.bot import db

        checks.append(("Database extension", "SQLAlchemy initialized", "✅"))
    except Exception as e:
        checks.append(("Database extension", str(e), "❌"))

    # Check models
    try:
        from app.bot.shared.models import Signal, ConfigProfile, JobLog, ApiCredential

        checks.append(("Database models", "All models imported", "✅"))
    except Exception as e:
        checks.append(("Database models", str(e), "❌"))

    # Check services
    try:
        from app.bot.services.signal_engine import generate_daily_signals

        checks.append(("Signal engine service", "Function imported", "✅"))
    except Exception as e:
        checks.append(("Signal engine service", str(e), "❌"))

    try:
        from app.bot.services.notification_service import notify_signals

        checks.append(("Notification service", "Function imported", "✅"))
    except Exception as e:
        checks.append(("Notification service", str(e), "❌"))

    # Check market services
    try:
        from app.bot.markets.asx.signal_service import ASXSignalService

        checks.append(("ASX market service", "Class imported", "✅"))
    except Exception as e:
        checks.append(("ASX market service", str(e), "❌"))

    # Check API routes
    try:
        from app.bot.api.cron_routes import cron_bp

        checks.append(("Cron API routes", "Blueprint imported", "✅"))
    except Exception as e:
        checks.append(("Cron API routes", str(e), "❌"))

    # Display results
    for name, result, status in checks:
        print(f"{status} {name:30s} {result}")

    failures = [c for c in checks if c[2] == "❌"]
    if failures:
        print(f"\n❌ {len(failures)} structure check(s) failed")
        return False

    print(f"\n✅ All {len(checks)} structure checks passed")
    return True


def check_core_module():
    """Validate core module availability"""
    print("\n" + "=" * 70)
    print("3. CHECKING CORE MODULE (from main/ASX branch)")
    print("=" * 70)

    checks = []

    try:
        from core.model_builder import ModelBuilder

        checks.append(("ModelBuilder import", "✅"))

        # Test instantiation
        builder = ModelBuilder()
        checks.append(("ModelBuilder instantiation", "✅"))

        # Check available model types
        if hasattr(builder, "config"):
            checks.append(("ModelBuilder config", "✅"))
        else:
            checks.append(("ModelBuilder config", "❌"))

    except ImportError as e:
        checks.append(("ModelBuilder import", f"❌ {str(e)}"))
    except Exception as e:
        checks.append(("ModelBuilder usage", f"❌ {str(e)}"))

    # Display results
    for check in checks:
        if len(check) == 2:
            name, status = check
            print(f"{status} {name}")
        else:
            name, message = check
            print(f"{message}")

    return all("✅" in str(c) for c in checks)


def check_environment():
    """Check environment variables"""
    print("\n" + "=" * 70)
    print("4. CHECKING ENVIRONMENT VARIABLES")
    print("=" * 70)

    required_vars = ["DATABASE_URL", "CRON_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]

    optional_vars = [
        "BACKUP_ENCRYPTION_KEY",
        "SENDGRID_API_KEY",
        "TELNYX_API_KEY",
        "TIGRIS_ACCESS_KEY_ID",
    ]

    print("Required:")
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✅ {var:25s} {masked}")
        else:
            print(f"❌ {var:25s} NOT SET")

    print("\nOptional:")
    for var in optional_vars:
        value = os.environ.get(var)
        if value:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✅ {var:25s} {masked}")
        else:
            print(f"⚠️  {var:25s} NOT SET")

    missing_required = [v for v in required_vars if not os.environ.get(v)]

    if missing_required:
        print(f"\n❌ Missing {len(missing_required)} required variable(s)")
        print("   Run: cp .env.example .env")
        print("   Then configure: DATABASE_URL, CRON_TOKEN, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID")
        return False

    print(f"\n✅ All required variables set")
    return True


def check_database_connection():
    """Test database connection"""
    print("\n" + "=" * 70)
    print("5. CHECKING DATABASE CONNECTION")
    print("=" * 70)

    try:
        from app.bot import create_app, db

        app = create_app()

        with app.app_context():
            # Try to connect
            db.engine.connect()
            print("✅ Database connection successful")

            # Check if tables exist
            from sqlalchemy import inspect

            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            expected_tables = ["signals", "config_profiles", "job_logs", "api_credentials"]

            print(f"\nExisting tables: {len(tables)}")
            for table in tables:
                exists = "✅" if table in expected_tables else "⚠️"
                print(f"   {exists} {table}")

            missing = [t for t in expected_tables if t not in tables]
            if missing:
                print(f"\n⚠️  Missing tables: {', '.join(missing)}")
                print("   Run: flask db upgrade")
                print("   Or: python run_bot.py (auto-creates tables)")

            return True

    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("   Check DATABASE_URL environment variable")
        return False


def main():
    """Run all validation checks"""
    print("\n🚀 PRE-DEPLOYMENT VALIDATION")
    print("=" * 70)

    results = {
        "Imports": check_imports(),
        "App Structure": check_app_structure(),
        "Core Module": check_core_module(),
        "Environment": check_environment(),
    }

    # Only check database if environment is configured
    if results["Environment"]:
        results["Database"] = check_database_connection()

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    for check, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status:12s} {check}")

    all_passed = all(results.values())

    if all_passed:
        print("\n" + "=" * 70)
        print("✅ ALL CHECKS PASSED - READY FOR DEPLOYMENT")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Initialize default profile: python scripts/init_default_profile.py")
        print("2. Test locally: python run_bot.py")
        print("3. Deploy to Koyeb: koyeb service create --config koyeb.yaml")
        sys.exit(0)
    else:
        print("\n" + "=" * 70)
        print("❌ VALIDATION FAILED - FIX ISSUES BEFORE DEPLOYMENT")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
