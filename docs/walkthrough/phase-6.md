# Phase 6 walkthrough — reproducing the evidence

# 第 6 阶段讲解：复现证据

Phase 6 adds a readable project entry point, input checks and a one-command
driver. Its acceptance is still partial. Local source validation, installing
dependencies and reproducing a complete committed project are separate
checks. The current state is recorded in [the reproduction report](../../results/phase-6-reproduction.md).
Earlier failures, tracking settings and results stay intact.

阶段 6 增加清楚的项目入口、输入检查和一键执行程序。它仍属于部分验收。本地源码
验证、安装依赖和复现完整的已提交项目，是不同的检查。当前状态见
[复现报告](../../results/phase-6-reproduction.md)。之前的失败、追踪设置和结果均保留。

## 1. The source you have versus the source you can clone / 手上的源码与能克隆到的源码

A **fresh clone** is a separate checkout created from Git history. It includes
committed files and does not automatically inherit local edits or untracked
files. Here, actual HEAD is `6f0e68f`, containing Phases 0–2. An inspected
clone is clean but lacks the new tracker, benchmark and reproduction entry
point. A **source snapshot** is an archive of the current working files; it
can include those unfinished edits, but is not a fresh clone. We tested a
separate snapshot without overlaying the actual clone. This distinction
prevents a local success from hiding missing distributed source.

**干净克隆（fresh clone）**是从 Git 历史建立的独立检出，包含已提交的文件，不会
自动继承本地修改或未跟踪文件。这里实际的 HEAD 是 `6f0e68f`，包含阶段 0–2。
检查过的克隆虽然干净，却没有新增追踪器、测速程序和复现入口。**源码快照
（source snapshot）**是当前工作文件的归档，可以包含这些尚未提交的修改，但不是
干净克隆。我们测试的是独立快照，没有将它覆盖到真实克隆中。这个区别避免本地成功
掩盖对外提供的源码不完整。

## 2. Inputs need identities too / 输入也需要明确身份

A **preflight** checks prerequisites before expensive work. It verifies both
original ONNX model hashes, pinned external revisions and unchanged tracked
external files, dataset sequence/image counts, GT hashes and a representative
image hash. It records exactly what was checked. It does not checksum every
JPEG. The large inputs are shared through explicit read-only submounts during
snapshot validation; only new outputs are writable. This avoids copying the
datasets or granting access to the whole personal directory. Inputs remain
licensed research data, with provenance in assets.json.

**预检查（preflight）**是在昂贵工作之前检查前提条件。它核对两种原始 ONNX 模型的
校验值、外部代码固定版本及其已跟踪文件未修改、数据集序列与图片数量、人工标注
文件校验值，以及一张代表图片的校验值，并明确记录检查范围。它没有逐张校验所有
JPEG。快照验证通过明确的只读子挂载共享大输入，只有新输出可写，因此不用复制
数据集，也不用开放整个个人目录。输入仍遵守研究数据许可，来源记录在 assets.json。

## 3. Rebuilding source is not the same as reinstalling dependencies / 重建源码与重装依赖不同

A **dependency cache** stores previously completed installation/build layers.
The first standalone root build ran with no network and failed because a
required apt layer was not cached. That failure remains. Rebuilding C++ on
the already installed local toolchain is another route and was tested
separately. Initial temporary-path and read-only mountpoint failures were
corrected by using an independent directory under the already shared project
and creating empty mount destinations, without changing Docker settings or
weakening protections. The standalone online-build outcome is recorded in the
report; it does not automatically establish a fresh Python dependency build
or a successful clean-clone experiment.

**依赖缓存（dependency cache）**保存之前完成的安装或构建层。第一次独立根镜像
构建禁止网络，因为所需 apt 安装层没有缓存而失败，这一失败仍保留。用已经安装好的
本地工具链重新构建 C++ 是另一条路线，已单独测试。最初的临时目录和只读挂载点失败，
通过改用已共享项目下的独立目录、建立空的挂载目标解决，没有修改 Docker 设置或
放宽保护。独立联网构建的实际结果记录在报告中；它不会自动证明新的 Python 依赖
安装成功，更不会自动证明完整的干净克隆实验通过。

The Ubuntu base image and ORT release are digest/checksum pinned. Python
package versions are specified, but apt versions and Python **transitive
dependencies**, packages installed because another package needs them, are
not completely locked. Future builds can therefore differ. We document this
limit and record actual versions instead of calling the environment bitwise
reproducible. A fully locked dependency distribution would be separate work.

Ubuntu 基础镜像和 ORT 发布包固定了摘要或校验值。Python 包指定了版本，但 apt
版本和 Python 的**传递依赖（transitive dependencies）**没有完全锁定；传递依赖
就是因为某个包需要它们而安装的其他包。所以未来构建可能不同。我们明确这一限制，
记录实际版本，而不声称环境可以逐字节复现。完整锁定依赖发行版属于另外的工作。

## 4. What the bounded check says / 有限检查说明什么

The source snapshot rebuilt current C++ and ran the first 50 MOT17-02 frames
for both FP32 models. Detection and tracking outputs are byte-identical to
the frozen slices. Fresh Python/C++ synthetic behavior also agrees under the
original fixture rule. The four-thread benchmark uses the same input,
warm-up, measured frames and three repeats as Phase 4. Nano's median is
27.215 FPS inside the old 26.425–27.816 interval. Tiny's median is 10.131 FPS,
outside its old 9.740–9.896 interval. Faster throughput does not pass this
strict repeat-interval consistency test. We retain that failure rather than
changing the interval or replacing it with a more favorable earlier run.

源码快照重新构建当前 C++，两种 FP32 模型都处理 MOT17-02 的前 50 帧。检测与追踪
输出和冻结片段逐字节相同，新运行的 Python/C++ 合成行为检查也满足原来的规则。
四线程测速沿用阶段 4 的输入、热身、被测帧和三次重复。nano 中位数为 27.215 FPS，
位于原来的 26.425–27.816 范围内；tiny 为 10.131 FPS，超出原来的 9.740–9.896
范围。即使更快，也没有通过这个严格的重复区间一致性检查。我们保留失败，不改变
区间，也不换用另一次更有利的旧测量。

## 5. Two commands, two claims / 两种模式，两种结论

`bash scripts/reproduce.sh smoke` is the bounded local check and needs the
installed images and frozen inputs described in README. Full mode builds
the original recipes and runs the full original stages in an explicitly
disposable, clean checkout; the optional mean-shift experiment remains
deferred. Full mode is prepared and syntax-checked, not executed or accepted
by the snapshot test. Numerical checks and proof of fresh-clone context are
reported separately. No subset test replaces the full INT8/quality/budget
matrix. The project rule requires the owner to request a commit before Git
history can include the complete source. No commit or push was performed.

`bash scripts/reproduce.sh smoke` 是有限的本地检查，需要 README 中说明的已安装
镜像和冻结输入。完整模式在明确可丢弃的干净检出中构建原配方、运行原来的完整阶段，
可选 mean-shift 实验仍推迟。完整模式已准备并检查语法，但没有因为快照检查就被
执行或验收。数值检查与干净克隆环境的证明分别报告，子集测试不能代替完整的 INT8、
质量和 CPU 预算矩阵。项目规则要求用户明确要求提交，Git 历史才能包含完整源码。
本轮没有提交或推送。

## New terms / 新术语

| Term | 中文 | Meaning / 含义 |
|---|---|---|
| Fresh clone | 干净克隆 | Independent checkout of committed Git history / 已提交 Git 历史的独立检出 |
| Source snapshot | 源码快照 | Archive of current working files, including local changes / 当前工作文件的归档，可包含本地修改 |
| Preflight | 预检查 | Checks prerequisites before running / 运行前检查前提条件 |
| Dependency cache | 依赖缓存 | Previously completed build/install layers / 之前完成的构建或安装层 |
| Transitive dependency | 传递依赖 | Package required by another package / 其他包所需要的包 |
