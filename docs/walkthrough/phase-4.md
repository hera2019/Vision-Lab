# Phase 4 walkthrough — measuring cost fairly

# 第 4 阶段讲解：公平地测量成本

This walkthrough explains the completed controlled FP32/INT8 experiment. Neither INT8 model passed the fixed usefulness criterion. The initial FP32 measurements remain separately archived; the final comparison uses alternating paired runs and full held-out MOT20 evaluation. Independent review remains pending. English paragraphs come first, followed by their Chinese counterparts. FPS, latency, p50/p95, RSS and quantization were introduced in Phase 0; those definitions are not repeated.

本讲解解释已完成的、按固定条件开展的 FP32/INT8 实验。两种 INT8 模型都未通过原定的“值得使用”标准。初次 FP32 测量单独保留，最终比较使用交替执行的配对测量和完整的 MOT20 留出集评估。独立复核仍待进行。每段先英文，再给对应中文。FPS、延迟、p50/p95、RSS 和量化已在阶段 0 介绍，这里不重复定义。

## 1. Why measure again? / 为什么还要重新测速

Phase 3 ran many sequences to check tracking behavior. Some jobs ran together, competing for the same machine. Their elapsed times answer “how long did this accuracy job take?” rather than “how fast is this one pipeline under a specified CPU budget?” Phase 4 gives each measured process a defined budget and runs it alone relative to other experimental inference jobs. Ordinary activity on the host is not disabled. We retain three repeats and their distributions instead of reporting only the fastest result. This makes the speed claim narrower, but much easier to reproduce and assess.

阶段 3 运行多段序列来检查追踪行为，有些任务同时运行、争用同一台机器。因此，耗时回答的是“这项准确性任务跑了多久”，不是“在指定 CPU 预算下，单条流水线有多快”。阶段 4 为每个被测进程设置明确预算，不与其他实验推理任务并行。电脑上的普通活动没有被禁用。我们保留三次重复及其分布，不只报告最快的结果。这样速度结论的适用范围更明确，也更容易复现和判断。

## 2. Excluding startup / 排除启动影响

A **warm-up** runs early frames before recording measured timings. Loading code, allocating tensor buffers and preparing runtime kernels can make early work different from steady operation. We process frames 1–50 but exclude their timings, then record frames 51–150. Tracking still receives all 150 frames, so the measured portion continues a real track history instead of starting a new tracker at frame 51. Each repeat is a fresh process with the same inputs. This measures a warmed pipeline; it does not measure application startup latency or a disk read after clearing all operating-system caches.

**热身（warm-up）**是在记录测速前先处理一批帧。加载代码、分配张量缓冲区、准备运行时计算内核，会使早期运行与稳定运行不同。我们处理第 1–50 帧，但排除其耗时，然后记录第 51–150 帧。追踪器仍收到全部 150 帧，测量部分延续真实的轨迹历史，不是在第 51 帧重新建立追踪器。每次重复使用相同输入，启动一个新进程。这测量的是热身后的流水线，不是应用启动速度，也不是清空所有操作系统缓存后的磁盘读取速度。

## 3. What end-to-end includes / 端到端包含哪些部分

The measured path begins with reading and decoding a JPEG, then performs detector preprocessing, inference, postprocessing, tracker update and output-box filtering. Video rendering and writing track files are excluded. This is the cost of obtaining usable tracking results from image files, not the total cost of a future camera application. We separately time each stage, which tells us whether speeding up the model could materially speed up the whole pipeline. Stage sums can differ slightly from the full path because function-call bookkeeping and allocations also take time. The output document names this boundary explicitly.

被测流程从读取和解码 JPEG 开始，然后执行检测预处理、推理、后处理、追踪更新和输出框过滤。不包括视频绘制和轨迹文件写入。这是从图片文件得到可用追踪结果的成本，不是未来摄像头应用的全部成本。我们还分别记录各阶段耗时，以判断加速模型是否能明显加速整个流程。函数调用的管理开销、分配等也需要时间，所以阶段之和可能与完整流程略有不同。结果文档明确写出这个测量边界。

## 4. Threads versus CPU allowance / 线程与 CPU 额度

A **CPU quota** limits the average processing allowance given to a container. A quota of two is approximately two CPU cores' worth of time, but it does not reserve two particular physical cores. The operating system may move work between cores. We pair quotas 1/2/4 with the same ONNX Runtime thread counts, keep its inter-operation thread count at one and keep OpenCV at one thread. More threads can divide model work, but also add coordination and scheduling costs. We therefore measure all three settings rather than assume four threads are always four times faster. Linux **cgroups** are the resource-control mechanism; the program records the actual quota from `cpu.max` so the report checks what was applied.

**CPU 配额（CPU quota）**限制容器平均可使用的计算额度。额度为二，大致相当于两个核心的处理时间，但并不保留两个指定的物理核心；操作系统可能在核心之间调度任务。我们将 1、2、4 的配额分别配上相同的 ONNX Runtime 线程数，同时让其操作间线程数为一，OpenCV 也用一个线程。更多线程可以分担模型计算，但会增加协调和调度成本。因此三个设置都测，不假设四线程一定快四倍。Linux 的 **cgroups（资源控制组）**负责实施资源限制；程序从 `cpu.max` 记录实际额度，报告据此检查设置是否生效。

## 5. Reading repeated results / 怎样读重复测量

The headline FPS is calculated separately for each repeat from the sum of its 100 measured frame times. We report the median of those three throughputs. It is not the reciprocal of the median frame latency, because those quantities answer different questions. The per-stage p50 and p95 combine the 300 measured observations at one setting. A setting can have acceptable average throughput while still showing occasional long delays. For an interactive product, those slow frames matter. The complete raw CSV files stay available; the human report is a readable summary rather than the only surviving evidence.

先将每次重复中 100 帧的耗时相加，分别计算三次 FPS，再报告这三个吞吐量的中位数。它不是帧延迟中位数的倒数，两种计算回答的问题不同。各阶段的 p50、p95 使用同一设置下合计 300 个被测观测。一个设置的平均吞吐量可能可以接受，但仍偶尔出现较长延迟；交互产品需要关心这些慢帧。完整 CSV 原始记录会保留，人类可读报告只是摘要，不是唯一留下的证据。

The labelled result table is in [the Phase 4 report](../../results/phase-4-performance.md). The >=25 FPS gate was fixed before these measurements. A failed setting remains failed; we do not reduce input resolution or substitute inference-only FPS to cross the line. A passing setting is a throughput result for this platform and measurement boundary, not a guarantee of continuous identities or a commercial readiness verdict.

带完整标签的结果表见[阶段 4 报告](../../results/phase-4-performance.md)。至少 25 FPS 的门槛在测量前已经冻结。失败的设置仍然记录为失败，不通过降低输入分辨率或改用纯推理 FPS 来越过门槛。通过只表示这个平台、这个测量边界下的吞吐量达标，不保证身份始终连续，也不代表商业产品已经就绪。

The following table records the initial FP32-only run, not the denominator for final INT8 speed ratios.

下面的表格记录初次单独执行的 FP32 测量，不用作最终 INT8 加速比的分母。

| Initial FP32 model / 初次模型 | Threads and CPU quota / 线程与配额 | Median repeat FPS / 三次 FPS 中位数 | Peak process RSS MiB / 进程峰值内存 | >=25 FPS / 达标 |
|---|---:|---:|---:|---|
| nano | 1 | 11.43 | 153.33 | No / 否 |
| nano | 2 | 18.47 | 153.71 | No / 否 |
| nano | 4 | 26.34 | 153.79 | Yes / 是 |
| tiny | 1 | 3.14 | 203.87 | No / 否 |
| tiny | 2 | 5.81 | 205.04 | No / 否 |
| tiny | 4 | 10.11 | 205.60 | No / 否 |

The faster model clears the throughput line only with four threads in this experiment, and only narrowly. Tiny's higher tracking scores therefore come with a measured cost on this platform. That does not establish which model is best for a future device or scene; the original identity failures also remain.

较快的模型在本实验中只有四线程越过吞吐量门槛，而且余量不大。tiny 更高的追踪分数在这个平台上有实测成本。这仍不能确定未来设备或场景的最佳模型，原来的身份追踪失败也依然保留。

## 6. Memory and model size / 内存与模型大小

**VmHWM** is the process's highest recorded resident-memory level in Linux. We read it after the run and report the largest value across the three repeats. It includes initialization and warm-up, even though those frames are excluded from latency statistics. A small model file does not imply equally small working memory: activations, input/output buffers, runtime kernels and thread-related allocations also occupy RAM. This number is process memory, not Docker VM memory or all Mac memory. Model file size is reported separately, with a hash proving exactly which file was measured.

**VmHWM** 是 Linux 记录的进程最高常驻内存值。运行后读取它，并报告三次重复中的最大值。它包含初始化和热身，即使这些帧不进入延迟统计。模型文件小，不代表工作内存同样小：中间激活、输入输出缓冲区、运行时内核和线程相关分配也占用内存。这里的数值属于进程，不是 Docker 虚拟机内存或整个 Mac 的内存。模型文件大小单独报告，并用校验值明确测的是哪个文件。

## 7. Measuring the INT8 trade-off / 测量 INT8 的取舍

**Calibration** supplies representative model inputs to estimate numerical ranges before static quantization. Static means those ranges are fixed before ordinary inference. The fixed plan uses MOT17 only, never MOT20. **QDQ** means quantize/dequantize: the derived graph inserts conversions around selected operations while retaining float inputs and outputs. **Convolution (Conv)** applies learned filters to image features; these operations are the planned INT8 portion, while remaining operations retain floating-point precision. Neither a smaller file nor successful model loading proves a useful trade-off. The original criteria require a speed-up of at least 1.3 times and no more than one percentage point of MOT20 MOTA loss under the same evaluator. No thresholds or calibration data may be changed after seeing held-out scores.

**校准（calibration）**是在静态量化前，用有代表性的模型输入估计数值范围。“静态”表示普通推理之前就固定这些范围。固定计划只使用 MOT17，不使用 MOT20。**QDQ** 指量化与反量化：派生计算图在指定操作周围插入转换，但输入输出仍为浮点。**卷积（convolution，Conv）**用学习到的滤镜处理图像特征；计划将这些操作量化为 INT8，其余操作保留浮点精度。文件变小、模型成功加载，都不足以证明取舍值得。原标准要求至少 1.3 倍加速，同时同一评估器下 MOT20 的 MOTA 下降不超过一个百分点。看到留出集分数后，不能再改变门槛或校准数据。

**S8S8** means signed 8-bit integers are used for both learned weights and **activations**, the intermediate feature values computed from an input. **Per-channel** weight quantization gives each output feature channel its own scale instead of forcing all channels to share one. **MinMax** calibration takes the observed minimum and maximum values to set the activation range. These choices were fixed before held-out evaluation; this experiment does not search alternative schemes after seeing MOT20 scores.

**S8S8** 表示学习得到的权重和**激活（activations）**都使用有符号的 8 位整数；激活就是输入经过模型计算后产生的中间特征值。**逐通道（per-channel）**权重量化为每个输出特征通道分别设置缩放比例，而不是让所有通道共享一个。**最小最大值（MinMax）**校准使用观测到的最小值与最大值来确定激活范围。这些选择在留出集评估前就已固定，本实验不会在看到 MOT20 分数后搜索别的方案。

The original quantization import failed because `ml_dtypes` was missing. After the owner approved this download, only the hash-pinned 0.6.0 binary wheel was installed in a separate Python image; the host and other dependency versions were unchanged. Calibration consumes 16 evenly spaced images from each of seven MOT17 sequences, 112 total, without reading their labels. Both derived models load and emit finite native-shaped outputs. These checks allow the experiment to proceed; accuracy still requires scoring the complete held-out set.

原量化模块因缺少 `ml_dtypes` 而导入失败。用户授权这次下载后，只在独立 Python 镜像中安装了固定校验值的 0.6.0 二进制安装包，主机和其他依赖版本没有改变。校准从七段 MOT17 序列各取 16 张均匀间隔的图片，共 112 张，不读取它们的标签。两种派生模型都能加载，并输出形状正确、数值有限的结果。这些检查允许继续实验；准确率仍需完整评估留出集。

The first calibration attempt failed because ORT 1.30 cleared its intermediate observations at the chosen buffer cap without merging their ranges. We preserved that failure and increased only the storage cap to 128, above the fixed 112 observations. The reader asserts that all 112 samples were consumed. Calibration images, scheme, thresholds and the 6 GiB memory limit remain fixed. This matters because quietly dropping observations could create a different experiment while appearing to be a memory optimization.

第一次校准因 ORT 1.30 在到达设定的缓冲上限后清空中间观测、却没有合并数值范围而失败。失败记录保留，只将存储上限改为 128，高于固定的 112 个观测，并检查读取器确实使用全部 112 张图片。校准图片、方案、门槛和 6 GiB 内存限制保持不变。这一点很重要：悄悄丢弃观测，可能表面上只是节省内存，实际却改变了实验。

## 8. Paired speed results / 配对速度结果

All 36 paired runs are complete. Compare each INT8 setting to its FP32 setting from the same matrix, not to the earlier independent run. The speed ratio divides the median of three INT8 repeat throughputs by the corresponding FP32 median. Every stage retains its own mean/p50/p95 in the result files. The table shows why we must measure rather than assume that lower precision always helps.

36 次配对运行全部完成。每个 INT8 设置都与同一矩阵里的 FP32 设置比较，不与较早的独立运行比较。加速比是三次 INT8 吞吐量的中位数，除以对应 FP32 的中位数。每个阶段自己的平均值、p50 和 p95 保存在结果文件中。表格说明了为什么必须实测，而不能假设低精度总能加速。

| Model / 模型 | Threads / 线程 | FP32 FPS | INT8 FPS | Speed ratio / 加速比 |
|---|---:|---:|---:|---:|
| nano | 1 | 11.61 | 15.28 | 1.32× |
| nano | 2 | 19.09 | 20.56 | 1.08× |
| nano | 4 | 27.34 | 25.46 | 0.93× |
| tiny | 1 | 3.18 | 7.81 | 2.46× |
| tiny | 2 | 5.66 | 13.00 | 2.30× |
| tiny | 4 | 9.76 | 18.25 | 1.87× |

Nano's four-thread INT8 pipeline is slightly slower than FP32 here. Tiny speeds up at all three budgets but still misses 25 FPS. Model files shrink from 3.48 to 1.33 MiB for nano and from 19.23 to 5.18 MiB for tiny, while four-thread peak process RSS rises from 153.9 to 201.4 MiB and from 205.7 to 221.4 MiB respectively. Runtime data structures, kernels and quantization conversions can offset file-size savings. File size, working memory and latency are different measurements; none substitutes for the others. Speed observations alone do not establish the quality gate; the complete MOT20 score follows below.

nano 的四线程 INT8 流水线在这里比 FP32 略慢。tiny 在三个预算下都加速，但仍未达到 25 FPS。nano 模型文件从 3.48 缩小到 1.33 MiB，tiny 从 19.23 缩小到 5.18 MiB；四线程进程峰值内存却分别从 153.9 增加到 201.4 MiB、从 205.7 增加到 221.4 MiB。运行时的数据结构、计算内核和量化转换可能抵消文件大小的节省。文件大小、工作内存和延迟是不同的测量，不能互相代替。仅凭这些速度观察不能确定准确率门槛，完整的 MOT20 分数如下。

## 9. Held-out quality and the failed gate / 留出集质量与失败判定

Each INT8 model processed all four MOT20 sequences, 8,931 frames, with the original tracker and A1 settings. We used the same motmetrics procedure as the accepted FP32 baseline; TrackEval results are separately labelled in the full report. Differences below are INT8 minus FP32 in percentage points. Nano fails severely, and tiny fails narrowly: its MOTA loss is 1.0635335 points, greater than the fixed one-point limit. We compare the unrounded value, so rounding cannot turn the failure into a pass. No tested INT8 budget satisfies both required conditions. Completing the experiment is different from accepting a model.

每种 INT8 模型都用原追踪器和 A1 设置处理完整的四段 MOT20 序列，共 8,931 帧。我们使用与已验收 FP32 基线相同的 motmetrics 流程，TrackEval 的结果在完整报告中单独标注。下表差值为 INT8 减 FP32，单位是百分点。nano 严重失败，tiny 则略超门槛：MOTA 下降 1.0635335 个百分点，大于固定的一个百分点上限。判断使用未取整的值，不能靠四舍五入将失败变成通过。没有一个被测 INT8 预算同时满足两个条件。实验完成与模型被接受是两回事。

| Model / 模型 | FP32 MOTA | INT8 MOTA | ΔMOTA pp / 差值 | FP32 IDF1 | INT8 IDF1 | ΔIDF1 pp / 差值 |
|---|---:|---:|---:|---:|---:|---:|
| nano | 56.0207 | -0.0795 | -56.1002 | 51.3699 | 1.3235 | -50.0464 |
| tiny | 61.0752 | 60.0117 | -1.0635 | 59.4906 | 57.9299 | -1.5608 |

The [read-only diagnosis](../../results/phase-4-int8-diagnostic.md) checked MOT17-02 frames 1/51/150, not new held-out inputs. Reconstructing the C++ preprocessing formula agrees with the official calibration helper within 4.77e-7. Original and preprocessed FP32 raw outputs are identical on these images. Nano INT8 produces many more boxes after NMS, and disabling runtime optimization does not restore the original outputs/counts. The evidence points to the INT8 computation path on this slice, but does not prove a specific operator or general cause. We retained the failed models and scores; no alternative quantization search or MOT20 recalibration followed. Finite tensors and successful loading were only smoke checks, not proof of accuracy. The existing FP32 baseline remains in use, and the original occlusion/identity failures remain unresolved.

[只读诊断](../../results/phase-4-int8-diagnostic.md)检查的是 MOT17-02 第 1、51、150 帧，没有使用新的留出集输入。独立重建的 C++ 预处理公式与官方校准辅助函数相差不超过 4.77e-7；原始与预处理后的 FP32 在这些图片上的原始输出完全相同。nano INT8 在 NMS 后产生多得多的框，禁用运行时优化也没有恢复原来的输出与数量。证据指向这个片段上的 INT8 计算路径，但不能证明具体是哪一个操作或普遍原因。失败模型和分数均保留，没有接着搜索其他量化方案或用 MOT20 重新校准。数值有限、能够加载只是基本运行检查，不是准确率证明。现有 FP32 基线继续保留，原来的遮挡与身份切换问题仍未解决。

## 10. Runtime isolation / 运行时隔离

Every test uses the same hardened wrapper: no runtime network, ordinary user, no Linux capabilities or privilege escalation, read-only system/project, and only explicitly selected output directories writable. CPU budgets, 6 GiB memory and 512-process limits constrain resource use. A 1 GiB temporary filesystem rejects direct execution and device/set-user-ID behavior; interpreters can still read scripts, so this is not a ban on all computation. There is no Docker socket or whole-home mount. Actual write, routing, connection, identity and resource checks are saved in [the safety report](../../results/phase-4/container-safety.md). Approved dependency builds use a separate network-enabled build step. These controls limit access; they are not an absolute guarantee against every vulnerability.

每项测试使用同一个加固的运行入口：运行时没有网络，使用普通用户，撤销 Linux 额外权限并禁止提升权限，系统和项目只读，只有明确列出的输出目录可写。CPU 配额、6 GiB 内存和 512 个进程的限制约束资源使用。1 GiB 的临时文件系统拒绝直接执行文件、设备和设置用户身份的行为；解释器仍可以读取脚本，因此这不代表禁止一切计算。没有挂载 Docker 控制接口或整个个人目录。实际的写入、路由、连接、身份和资源检查保存在[安全报告](../../results/phase-4/container-safety.md)。经授权的依赖构建是单独的联网步骤。这些控制限制访问，但不是对所有漏洞的绝对保证。

## 11. A separate post-hoc diagnosis / 单独的后验诊断

Opus pointed out that our first diagnosis used three MOT17 frames, although the
large quality failure happened on MOT20. We now inspect a fixed small set of
frames from both datasets. On MOT20 the original INT8 model loses many
high-confidence boxes. The same MOT17 diagnostic frames already show a coarse
0.7163 step in the first feature layer: every observed negative floating
activation rounds to zero. Being outside the representable window is different
from saturation, which means a rounded integer exceeds its allowed bounds.
The actual saturation rate there is negligible. These observations point to
loss of numerical resolution, rather than proving that a new scene alone
exceeded calibration ranges. The detailed tables retain that distinction.

Opus 指出：第一次诊断只看了三张 MOT17 图，但严重质量失败发生在 MOT20。
现在我们检查两套数据中预先固定的少量图片。在 MOT20 上，原 INT8 模型丢失了
大量高置信度框。同一组 MOT17 诊断图已经显示：第一层特征的量化步长粗达
0.7163，所有观测到的浮点负激活都被取整为零。“超出可表示范围”和“饱和”不同，
饱和是取整后的整数超出了允许上下限；这里的实际饱和率很低。这些现象指向数值
分辨率损失，并不能证明仅仅是新场景超出了校准范围。详细表格保留了这种区别。

Two fixed mixed-precision candidates keep either the prediction head (which
produces boxes and confidence), or the head and feature pyramid (which combines
features at several scales), floating. Both fail complete MOT17 development
evaluation. A conditional diagnostic control keeps the original INT8 weights
but every activation and bias (a learned additive offset) floating; it uses floating convolution computation.
It reaches MOT17 MOTA 69.1755, only 0.0570 points below the floating baseline,
and its identity score falls by 0.4315 points. This supports the activation/
bias quantization path as a major source of the original collapse; the control
restores both, so their effects are not separately isolated. It does not identify
one causal layer and does not establish an accelerated INT8 solution. The
control's model hash is fixed before one MOT20 evaluation and paired speed test;
[the separate report](../../results/phase-4-nano-repair.md) records their outcome.
Original failed models, scores and limits stay unchanged.

两个固定的混合精度方案分别保留检测头（产生框和置信度）浮点，或保留检测头与
特征金字塔（组合多个尺度的特征）浮点，
但都没通过完整的 MOT17 开发集验证。有条件的诊断对照保留原 INT8 权重，
让全部激活和偏置（学习得到的加法偏移量）保持浮点，卷积仍以浮点计算。
它在 MOT17 上达到 MOTA 69.1755，
仅比浮点基线低 0.0570 个百分点，身份一致性分数低 0.4315 个百分点。
这支持“激活／偏置量化路径是原始崩溃的重要来源”的判断；对照同时恢复了两者，
没有单独隔离各自的影响。它没有锁定某一层，也没有证明
INT8 加速方案合格。对照模型的摘要在单次 MOT20 评估与配对测速之前固定；
[单独报告](../../results/phase-4-nano-repair.md)记录这些测试的结果。
原来失败的模型、分数和门槛保持不变。

The single MOT20 run reaches MOTA 55.3158, a loss of 0.7049 percentage points,
inside the original quality cap. Paired speed ratios at 1/2/4 threads are
1.030/0.995/0.969x, all below the required 1.3x. Recovering quality is useful
diagnostic evidence, but this floating control does not solve INT8 acceleration.
The original FP32 baseline remains the accepted comparison.

单次 MOT20 测量达到 MOTA 55.3158，损失 0.7049 个百分点，落在原质量限值内。
一／二／四线程的配对速度比为 1.030／0.995／0.969 倍，都低于要求的 1.3 倍。
质量恢复提供了有用的诊断证据，但这个浮点对照没有解决 INT8 加速问题。
原 FP32 基线仍是已接受的比较对象。

## New terms / 新术语

| Term | 中文 | Meaning / 含义 |
|---|---|---|
| Warm-up | 热身 | Early processing before measured observations / 正式测量前的早期处理 |
| CPU quota | CPU 配额 | Average processing allowance, not core reservation / 平均计算额度，不是保留指定核心 |
| cgroups | 资源控制组 | Linux mechanism enforcing process/container resource limits / Linux 实施进程、容器资源限制的机制 |
| VmHWM | 内存高水位 | Highest recorded resident memory of the process / 进程曾达到的最高常驻内存 |
| Calibration | 校准 | Inputs used to estimate quantization ranges / 用输入估计量化数值范围 |
| QDQ | 量化与反量化 | Graph conversions surrounding selected low-precision operations / 指定低精度操作周围的计算图转换 |
| Convolution (Conv) | 卷积 | Learned filters applied to feature values / 将学习得到的滤镜作用于特征值 |
| Activation | 激活 | Intermediate feature value computed from an input / 输入经过模型计算产生的中间特征值 |
| S8S8 | 有符号 8 位权重与激活 | Signed INT8 representation for both quantities / 两者都使用有符号 INT8 表示 |
| Per-channel | 逐通道 | Separate weight scaling for each output feature channel / 每个输出特征通道分别缩放权重 |
| MinMax | 最小最大值 | Calibration using observed extrema / 使用观测到的极值进行校准 |
| Saturation | 饱和 | Rounded quantized integer would exceed its bounds and must be clamped / 取整后的量化整数超出上下限，需要截断 |
| Weight-only storage | 仅权重低精度存储 | Store weights as INT8, then restore float values for floating computation / 权重以 INT8 存储，恢复浮点值后进行浮点计算 |
| Feature pyramid | 特征金字塔 | Combines image features at different resolutions / 组合不同分辨率的图像特征 |
| Bias | 偏置 | Learned additive offset / 学习得到的加法偏移量 |
