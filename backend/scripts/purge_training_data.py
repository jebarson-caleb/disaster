"""Preview or execute the exact production acceptance-data purge."""

import argparse
import json
import sys

from app import create_app
from app.maintenance import PURGE_CONFIRMATION, build_training_cleanup_plan, purge_training_data


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="commit the guarded purge; default is read-only")
    parser.add_argument("--confirmation", help=f"required with --execute: {PURGE_CONFIRMATION}")
    return parser.parse_args()


def main():
    args = parse_args()
    app = create_app()
    if app.config.get("APP_ENV") != "production":
        raise RuntimeError("this command requires APP_ENV=production")
    if str(app.config.get("SQLALCHEMY_DATABASE_URI", "")).startswith("sqlite"):
        raise RuntimeError("refusing to run against SQLite")

    with app.app_context():
        result = purge_training_data(args.confirmation) if args.execute else build_training_cleanup_plan()
        print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
        if not result.ready:
            return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(json.dumps({"error": str(error)}, indent=2), file=sys.stderr)
        sys.exit(1)
