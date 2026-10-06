#!/usr/bin/env bash
# Independent source snapshot + actual HEAD clone inventory. No commit or push.
set -euo pipefail
cd "$(dirname "$0")/.."
repo=$PWD
export PATH="$HOME/.docker/bin:$PATH"
mkdir -p results/phase-6
snapshot=$(mktemp -d "$repo/data/phase-6-validation.XXXXXX")
echo "$snapshot" > results/phase-6/snapshot-location.txt
git clone --no-hardlinks "$repo" "$snapshot/head-clone" > results/phase-6/clone.log 2>&1
git -C "$snapshot/head-clone" rev-parse HEAD > results/phase-6/clone-head.txt
git -C "$snapshot/head-clone" status --porcelain > results/phase-6/clone-status.txt
git -C "$snapshot/head-clone" ls-files > results/phase-6/clone-files.txt
mkdir "$snapshot/source"
tar --exclude='results/phase-6' --exclude='results/phase-6-reproduction.*' \
  --exclude='__pycache__' -cf "$snapshot/source.tar" \
  cpp python scripts docs results assets.json README.md AGENTS.md CLAUDE.md \
  LICENSE .dockerignore .gitignore Dockerfile Dockerfile.phase4 \
  Dockerfile.phase4-pytools Dockerfile.review-fixes Dockerfile.reproduce
tar -xf "$snapshot/source.tar" -C "$snapshot/source"
mkdir -p "$snapshot/source/models" "$snapshot/source/external" \
  "$snapshot/source/data/MOT17" "$snapshot/source/data/MOT20" "$snapshot/source/data/phase-3"
shasum -a 256 "$snapshot/source.tar" > results/phase-6/source-archive-sha256.txt
# Try the standalone root recipe offline; preserve failure, then use smoke path.
if [[ ! -f results/phase-6/root-build-exit.txt ]]; then
  set +e
  docker build --network=none --target build -t vision-lab:phase6-root \
    "$snapshot/source" > results/phase-6/root-build-offline.log 2>&1
  root_status=$?
  set -e
  echo "$root_status" > results/phase-6/root-build-exit.txt
fi
VL_ASSET_ROOT="$repo" bash "$snapshot/source/scripts/reproduce.sh" smoke \
  > results/phase-6/snapshot-driver.log 2>&1
cp -R "$snapshot/source/results/phase-6/." results/phase-6/
cp "$snapshot/source/results/phase-6-reproduction.md" results/phase-6-reproduction.md
cp "$snapshot/source/results/phase-6-reproduction.json" results/phase-6-reproduction.json
echo 'Isolated snapshot smoke finished. HEAD clone and root-build records retained.'
