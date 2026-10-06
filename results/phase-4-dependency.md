# Phase 4 INT8 dependency boundary

**Update:** owner approved the download on 2026-10-06 and requested continued
experiments. The separate image build succeeded; ml_dtypes 0.6.0 import and
ORT quantization import pass. Build log: `phase-4/dependency-build.log`.
The initial unapproved boundary record is preserved in
`phase-4-dependency-initial.md` / `.json`; the text below describes that
initial state, not the current installation status.

Date: 2026-10-06. Author: Codex / GPT-6 (exact runtime model ID not exposed).

**Observed:** importing the already installed ONNX Runtime 1.30 quantization
module fails with `ModuleNotFoundError: No module named 'ml_dtypes'`.
The installed `quant_utils.py` imports `float8_e4m3fn`, `int4`, and `uint4`
at module load time, even though this experiment will use INT8.
Inspection saved in `phase-4/quantization-dependency-inspection.txt`.
No matching wheel was found in the checked local pip caches.

**Concrete proposal, not executed:** install only pinned `ml_dtypes==0.6.0`
in a separate `vision-lab:phase4-pytools` image derived from the existing
Python image. `--no-deps` preserves NumPy and all existing packages;
`--only-binary` avoids a new compiler/build toolchain. Require SHA-256 hashes
for the published CPython 3.12 Linux ARM64/x86-64 wheels.

The [published ARM64 wheel](https://pypi.org/project/ml-dtypes/0.6.0/#files)
is 360.2 kB; x86-64 is 409.9 kB. Source license Apache-2.0; bundled Eigen
license MPL-2.0, as described by the [maintainers](https://github.com/jax-ml/ml_dtypes#license).
No account, payment, model download, video upload or host installation.
Network is needed only for the container build/download; runs stay offline.

`Dockerfile.phase4-pytools` and `python/requirements-phase4.txt` make the
proposal reviewable. No build or download of this dependency has been run.
FP32 benchmark work can continue independently. Project download boundaries
require owner approval before adding an unlisted dependency.
