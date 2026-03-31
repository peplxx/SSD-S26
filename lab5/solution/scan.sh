#!/usr/bin/env bash
# SAST scanning script – produces SARIF reports for all 3 projects
# Tools: Bandit (Python), njsscan (NodeJS), FlawFinder (C/C++)
# Projects: vulpy (Python), dvna (NodeJS), dvca (C)
#
# Prerequisites:
#   python3 -m venv venv && source venv/bin/activate
#   pip install bandit bandit-sarif-formatter flawfinder
#
# NOTE: njsscan is run via Docker because semgrep>=1.47 is no longer
#       published to PyPI and cannot be installed with pip.
#   docker pull opensecurity/njsscan

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECTS_DIR="${1:-$SCRIPT_DIR/projects}"
REPORTS_DIR="${SCRIPT_DIR}/reports"

mkdir -p "$REPORTS_DIR"

echo "==> Projects directory : $PROJECTS_DIR"
echo "==> Reports directory  : $REPORTS_DIR"
echo ""

# ---------------------------------------------------------------------------
# Helper: check that a required tool is available
# ---------------------------------------------------------------------------
require_tool() {
    if ! command -v "$1" &>/dev/null; then
        echo "[ERROR] '$1' not found."
        echo "  For bandit/flawfinder: activate your venv and run: pip install bandit flawfinder"
        echo "  For docker: install Docker Desktop"
        exit 1
    fi
}

require_tool bandit
require_tool flawfinder
require_tool docker

# bandit-sarif-formatter registers itself as a bandit formatter plugin.
# Check it's installed so -f sarif works.
if ! python3 -c "import bandit_sarif_formatter" 2>/dev/null; then
    echo "[ERROR] bandit-sarif-formatter not found."
    echo "  Run: pip install bandit-sarif-formatter"
    exit 1
fi

# ---------------------------------------------------------------------------
# 1. Bandit – Python SAST → scan vulpy
# ---------------------------------------------------------------------------
echo ">>> [1/3] Bandit scanning vulpy (Python) ..."
VULPY="$PROJECTS_DIR/vulpy"

if [ ! -d "$VULPY" ]; then
    echo "    Cloning vulpy ..."
    git clone --depth 1 https://github.com/fportantier/vulpy "$VULPY"
    rm -rf "$VULPY/.git"
fi

bandit \
    -r "$VULPY" \
    -f sarif \
    -o "$REPORTS_DIR/bandit_vulpy.sarif" \
    --exit-zero          # don't fail the script on findings

echo "    Saved -> $REPORTS_DIR/bandit_vulpy.sarif"

# ---------------------------------------------------------------------------
# 2. njsscan – NodeJS SAST → scan dvna  (run via Docker)
#
# Why Docker?  njsscan 0.4.x pins semgrep==1.86.0 which is not published
# to PyPI (semgrep stopped distributing via pip after 1.46.0).
# The opensecurity/njsscan Docker image ships the correct semgrep version.
# ---------------------------------------------------------------------------
echo ""
echo ">>> [2/3] njsscan scanning dvna (NodeJS) via Docker ..."
DVNA="$PROJECTS_DIR/dvna"

if [ ! -d "$DVNA" ]; then
    echo "    Cloning dvna ..."
    git clone --depth 1 https://github.com/appsecco/dvna "$DVNA"
    rm -rf "$DVNA/.git"
fi

# Pull the image if not already present
docker pull opensecurity/njsscan --quiet

# Run the scan; mount the project as /src and the reports dir as /reports.
# njsscan exits 1 when it finds vulnerabilities, so we tolerate that with ||true.
docker run --rm \
    -v "$DVNA:/src" \
    -v "$REPORTS_DIR:/reports" \
    opensecurity/njsscan \
    --sarif -o /reports/njsscan_dvna.sarif /src || true

echo "    Saved -> $REPORTS_DIR/njsscan_dvna.sarif"

# ---------------------------------------------------------------------------
# 3. FlawFinder – C/C++ SAST → scan dvca
# ---------------------------------------------------------------------------
echo ""
echo ">>> [3/3] FlawFinder scanning dvca (C) ..."
DVCA="$PROJECTS_DIR/dvca"

if [ ! -d "$DVCA" ]; then
    echo "    Cloning dvca ..."
    git clone --depth 1 https://github.com/hardik05/Damn_Vulnerable_C_Program "$DVCA"
    mv "$SCRIPT_DIR/projects/Damn_Vulnerable_C_Program" "$DVCA" 2>/dev/null || true
    rm -rf "$DVCA/.git"
fi

flawfinder \
    --sarif \
    "$DVCA" \
    > "$REPORTS_DIR/flawfinder_dvca.sarif"

echo "    Saved -> $REPORTS_DIR/flawfinder_dvca.sarif"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "========================================================="
echo " Scan complete. Reports:"
ls -lh "$REPORTS_DIR"/*.sarif
echo "========================================================="
echo ""
echo "Next step: python import_to_dojo.py"
