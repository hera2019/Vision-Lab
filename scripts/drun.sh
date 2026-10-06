#!/usr/bin/env bash
# Hardened `docker run` for every step in this repository.
#
#   scripts/drun.sh <image> [docker run options...] -- <command...>
#
# - The repository is mounted read-only at /work. Only the directories in
#   VL_RW (space-separated, relative to the repo root; default "results") are
#   writable, each must already exist.
# - No network, non-root user (the caller's uid/gid), all Linux capabilities
#   dropped, no privilege escalation, read-only root filesystem with a tmpfs
#   /tmp, and process / memory caps.
# Builds (`docker build`) still need the network; runs never do.
set -euo pipefail

image=$1; shift
extra=()
while [[ $# -gt 0 && $1 != "--" ]]; do extra+=("$1"); shift; done
[[ ${1:-} == "--" ]] && shift

repo=$(cd "$(dirname "$0")/.." && pwd)
mounts=(-v "$repo:/work:ro")
for dir in ${VL_RW:-results}; do
  [[ -d "$repo/$dir" ]] || { echo "drun: $dir does not exist" >&2; exit 2; }
  mounts+=(-v "$repo/$dir:/work/$dir")
done

exec docker run --rm \
  --network none \
  --user "$(id -u):$(id -g)" \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --read-only --tmpfs /tmp:rw,size=1g \
  --pids-limit 512 \
  --memory "${VL_MEMORY:-6g}" \
  -e HOME=/tmp \
  "${mounts[@]}" ${extra[@]+"${extra[@]}"} "$image" "$@"
