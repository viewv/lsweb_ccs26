import os

# Read TASK_ID from environment (use `TASK_ID` or fallback `TASK`)
TASK_ID = os.environ.get("TASK_ID") or os.environ.get("TASK") or ""

HOME_DIR = os.path.dirname(os.path.abspath(__file__))

# ROOT_DIR base (default project prompt folder)
ROOT_DIR_BASE = "/tmp/crawler_outputs"
if TASK_ID:
	ROOT_DIR = os.path.join(ROOT_DIR_BASE, TASK_ID)
else:
	ROOT_DIR = ROOT_DIR_BASE

# Outputs directory under the computed ROOT_DIR
OUT_DIR = os.path.join(ROOT_DIR, "outputs")

# Ensure OUT_DIR exists
os.makedirs(OUT_DIR, exist_ok=True)

# pattern file path in current path
PATTERN_FILE = os.path.join(HOME_DIR, "patterns", "patterns.json")

DATA_DIR_COMMONCRAWL = os.path.join(OUT_DIR, "commoncrawl")

DATA_DIR_SHODAN = os.path.join(OUT_DIR, "shodan")
DATA_DIR_CENSYS = os.path.join(OUT_DIR, "censys")
