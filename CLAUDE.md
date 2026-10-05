# Vision Lab

Work plan and phases: [docs/PLAN.md](docs/PLAN.md).

- All public-facing content (README, docs, reports, commit messages) is in English; conversation with the owner can be in Chinese.
- Follow the AI-Lab method: test plan before downloads, results as `.md` + `.json`, keep negative results, never call an unexecuted command verified.
- Model weights, datasets and videos stay out of git (see `.gitignore`); record source, revision, SHA-256 and license for each.
- Inference code is C++ (ONNX Runtime) and runs inside the Linux Docker container, CPU only. Python is for export and evaluation.
- Docker CLI lives at `~/.docker/bin` (added in `~/.zprofile`); non-login shells may need `export PATH="$HOME/.docker/bin:$PATH"`.
