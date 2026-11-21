"""Platform model and policy version constants."""

from __future__ import annotations

import os

MODEL_VERSION: str = "1.1.0"
POLICY_VERSION: str = "2.1.0"
GIT_SHA: str = os.getenv("GIT_SHA", "3acc779")
GIT_TAG: str = os.getenv("GIT_TAG", "sprint-10")
BUILD_TIME: str = os.getenv("BUILD_TIME", "2026-11-21T13:16:00Z")
