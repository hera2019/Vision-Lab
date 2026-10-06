#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
docker build --target build -t vision-lab:dev .
docker build --target pytools -t vision-lab:pytools .
mkdir -p results/phase-3
scripts/drun.sh vision-lab:dev -- /src/build/env_check > results/phase-3/environment.txt
docker image inspect vision-lab:dev vision-lab:pytools \
  --format '{{json .RepoTags}} {{.Id}} {{.Architecture}} {{.Os}}' > results/phase-3/image-versions.txt
scripts/drun.sh vision-lab:pytools -- pip freeze --all > results/phase-3/python-environment.txt
