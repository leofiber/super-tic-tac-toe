#!/bin/bash
# Build script for Render deployment

# Ensure we have the right Python version
python3 --version

# Upgrade pip and install build tools first
pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r requirements.txt

echo "Build completed successfully!"
