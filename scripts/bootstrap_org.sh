#!/usr/bin/env bash
# Create the repo in the org and invite the team.
#
# Prerequisites:
#   1. Org already created: https://github.com/meridian-finance-ai
#   2. gh auth login   (choose HTTPS, and grant the admin:org scope)
#
# Then, from the repo root:
#   ORG=meridian-finance-ai ./scripts/bootstrap_org.sh
set -euo pipefail

ORG="${ORG:-meridian-finance-ai}"
REPO="${REPO:-profitability-agent}"
VISIBILITY="${VISIBILITY:-public}"

COLLABORATORS=(
  skotipalli
  svijetaj
  sameer59-saks
  santhoshhugar
)

echo "==> verifying handles"
for u in "${COLLABORATORS[@]}"; do
  gh api "users/$u" --jq .login >/dev/null 2>&1 \
    && echo "    ok   $u" \
    || echo "    !!   $u does not resolve - check the handle before inviting"
done

echo "==> creating $ORG/$REPO ($VISIBILITY)"
gh repo create "$ORG/$REPO" --"$VISIBILITY" --disable-wiki \
  --description "Manufacturing profitability agent - Meridian Corp Finance & Analytics task force"

git init -b main
git add .
git commit -m "Scaffold: scope, synthetic data generator, workstreams, eval harness"
git remote add origin "https://github.com/$ORG/$REPO.git"
git push -u origin main

echo "==> creating the taskforce team"
gh api "orgs/$ORG/teams" -f name="taskforce" -f privacy="closed" >/dev/null || true
gh api -X PUT "orgs/$ORG/teams/taskforce/repos/$ORG/$REPO" -f permission="push" >/dev/null

echo "==> inviting collaborators"
for u in "${COLLABORATORS[@]}"; do
  echo "    $u"
  gh api -X PUT "orgs/$ORG/teams/taskforce/memberships/$u" -f role="member" >/dev/null \
    || echo "    ! could not invite $u - add manually"
done

echo "==> branch protection on main"
gh api -X PUT "repos/$ORG/$REPO/branches/main/protection" \
  -H "Accept: application/vnd.github+json" \
  --input - <<'JSON' >/dev/null || echo "    ! protection not applied - fine to skip for a weekend build"
{
  "required_status_checks": {"strict": false, "contexts": ["smoke"]},
  "enforce_admins": false,
  "required_pull_request_reviews": {"required_approving_review_count": 1},
  "restrictions": null,
  "allow_force_pushes": false
}
JSON

echo
echo "done -> https://github.com/$ORG/$REPO"
echo "add later joiners with:"
echo "  gh api -X PUT orgs/$ORG/teams/taskforce/memberships/<handle> -f role=member"
