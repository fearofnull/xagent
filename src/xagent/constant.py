# -*- coding: utf-8 -*-
import os
from pathlib import Path

WORKING_DIR = (
    Path(os.environ.get("XAGENT_WORKING_DIR", "~/.xagent"))
    .expanduser()
    .resolve()
)
SECRET_DIR = (
    Path(
        os.environ.get(
            "XAGENT_SECRET_DIR",
            f"{WORKING_DIR}.secret",
        ),
    )
    .expanduser()
    .resolve()
)

# Memory compaction configuration
MEMORY_COMPACT_KEEP_RECENT = int(
    os.environ.get("XAGENT_MEMORY_COMPACT_KEEP_RECENT", "3"),
)

MEMORY_COMPACT_RATIO = float(
    os.environ.get("XAGENT_MEMORY_COMPACT_RATIO", "0.7"),
)

# Browser configuration
PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH_ENV = "XAGENT_PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH"
RUNNING_IN_CONTAINER = os.environ.get("XAGENT_RUNNING_IN_CONTAINER", "")

# Skills directories
# Active skills directory (activated skills that agents use)
ACTIVE_SKILLS_DIR = WORKING_DIR / "active_skills"
# Customized skills directory (user-created skills)
CUSTOMIZED_SKILLS_DIR = WORKING_DIR / "customized_skills"

# Web Admin configuration
WEB_ADMIN_URL = os.getenv("WEB_ADMIN_URL", "http://localhost:8080")
WEB_ADMIN_TOKEN = os.getenv("WEB_ADMIN_TOKEN", "")

# File paths
HEARTBEAT_FILE = "HEARTBEAT.md"
JOBS_FILE = "jobs.json"
CHATS_FILE = "chats.json"