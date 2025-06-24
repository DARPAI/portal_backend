#!/bin/bash

set -euo pipefail

echo "🔍 Checking for duplicate down_revision values in Alembic migrations..."

extract_down_revision_lines() {
  grep -h down_revision alembic/versions/*.py
}

parse_down_revision_values() {
  grep -v '=\s*None$' | \
  awk -F"=" '{ gsub(/^[ \t]+|[ \t]+$/, "", $2); print $2 }' | \
  sed -E "s/^['\"](.*)['\"]$/\1/"
}

find_duplicates() {
  sort | uniq -d
}

duplicates=$(extract_down_revision_lines | parse_down_revision_values | find_duplicates)

if [ -n "$duplicates" ]; then
  echo "❌ Found duplicate down_revision(s):"
  echo "$duplicates"
  exit 1
fi

echo "✅ No duplicate down_revision values found."