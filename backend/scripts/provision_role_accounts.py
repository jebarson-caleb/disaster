"""Preview or execute guarded provisioning of one live account per application role."""

import argparse
import json
import os
import sys

from app import create_app
from app.role_account_provisioning import (
    PROVISION_CONFIRMATION,
    build_role_account_plan,
    provision_role_accounts,
    verify_role_accounts,
)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--execute", action="store_true", help="commit missing accounts; default is read-only")
    action.add_argument("--verify", action="store_true", help="verify supplied credentials and role bindings read-only")
    parser.add_argument("--confirmation", help=f"required with --execute: {PROVISION_CONFIRMATION}")
    parser.add_argument(
        "--reissue-managed",
        action="store_true",
        help="replace credentials only for test accounts previously created by this command",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    app = create_app()
    if app.config.get("APP_ENV") != "production":
        raise RuntimeError("this command requires APP_ENV=production")
    if str(app.config.get("SQLALCHEMY_DATABASE_URI", "")).startswith("sqlite"):
        raise RuntimeError("refusing to run against SQLite")
    if app.config.get("DEMO_MODE"):
        raise RuntimeError("refusing to provision live accounts while DEMO_MODE is enabled")

    with app.app_context():
        if args.execute or args.verify:
            raw_passwords = os.getenv("LIVE_ROLE_ACCOUNT_PASSWORDS_JSON", "")
            if not raw_passwords:
                raise RuntimeError("LIVE_ROLE_ACCOUNT_PASSWORDS_JSON is required with --execute or --verify")
            try:
                passwords = json.loads(raw_passwords)
            except json.JSONDecodeError as error:
                raise RuntimeError("LIVE_ROLE_ACCOUNT_PASSWORDS_JSON must contain valid JSON") from error
            if args.execute:
                result = provision_role_accounts(
                    passwords,
                    args.confirmation,
                    reissue_managed=args.reissue_managed,
                )
            else:
                result = verify_role_accounts(passwords)
        else:
            result = build_role_account_plan()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("ready", True) else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(json.dumps({"error": str(error)}, indent=2), file=sys.stderr)
        sys.exit(1)
