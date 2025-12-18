#!/bin/bash

# Documentation Linter Script
# Checks for broken links and common issues in documentation.

DOCS_DIR="docs"

echo "Checking documentation in $DOCS_DIR..."

# Check if markdown-link-check is installed
if command -v markdown-link-check &> /dev/null; then
    echo "Running markdown-link-check..."
    find "$DOCS_DIR" -name "*.md" -print0 | xargs -0 -n1 markdown-link-check
else
    echo "WARNING: markdown-link-check is not installed."
    echo "To install: npm install -g markdown-link-check"
    echo "Skipping link checking."
fi

# Simple check for TODOs
echo "Checking for remaining TODOs..."
grep -r "TODO" "$DOCS_DIR"
if [ $? -eq 0 ]; then
    echo "Found TODOs in documentation. Please review."
else
    echo "No TODOs found."
fi

echo "Documentation check complete."
