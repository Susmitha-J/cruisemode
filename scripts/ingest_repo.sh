#!/bin/bash
# CruiseMode — Custom Git Repository Ingestion Tool
# Usage: ./scripts/ingest_repo.sh <github-repo-url> <path-to-requirements-md> [branch]

set -e

REPO_URL=$1
REQ_FILE=$2
BRANCH=${3:-main}

if [ -z "$REPO_URL" ] || [ -z "$REQ_FILE" ]; then
    echo "Usage: $0 <github-repo-url> <path-to-requirements-md> [branch]"
    exit 1
fi

echo "===================================================="
echo "🔌 CruiseMode Custom Repository Ingester Starting"
echo "===================================================="

# 1. Clean previous state
echo "🧹 Cleaning sample_app/ and temporary sandbox..."
rm -rf sample_app
rm -rf .sandbox
rm -rf generated_tests
mkdir -p sample_app

# 2. Clone custom repository
echo "📥 Cloning $REPO_URL (branch: $BRANCH) into sample_app/..."
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" sample_app/

# Remove cloned repo's inner git history to avoid submodules confusion
rm -rf sample_app/.git

# 3. Copy custom requirements
echo "📄 Copying requirements $REQ_FILE into inputs/acceptance_criteria.md..."
mkdir -p inputs
cp "$REQ_FILE" inputs/acceptance_criteria.md

# 4. Generate mock/scaffolded scan reports tailored to the new codebase
# In production, these reports are uploaded by SonarQube, DependencyCheck, and OWASP scanners
echo "🔍 Initializing mock security scan reports for the new repository..."
cat <<EOF > inputs/owasp_scan_report.json
{
  "project": "Custom Ingested Repo",
  "scanned_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "findings": [
    {
      "id": "SEC-001",
      "severity": "CRITICAL",
      "type": "PII_LEAK",
      "message": "Potential PII leak: Logging credentials or card details detected in source code.",
      "file": "sample_app/app.py",
      "line": 45,
      "auto_patchable": true
    }
  ]
}
EOF

cat <<EOF > inputs/clean_code_report.json
{
  "project": "Custom Ingested Repo",
  "findings": [
    {
      "id": "CC-001",
      "severity": "WARNING",
      "type": "BROAD_EXCEPTION",
      "message": "Do not catch broad Exception objects directly. Catch specific targets.",
      "file": "sample_app/refund_service.py",
      "line": 80,
      "auto_patchable": true
    }
  ]
}
EOF

# Copy dummy SonarQube & OSS reports
cat <<EOF > inputs/sonarqube_report.json
{ "project": "Custom Ingested Repo", "findings": [] }
EOF

cat <<EOF > inputs/oss_scan_report.json
{
  "project": "Custom Ingested Repo",
  "findings": [
    {
      "id": "OSS-001",
      "package": "pyjwt",
      "current_version": "2.3.0",
      "severity": "CRITICAL",
      "cve": "CVE-2022-29217",
      "recommended_action": "Upgrade pyjwt to version 2.4.0 or higher.",
      "auto_patchable": false
    }
  ]
}
EOF

echo "✅ Custom repository successfully ingested."
echo "🚀 Triggering CruiseMode Multi-Agent Validation..."
python3 -m src.main
echo "===================================================="
echo "🎉 Validation Complete! Refresh your Streamlit dashboard."
echo "===================================================="
