import os
import json
import hashlib
import settings
from pathlib import Path
from datetime import datetime


def get_module_name(file_path, project_root=settings.ROOT_DIR):
    """return a module name"""
    file_path = Path(file_path).resolve()
    project_root = Path(project_root).resolve()
    try:
        rel = file_path.relative_to(project_root)
        rel_no_suffix = rel.with_suffix("")
        return ".".join(rel_no_suffix.parts)
    except Exception:
        # fallback: try relative to current working directory
        try:
            rel = file_path.relative_to(Path.cwd())
            rel_no_suffix = rel.with_suffix("")
            return ".".join(rel_no_suffix.parts)
        except Exception:
            # final fallback: use the file name (no path)
            return file_path.with_suffix("").name


def get_timestamp():
    """get the current timestamp"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sha256_hash(data, length=16):
    """Return the SHA-256 hex digest of a string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]


def get_patterns(logger, file_path=settings.PATTERN_FILE):
    """Load all prompt injection patterns to memory"""
    if os.path.exists(file_path):
        with open(file_path, 'r') as fd:
            patterns = json.load(fd)
            logger.info(f"Loaded {len(patterns)} patterns.")
            return patterns
    logger.error(f"No patterns found at {file_path}")
    return []