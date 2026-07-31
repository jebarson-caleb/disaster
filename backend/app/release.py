"""Public, non-secret application release metadata."""

import os

APPLICATION_VERSION = "1.3.4"


def release_commit():
    return (
        os.getenv("VERCEL_GIT_COMMIT_SHA", "").strip().lower()
        or os.getenv("RESQ_RELEASE_COMMIT", "").strip().lower()
    )
