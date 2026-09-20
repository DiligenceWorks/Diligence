#!/bin/bash
# =============================================================================
# Diligence Portable Build Script
# Assembles a zero-install portable distribution for Windows 10 x64
#
# Run this on a Linux build host (subo). It downloads the Windows embeddable
# Python, cross-downloads Windows wheels, and packages everything into a zip
# that the end user extracts and double-clicks start.bat.
#
# Usage: ./build.sh [PYTHON_VERSION]
# Output: dist/Diligence-portable-win64.zip
# =============================================================================
set -euo pipefail

# --- Configuration -----------------------------------------------------------
PYTHON_VERSION="${1:-3.12.10}"
PYTHON_MAJOR_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f1,2)
PYTHON_TAG=$(echo "$PYTHON_MAJOR_MINOR" | tr -d '.')

APP_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$APP_ROOT/portable/build"
DIST_DIR="$APP_ROOT/portable/dist"
STAGE="$BUILD_DIR/Diligence"
WHEELS_DIR="$BUILD_DIR/wheels"

PYTHON_EMBED_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-embed-amd64.zip"

OUTPUT_ZIP="$DIST_DIR/Diligence-portable-win64.zip"

echo ""
echo "  Diligence Portable Build"
echo "  Python: ${PYTHON_VERSION} (embed amd64)"
echo "  App root: ${APP_ROOT}"
echo ""

# --- Clean -------------------------------------------------------------------
rm -rf "$BUILD_DIR" "$DIST_DIR"
mkdir -p "$STAGE" "$WHEELS_DIR" "$DIST_DIR"

# --- Step 1: Download embeddable Python --------------------------------------
echo "  [1/6] Downloading embeddable Python ${PYTHON_VERSION}..."
curl -sL -o "$BUILD_DIR/python-embed.zip" "$PYTHON_EMBED_URL"
mkdir -p "$STAGE/python"
unzip -q "$BUILD_DIR/python-embed.zip" -d "$STAGE/python"
rm "$BUILD_DIR/python-embed.zip"

# --- Step 2: Configure Python import paths -----------------------------------
echo "  [2/6] Configuring Python import paths..."

# The ._pth file controls sys.path for the embeddable Python.
# Paths are relative to the python/ directory.
cat > "$STAGE/python/python${PYTHON_TAG}._pth" << EOF
python${PYTHON_TAG}.zip
.
..
../lib
import site
EOF

# --- Step 3: Download Windows wheels -----------------------------------------
echo "  [3/6] Downloading Windows wheels..."

# We download binary wheels for Windows from PyPI using the Linux pip.
# --platform win_amd64 fetches Windows-specific binaries.
# --no-deps because we manage the dependency list explicitly to avoid
# pulling in unnecessary transitive deps.

# Core dependencies (from pyproject.toml)
CORE_DEPS=(
    "fastapi>=0.115.0"
    "uvicorn>=0.30.0"
    "sqlalchemy>=2.0.30"
    "aiosqlite>=0.20.0"
    "pydantic>=2.10.0"
    "pydantic-settings>=2.7.0"
    "pydantic-core"
    "python-jose>=3.3.0"
    "cryptography"
    "bcrypt>=4.2.0"
    "httpx>=0.27.0"
    "python-multipart>=0.0.18"
    "tzdata>=2024.1"
)

# Transitive dependencies (required by core deps)
TRANSITIVE_DEPS=(
    "annotated-types"
    "typing-extensions"
    "anyio"
    "sniffio"
    "idna"
    "certifi"
    "httpcore"
    "h11"
    "starlette"
    "click"
    "jinja2"
    "markupsafe"
    "ecdsa"
    "rsa"
    "pyasn1"
    "cffi"
    "pycparser"
    "greenlet"
    "python-dotenv"
)

download_wheel() {
    local pkg="$1"
    # Try platform-specific binary first
    pip download \
        --platform win_amd64 \
        --python-version "$PYTHON_MAJOR_MINOR" \
        --only-binary :all: \
        --dest "$WHEELS_DIR" \
        --no-deps \
        "$pkg" 2>/dev/null && return 0

    # Fall back to pure-python wheel (no platform restriction needed)
    pip download \
        --python-version "$PYTHON_MAJOR_MINOR" \
        --dest "$WHEELS_DIR" \
        --no-deps \
        "$pkg" 2>/dev/null && return 0

    echo "    WARNING: Could not download $pkg"
    return 1
}

for pkg in "${CORE_DEPS[@]}" "${TRANSITIVE_DEPS[@]}"; do
    download_wheel "$pkg" || true
done

# MCP connector (optional — included if available)
download_wheel "fastmcp>=3.0.0" || echo "  (fastmcp unavailable — MCP will be optional)"

# --- Step 4: Extract wheels into lib/ ----------------------------------------
echo "  [4/6] Extracting wheels into lib/..."
mkdir -p "$STAGE/lib"
for whl in "$WHEELS_DIR"/*.whl; do
    [ -f "$whl" ] || continue
    unzip -qo "$whl" -d "$STAGE/lib"
done

# Clean .dist-info (saves space, not needed at runtime)
find "$STAGE/lib" -type d -name "*.dist-info" -exec rm -rf {} + 2>/dev/null || true
# Remove any .tar.gz source dists that snuck in
rm -f "$WHEELS_DIR"/*.tar.gz 2>/dev/null || true

# --- Step 5: Copy application code ------------------------------------------
echo "  [5/6] Copying application code..."

# Copy the diligence package (includes pre-built frontend at diligence/frontend/)
cp -r "$APP_ROOT/diligence" "$STAGE/diligence"

# Remove __pycache__
find "$STAGE/diligence" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# Copy supporting files
cp "$APP_ROOT/LICENSE" "$STAGE/"

# Create data directory placeholder
mkdir -p "$STAGE/data"

# Copy launchers and README from portable/
cp "$APP_ROOT/portable/start.bat" "$STAGE/"
cp "$APP_ROOT/portable/start.sh" "$STAGE/"
cp "$APP_ROOT/portable/README.txt" "$STAGE/"

# --- Step 6: Package --------------------------------------------------------
echo "  [6/6] Creating zip..."

# Use system zip if available, otherwise use Docker Alpine
if command -v zip &>/dev/null; then
    cd "$BUILD_DIR"
    zip -qr "$OUTPUT_ZIP" Diligence/
    cd "$APP_ROOT"
else
    echo "    (zip not installed — using Docker Alpine)"
    sg docker -c "docker run --rm \
        -v '$BUILD_DIR':/build \
        -v '$DIST_DIR':/dist \
        -w /build \
        alpine sh -c 'apk add --no-cache -q zip && zip -qr /dist/Diligence-portable-win64.zip Diligence/'"
fi

# --- Report ------------------------------------------------------------------
ZIP_SIZE=$(du -sh "$OUTPUT_ZIP" | cut -f1)
STAGE_SIZE=$(du -sh "$STAGE" | cut -f1)

echo ""
echo "  Build complete:"
echo "    Zip:            $OUTPUT_ZIP ($ZIP_SIZE)"
echo "    Extracted size: $STAGE_SIZE"
echo "    Python:         $PYTHON_VERSION (embed amd64)"
echo ""
echo "  Test on Windows:"
echo "    1. Extract zip to any folder"
echo "    2. Double-click start.bat"
echo "    3. Browser opens to http://localhost:8000"
echo ""
