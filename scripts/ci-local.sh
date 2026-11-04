#!/usr/bin/env bash
# ci-local.sh [base] - run the PR workflow's jobs locally, the way CI does.
#
# Reads .github/workflows/prd-toolkit.yml and runs each job's `run:` steps
# (`uses:` steps are skipped; uv and git are already here) from the repo root
# of the checkout this script sits in. Each job's steps run as one bash script
# with `set -e`, so the first failing step fails the job.
#
# CI parity: jobs get a fresh empty HOME (so nothing under the real ~/.claude
# or other dotfiles leaks in) and a clean environment. Only PATH, TMPDIR, LANG,
# UV_CACHE_DIR (default $HOME/.cache/uv) and npm_config_cache (default ~/.npm)
# of the real environment are kept, so runs stay fast.
#
# `${{ github.event.pull_request.base.sha }}` becomes `git merge-base <base> HEAD`;
# <base> defaults to origin/main.
#
# Prints `ci-local: <job> pass|fail` per job; exits 0 only if every job passed.
#
# Environment:
#   CI_LOCAL_WORKFLOW  path of the workflow file (default .github/workflows/prd-toolkit.yml)
#   CI_LOCAL_JOBS      space-separated subset of job names to run (default: all)
set -euo pipefail

root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && git rev-parse --show-toplevel)
cd "$root"

base=${1:-origin/main}
workflow=${CI_LOCAL_WORKFLOW:-$root/.github/workflows/prd-toolkit.yml}
base_sha=$(git merge-base "$base" HEAD)

real_home=$HOME
uv_cache=${UV_CACHE_DIR:-$real_home/.cache/uv}
npm_cache=${npm_config_cache:-$real_home/.npm}

work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
mkdir "$work/home" "$work/jobs"

# One <job>.sh per job, in workflow order; stdout lists the job names.
BASE_SHA=$base_sha OUT_DIR=$work/jobs WORKFLOW=$workflow JOBS=${CI_LOCAL_JOBS:-} \
  uv run --quiet --with pyyaml python -I -c '
import os, yaml
doc = yaml.safe_load(open(os.environ["WORKFLOW"], encoding="utf-8"))
want = os.environ["JOBS"].split()
unknown = [j for j in want if j not in doc["jobs"]]
if unknown:
    raise SystemExit("ci-local: unknown job(s): " + " ".join(unknown))
for name, job in doc["jobs"].items():
    if want and name not in want:
        continue
    runs = [s["run"] for s in job.get("steps", []) if "run" in s]
    text = "\n".join(runs).replace("${{ github.event.pull_request.base.sha }}", os.environ["BASE_SHA"])
    with open(os.path.join(os.environ["OUT_DIR"], name + ".sh"), "w", encoding="utf-8") as f:
        f.write("set -e\n" + text + "\n")
    print(name)
' > "$work/names"

results=()
failed=0
while IFS= read -r job; do
  echo "ci-local: $job running"
  if env -i HOME="$work/home" PATH="$PATH" TMPDIR="${TMPDIR:-/tmp}" LANG="${LANG:-en_US.UTF-8}" \
       UV_CACHE_DIR="$uv_cache" npm_config_cache="$npm_cache" \
       bash "$work/jobs/$job.sh"; then
    results+=("ci-local: $job pass")
  else
    results+=("ci-local: $job fail")
    failed=1
  fi
done < "$work/names"

printf '%s\n' "${results[@]}"
exit "$failed"
