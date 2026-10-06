# Phase 3 walkthrough — connecting detections into identities

# 第 3 阶段讲解：把检测框连成持续的身份

English first, then Chinese. Terms already introduced in phases 0–2 are not defined again. Complete measurement tables: [phase report](../../results/phase-3-tracking.md).

先英文后中文。阶段 0–2 介绍过的术语不再重复定义。完整测量表见[阶段报告](../../results/phase-3-tracking.md)。

## 1. What changed / 增加了什么

Phase 2 answers “where are the people in this picture?” Running that detector on a video produces separate lists of boxes. It cannot tell us which box belongs to the same person across pictures. Phase 3 adds a **track ID**, a number the tracker tries to keep attached to one person over time. If a person is marked 3, disappears briefly and returns, the useful outcome is still 3. The model itself has not learned a new task: the tracker links its existing detections. We ported the official Python tracking procedure to C++, so image preparation, model inference and tracking can run in one C++ process.

阶段 2 回答的是“这张图里的人在哪里？”把检测器逐帧运行，会得到一份份独立的框列表，但不知道前后两个框是不是同一个人。阶段 3 增加了 **track ID（追踪编号）**：追踪器尽量让同一个人在不同帧里保持同一个数字。如果一个人编号为 3，短暂消失后回来，理想结果仍是 3。模型本身没有学习新任务，而是追踪器把已有检测连起来。我们将官方 Python 追踪流程移植到 C++，使图片准备、模型推理和追踪可以在同一个 C++ 进程运行。

## 2. Predict, then match / 先预测，再匹配

A **Kalman filter** estimates motion from previous observations and predicts where a box should be next. It keeps both the estimate and its uncertainty. When a new detection is matched, the observation corrects the prediction. This is a mathematical motion model, not recognition of clothes or faces. Our reference models position, size and velocity in image coordinates. A walking person and a moving camera can both change those coordinates; this tracking path does not compensate for camera motion.

**卡尔曼滤波器（Kalman filter）**根据之前的观测估计运动，预测下一帧的框，并同时保存估计值和不确定性。匹配到新的检测后，用观测修正预测。这是数学运动模型，不会识别衣服或人脸。参照实现用画面坐标表示位置、大小和速度。人行走、镜头移动都可能改变这些坐标；当前追踪流程没有补偿镜头运动。

There may be many tracks and many detections. **Linear assignment** chooses pairs that minimize the total cost while allowing unmatched objects. Our cost uses overlap between predicted and detected boxes. **Score fusion** also uses detector confidence: a weak detection is less attractive even with the same overlap. The exact overlap geometry and assignment limits must match Python. A small numerical difference can change a pair, and that change can affect hundreds of later frames.

轨迹和检测都可能有很多个。**线性分配（linear assignment）**选择使总代价最小的配对，也允许某些对象不配对。这里的代价依据预测框和检测框的重叠程度。**分数融合（score fusion）**还加入检测置信度：即使重叠相同，较弱的检测也较不容易被选中。重叠的计算方式和分配门槛必须与 Python 一致。很小的数值差异就可能改变一次配对，而这次改变可能影响后续几百帧。

## 3. Why use weak detections? / 为什么保留较弱的检测

ByteTrack first matches high-confidence detections. It then lets unmatched currently tracked people use lower-confidence detections. A partly hidden person may produce a weak box that is still useful for maintaining an existing identity. This second pass does not freely create new identities from weak boxes. Newly created tracks must meet a higher threshold and, except on the first update, be confirmed in a later frame. An unmatched confirmed track becomes lost and remains eligible for recovery for a fixed number of updates; after expiry it is removed.

ByteTrack 先匹配高置信度检测，再让尚未匹配的、当前仍在追踪的人使用较低置信度检测。部分遮挡的人可能只产生一个较弱的框，但仍有助于保持已有编号。第二轮不会随便从弱检测建立新编号。新轨迹必须达到更高门槛，而且除第一次更新外，需要在后续帧确认。已确认轨迹没有匹配时，转为失踪状态，在固定更新次数内仍可找回；超时后移除。

Longer retention gives a returning detection more opportunity to recover its old ID. It does not guarantee the correct recovery: the prediction may drift, or another person may overlap it. The official evaluator also skips updates on frames with no detections. Retention therefore counts tracker updates, which are not necessarily identical to video frames. The port preserves this behavior for fidelity, rather than silently improving the algorithm.

保留更久，会让重新出现的检测有更多机会找回旧编号。但不能保证找对：预测可能偏离，也可能与另一个人重叠。官方评测流程还会跳过完全没有检测的帧。因此，保留时间实际按追踪器更新次数计算，不一定等于视频帧数。移植为了忠实复现，保留了这个行为，没有悄悄改变算法。

## 4. Separating detection from tracking / 将检测与追踪分开检查

A **detection cache** stores each frame's boxes and scores in a text file. Both trackers receive exactly those saved values. If their tracks differ, we can investigate tracking without rerunning the model or blaming different detector output. We also run an end-to-end path directly from images. Its tracking output must match the cache path, establishing that the pieces work together. The cache is an experimental tool; a deployed video pipeline does not need to write it.

**检测缓存（detection cache）**把每帧的框和分数保存为文本文件。两个追踪器收到完全相同的数值。如果轨迹不同，就可以直接调查追踪逻辑，不必重跑模型，也不必怀疑检测输入不同。另有直接从图片运行的端到端流程，它的追踪输出应与缓存流程一致，以检查各部分接起来是否正确。缓存是实验工具，实际视频产品不一定需要写它。

We checked **determinism**, meaning repeatability of the output under the tested execution settings: one versus four inference threads on the fixed 50-frame slice. Both models' caches were byte-identical, permitting four threads for accuracy runs. A **behavioral fixture** is a small artificial input designed to exercise particular rules. Ours includes weak detections, lost/recovered tracks, expiry, empty frames and exact score thresholds. It caught a real float32 threshold-comparison mistake in C++; the initial failure was retained and the corrected version passed. This was an implementation correction, not a change to the thresholds.

我们检查了 **determinism（确定性）**，即在所测试的执行设置下，输出能否重复一致：固定 50 帧，比较一个和四个推理线程。两个模型的缓存逐字节相同，因此准确性运行可以使用四线程。**行为检查样例（behavioral fixture）**是人为构造的少量输入，用来触发指定规则。这里覆盖弱检测、失踪找回、超时、空帧和恰好等于分数门槛的情况。它发现了 C++ 的一次 float32 门槛比较错误；失败记录保留，修正后通过。这是修正实现，没有改变门槛数值。

## 5. Two evaluators, labelled results / 两种评估器，分别标注

**motmetrics** is the Python evaluation library used by ByteTrack's published procedure. We use that same procedure to compare with the published numbers. **TrackEval** is another evaluation toolkit, used here for HOTA and companion MOTA/IDF1 results. Its standard dataset preprocessing removes distractor classes before scoring. These two procedures can therefore report different scores on the same tracks, particularly in crowded MOT20 footage. Every table labels its evaluator; one tool's baseline must not be compared with the other tool's variant.

**motmetrics** 是 ByteTrack 公布结果所用流程里的 Python 评估库。我们使用同样流程，才能与公布数字比较。**TrackEval** 是另一套评估工具，这里用于 HOTA 及配套的 MOTA、IDF1。它的标准数据预处理会在评分前移除干扰类别。因此，相同轨迹也可能得到不同分数，密集的 MOT20 尤其明显。每张表都注明评估器；不能把一个工具的基线与另一个工具的改进结果比较。

As a sanity check, TrackEval evaluated each dataset's annotation against itself and scored 100 for all three metrics on every sequence. This verifies the evaluation setup on a known answer. It does not prove that a detector or tracker is accurate. The fixed Phase 3 checks are implementation fidelity against Python and reproduction of the published MOT17 results.

作为基本检查，我们让 TrackEval 将标注与自身比较，每段序列的三项指标都是 100。这验证了评估流程能处理一个已知答案，并不证明检测器或追踪器准确。阶段 3 的固定验收检查是与 Python 实现一致，以及复现公布的 MOT17 结果。

## 6. What the measurements say / 实测结果说明什么

Every one of the 14 MOT17 model/sequence pairs had zero difference in MOTA and IDF1 between Python and C++. Both models also passed the ±1.0-point published-score check. All 22 end-to-end track files were byte-identical to their cached-C++ counterparts. These results support the fidelity claim, including on sequences where the reference tracker makes mistakes.

MOT17 的 14 组模型与序列组合，Python 和 C++ 的 MOTA、IDF1 差值全部为零。两个模型与公布结果的差距也都在 ±1.0 分内。22 份端到端轨迹文件与缓存 C++ 文件逐字节相同。这些结果支持忠实移植的结论，包括参照追踪器本来就会出错的序列。

| Dataset / purpose | Evaluator | Model | MOTA | IDF1 | HOTA |
|---|---|---|---:|---:|---:|
| MOT17 / fidelity | motmetrics | nano | 69.23 | 66.84 | — |
| MOT17 / fidelity | motmetrics | tiny | 77.13 | 71.57 | — |
| MOT20 / held-out | motmetrics | nano | 56.02 | 51.37 | — |
| MOT20 / held-out | motmetrics | tiny | 61.08 | 59.49 | — |
| MOT20 / held-out | TrackEval | nano | 62.42 | 53.31 | 42.07 |
| MOT20 / held-out | TrackEval | tiny | 68.05 | 61.88 | 48.78 |

The model saw MOT17 during training, so those scores remain fidelity results. MOT20 was not used in training or parameter tuning here. Lower scores there show a harder deployment problem, but do not isolate the reason: MOT20 is also much more crowded. **Domain shift** means that deployment scenes differ from the training scenes. Training exposure and domain shift are separate possible contributors; this experiment cannot assign a percentage to each. Tiny scores higher but requires a larger model. Formal speed and memory comparisons belong to Phase 4; concurrent accuracy-run timings cannot answer that trade-off reliably.

模型训练时见过 MOT17，所以那里的数字始终只是复现结果。MOT20 没有用于这里的训练或参数调整。较低的分数说明部署问题更难，但没有单独确定原因：MOT20 也密集得多。**领域偏移（domain shift）**指实际使用场景与训练场景不同。训练集暴露与领域偏移可能分别影响结果，本实验不能分配各自占比。tiny 分数更高，但模型更大。正式速度、内存比较属于阶段 4；并行准确性运行的耗时不能可靠回答这个取舍。

## 7. Matching files is not matching people / 文件一致不等于始终认对人

Python and C++ score text is not byte-identical: Python expands rounded float32 values while C++ writes two decimal places. Most numeric differences are below 2.87e-8; three held-out rows differ by 0.01 because the writers round a decimal-half boundary differently. Frames, IDs and boxes still agree. Neither evaluator uses those output scores in the configured scoring path. The report keeps literal file equality separate from numerical equivalence.

Python 和 C++ 的分数文本并不逐字节一致：Python 会展开舍入后的 float32 小数，C++ 则写两位小数。多数数值差异小于 2.87e-8；留出集有三行由于写入器对半分界舍入不同，相差 0.01。帧、编号和框仍然一致。在当前评分流程中，两套评估器都不使用这些输出分数。报告分别保留文本一致性和数值比较。

An **ID switch** happens when a person's associated tracker ID changes. The owner found two concrete failures. In MOT20-03, person 169 loses ID 75 behind a pillar and returns as 107 after retention expires. In MOT17-05, person 14 is followed as 3, then 4, then 18. ID 4 initially belonged to a different person, so the second case also demonstrates a wrong recovery, not just expiry. The cache replays confirm both failures in Python and C++. They remain documented in the paired case reports; no labels were repaired to make the demonstrations look continuous.

**ID switch（身份编号切换）**指同一个人被关联的追踪编号发生改变。使用者发现了两个具体失败。MOT20-03 中，标注 169 号的人在柱子后失去编号 75，超过保留时间后以 107 出现。MOT17-05 中，标注 14 号的人先后被编号为 3、4、18。4 号最初属于另一个人，因此第二例也证明了错误找回，并非只有超时。缓存重放确认 Python 和 C++ 都有这些问题。两例均保留成对报告，没有修补演示编号来制造连续追踪的假象。

## 8. Reading the demonstrations / 怎样理解演示

OpenCV draws a stable color for each ID and the last two seconds of box-bottom positions as a trail. These are image-space positions, not a person's path on a measured street map. Camera movement changes that picture-space trail. Missing frames break the drawn trail, and a new ID receives a new color. Videos play at their source rate; this does not imply that model inference can keep up with that rate. The three videos illustrate measured behavior and help find failures, while complete-sequence scores quantify broader behavior. Both kinds of evidence matter for deciding whether the intended application is ready.

OpenCV 给每个编号画固定颜色，用最近两秒框底部的位置画轨迹。这些是画面坐标，不是测量过的街道地图上的行走路线。镜头移动也会改变画面中的轨迹。缺帧会断开线条，新编号会获得新颜色。视频按源帧率播放，并不意味着模型推理跟得上这个速度。三段视频展示实测行为，便于发现失败；完整序列评分则衡量更广泛的表现。判断目标应用是否可用，两种证据都需要。

## New terms / 新术语

| Term | 中文 | Meaning / 含义 |
|---|---|---|
| Track ID | 追踪编号 | Identity label maintained across frames / 跨帧尽量保持的身份标签 |
| Kalman filter | 卡尔曼滤波器 | Predict motion and correct it with observations / 预测运动，再用观测修正 |
| Linear assignment | 线性分配 | Minimize the total pairing cost / 最小化配对总代价 |
| Score fusion | 分数融合 | Combine detection confidence with overlap for association / 将置信度与重叠程度共同用于关联 |
| Detection cache | 检测缓存 | Saved boxes and scores reused by trackers / 供追踪器复用的框和分数 |
| Determinism | 确定性 | Repeatable output under tested execution settings / 在测试设置下可重复一致的输出 |
| Behavioral fixture | 行为检查样例 | Artificial inputs exercising specific rules / 用人工输入触发指定规则 |
| motmetrics | 评估库名称 | Library used by the published ByteTrack evaluation procedure / 公布结果所用流程的评估库 |
| TrackEval | 评估工具名称 | Toolkit with dataset preprocessing and multiple tracking metrics / 含数据预处理和多项指标的工具集 |
| Domain shift | 领域偏移 | Deployment scenes differ from training scenes / 实际场景不同于训练场景 |
| ID switch | 身份编号切换 | One person's associated tracker ID changes / 同一人的关联编号改变 |
