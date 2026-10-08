# Phase 5 walkthrough — seeing how tracking fails

# 第 5 阶段讲解：看清追踪怎样失败

The original Phase 5 pass documents three failure categories using existing
nano FP32 outputs on held-out MOT20. Each crop
shows three source frames from a stated interval, with the annotated target
in yellow and its associated prediction in cyan. The accepted pipeline and
all earlier scores remain unchanged. The full records are in
[the failure report](../../results/phase-5-failures.md). Section 6 adds the
subsequent mean-shift control completed on 2026-10-08.

阶段 5 最初使用现有 nano FP32 在 MOT20 留出集上的输出，记录三类失败。
每张局部图展示明确区间中的三张原始帧，黄色框是人工标注的
目标，青色框是与它对应的预测。已验收的流水线和之前的分数均保持不变。
完整记录见[失败报告](../../results/phase-5-failures.md)。第 6 节补充了
2026-10-08 完成的均值漂移对照实验。

## 1. A box needs a reference / 判断框是否正确，需要参照

**Correspondence** means the evaluator pairs an annotated person with a
predicted track in one frame. It uses overlap and the previous correspondence
to avoid unnecessary changes. We use the same TrackEval pedestrian filtering
and CLEAR matching rule as the existing baseline, then cross-check our event
counts with upstream CLEAR. Original GT and predicted IDs are retained in the
records even though the evaluator internally renumbers them. A missing cyan
box in the crop means no accepted correspondence at IoU 0.5, not that the
detector emitted no box anywhere nearby. GT is available for this analysis;
a future ordinary video would not supply those reference labels.

**对应关系（correspondence）**是评估器在一帧中，将一个人工标注的人与一个预测轨迹
配成一对。它使用重叠程度和上一帧的对应关系，避免不必要的变化。这里采用与现有
基线相同的 TrackEval 行人过滤和 CLEAR 匹配规则，并将事件计数与官方 CLEAR 核对。
虽然评估器内部会重新编号，记录仍保留原始人工标注编号与预测编号。图中没有青色框，
表示在 IoU 0.5 的条件下没有合格的对应关系，不表示附近完全没有检测框。
这些参照标签可用于本次分析，未来普通视频不会自带它们。

## 2. Occlusion and a new identity / 遮挡后出现新编号

The first case is the owner's MOT20-03 observation. Annotated person 169 is
track 75 before the pillar and track 107 afterward. At frame 130 the annotated
**visibility**, a dataset-provided indication of how visible the target is,
is 0.67. At frame 155 it is zero and there is no matched track; at frame 180
it is 0.37 and the new track appears. The previous reference-state replay
established that track 75 was removed after its 30-update retention expired,
before 107 was born. This is a concrete recovery failure after a long gap.
It does not establish that every occlusion is longer than the buffer or that
simply extending the buffer fixes every identity error.

第一例就是用户发现的 MOT20-03 问题。人工标注的人物 169 在柱子之前对应轨迹 75，
之后对应 107。第 130 帧的**可见度（visibility）**是 0.67；这是数据集提供的目标
可见程度标注。第 155 帧降为零，没有匹配轨迹；第 180 帧为 0.37，新轨迹出现。
之前对官方追踪器状态的回放证实：轨迹 75 的 30 次更新保留期限已到，先被移除，
107 才建立。这是一个长时间缺失后未恢复原编号的具体失败。
它不能证明所有遮挡都超过保留时间，也不能证明延长保留时间能修好所有身份错误。

## 3. A visible person can still change identity / 人还看得见，也会换编号

The second case is MOT20-01, annotated person 28, frames 185–194. Five
consecutive frames correspond to track 13, followed by five corresponding to
22, with the change at frame 190. Visibility stays at 1.0 and another
annotated person overlaps at the change. The cached detector has good target
overlap: IoU 0.883 at frame 189 and 0.897 at frame 190. Thus this is not a
simple example of every useful detection disappearing. It demonstrates an
identity correspondence failure in a crowded neighborhood. The crops and
counts alone do not isolate the exact internal association that caused it;
that would require a separate tracker-state investigation.

第二例是 MOT20-01 的人物 28，第 185–194 帧。连续五帧对应轨迹 13，之后连续五帧
对应 22，变化发生在第 190 帧。可见度一直为 1.0，变化时还有另一个标注人物与它
重叠。缓存检测框与目标的重叠很好：第 189 帧 IoU 为 0.883，第 190 帧为 0.897。
因此，这不属于有用的检测全部消失的简单情况，而是在拥挤邻域发生的身份对应失败。
仅凭这些图和计数，不能确定是哪一次内部关联造成了错误；那需要另外调查追踪器状态。

## 4. Small visible extent and the image boundary / 可见部分很小，又在画面边缘

The third case is MOT20-01, annotated person 39, frames 86–93. Its annotated
height becomes only 19–28 pixels after resizing to the detector's native
input. It has no matched track in all eight frames; cached detections also
fail the IoU 0.5 correspondence condition throughout the interval. Nearby
detector boxes exist with low scores, but are much larger and poorly aligned.
The crop shows a head entering at the bottom edge. **Truncation** means part
of a person lies outside the image. This condition co-occurs with the small
annotated extent, so the example must not be presented as a distant person
that the model cannot see. The high visibility label concerns the annotated
extent and does not mean a complete body is visible. Keeping an old number
for longer would not create a good first detection here.

第三例是 MOT20-01 的人物 39，第 86–93 帧。缩放到检测器原生输入后，标注高度只有
19–28 个像素。八帧都没有匹配轨迹，缓存检测也在整个区间都不满足 IoU 0.5 的对应
条件。附近确实有低分检测框，但它们大得多，位置也不吻合。局部图显示的是从画面
底部刚进入的头部。**截断（truncation）**表示人物的一部分在画面之外。它与小的
标注范围同时存在，所以不能将这例说成“远处的人，模型看不到”。较高的可见度标签
针对标注范围，不表示完整身体可见。延长旧编号保留时间，也不能在这里生成一个好的
初次检测。

## 5. What this phase establishes / 这一阶段证实了什么

We deliberately selected illustrative errors, not a random sample. The
occlusion case was already reported by the owner; the other two use fixed
selectors written before the scan. No category frequency, model ranking or
new overall accuracy claim follows from three examples. Each case provides
its sequence, full frame interval, target boxes, visibility, match history,
detector overlap, source hashes and context-preserving crop. The three image
files decode exactly and were inspected directly as files, without screen or
app access. That meets the mandatory Phase 5 documentation requirement.
The subsequent Opus review accepted Phases 3–6, including this case evidence
and clean-clone reproduction. The new bonus below is outside that verdict.
Accelerated INT8 repair and continuous identity recovery remain unresolved.

我们特意选择能说明问题的错误，不是随机抽样。遮挡案例由用户先发现，另外两例
使用扫描前写好的固定选择规则。三个例子不能推出各类错误的频率、模型排名，或新的
整体准确率结论。每例都记录序列、完整帧区间、目标框、可见度、匹配历史、检测重叠、
源文件校验值和保留上下文的局部图。三张图片解码后与写入前完全一致，并直接作为
文件检查，没有读取屏幕或操作应用。这满足阶段 5 的必需失败文档要求。
之后 Opus 已验收阶段 3–6，包括这些案例证据与干净检出后的复现。
下面新增的加分实验不在那次验收范围内。INT8 加速修复和身份连续恢复仍未解决。

## 6. Classical mean-shift control / 经典均值漂移对照

**Mean-shift** moves a tracking window toward the center of pixels matching
the target's initial color distribution. **HSV** means hue, saturation and
value: color type, color intensity and brightness. We build a **histogram**,
a count of hue values, from the first target box. **Backprojection** assigns
each later pixel a weight from that histogram. OpenCV repeatedly shifts the
window toward the weighted center, at most ten times per frame. The histogram
and window size stay fixed. This is a small classical tracker, with no person
detector, re-identification or scale adaptation.

**均值漂移（mean-shift）**把追踪窗口移向符合目标初始颜色分布的像素中心。
**HSV** 是色相（hue）、饱和度（saturation）和明度（value），分别描述颜色类型、
浓淡与亮暗。我们在目标的初始框里建立**直方图（histogram）**，统计各色相的数量。
**反向投影（backprojection）**根据这个统计，为后续画面的每个像素赋予权重。
OpenCV 反复把窗口移向加权中心，每帧最多十次。直方图与窗口大小保持固定。
这个简单经典追踪器没有行人检测、身份重识别或大小适应能力。

The original plan supplies a ground-truth (GT, human-annotated reference)
box at each person's first valid appearance. This **oracle initialization**
gives mean-shift both the start time and correct initial position; an ordinary
video does not provide them. After initialization, no later GT position,
visibility or exit label is used. Every initialized tracker persists to the
end, including empty color histograms. This fixed protocol can leave boxes
after people depart and drift between similar clothes. It was declared before
scoring; removing failures afterward would change the experiment.

原计划在每个人首次有效出现时，提供一个人工标注框（ground truth，简称 GT）。
这种**使用参照答案的初始化（oracle initialization）**，提前告诉均值漂移何时开始、
正确的初始位置在哪里；普通视频没有这些信息。初始化后，不再使用后续 GT 位置、
可见度或离场标签。所有初始化的追踪器一直保留到视频结束，颜色直方图为空也一样。
这个固定方案会在人离场后留下框，也可能在相似衣服之间漂移。这些规则在评分前确定；
看到结果后再删除失败框，就改变了实验。

All 8,931 frames across four MOT20 sequences were processed once. We scored
the new outputs and existing nano/tiny FP32 outputs with the same pinned
TrackEval pedestrian preprocessing and metrics. Existing baseline scores and
track hashes reproduce exactly. These are percentages from TrackEval; they
must not be mixed with the project's separately reported motmetrics values.

四条 MOT20 序列的全部 8,931 帧各处理一次。新增输出与现有 nano/tiny FP32 输出，
使用相同版本的 TrackEval、行人预处理与指标评分。原有基线的分数和轨迹文件校验值
完全复现。下表是 TrackEval 百分数，不能与项目另行报告的 motmetrics 分数混用。

| Method / 方法 | HOTA | MOTA | IDF1 |
|---|---:|---:|---:|
| Mean-shift / 均值漂移 | 4.24 | −252.30 | 3.11 |
| Nano FP32 + ByteTrack | 42.07 | 62.42 | 53.31 |
| Tiny FP32 + ByteTrack | 48.78 | 68.05 | 61.88 |

HOTA combines detection and identity association quality. Negative MOTA is
valid: false positives, misses and identity switches together exceed the
annotated-target count. Mean-shift performs very poorly here despite initial
reference boxes. Its unchanged ID labels do not prove it follows the same
people. This characterizes the fixed tutorial-style control, not every
classical algorithm. A separate sparse MOT17 clip measured 135.69 FPS in
three one-thread runs, but has different initialization/workload and session
from the detector benchmark; image bytes were pre-read for checksums. It
does not establish a paired speedup or dense-scene real-time acceptance.

HOTA 综合衡量检测与身份关联质量。MOTA 为负是有效结果：误报、漏检与身份切换
加起来超过了标注目标的总数。这里即使提供初始参照框，均值漂移仍表现很差。
编号没有改变，也不能证明它跟着同一个人。这描述的是固定的教程式对照方案，
不能推广到所有经典算法。另一个较稀疏的 MOT17 短片经过三次单线程测速，得到
135.69 FPS；但初始化方式、工作量和运行时间都与检测器基准不同，图像字节还因
校验而提前读取。因此它不能证明成对加速收益，也不构成密集场景的实时验收。

See the [full comparison](../../results/phase-5-meanshift.md) and
[fixed protocol](../MEANSHIFT_EXECUTION.md). The own computational shortcuts
match standard OpenCV windows in 160 checks and upstream TrackEval arrays
and metrics on all 837 MOT17-05 frames. Independent bonus review and its
fresh-clone execution remain unverified; earlier full-run evidence covers
the prior profile. No accepted model or threshold changes.

完整证据见[对比报告](../../results/phase-5-meanshift.md)与
[固定实验方案](../MEANSHIFT_EXECUTION.md)。我们只优化计算方式：160 个窗口检查
与标准 OpenCV 一致，全部 837 帧 MOT17-05 的评估数组和指标与原版 TrackEval 一致。
新增实验尚未独立复核，也未从干净检出单独运行；之前完整复现的证据覆盖的是原有流程。
已验收模型与判定阈值保持不变。

## New terms / 新术语

| Term | 中文 | Meaning / 含义 |
|---|---|---|
| Correspondence | 对应关系 | Evaluator pairing between annotated person and predicted track / 评估器配对人工标注人物与预测轨迹 |
| Visibility | 可见度 | Dataset annotation of target visibility / 数据集标注的目标可见程度 |
| Truncation | 截断 | Part of a target outside the image / 目标一部分在画面之外 |
| Mean-shift | 均值漂移 | Moving a window toward weighted pixel mass / 把窗口移向像素加权中心 |
| HSV | 色相、饱和度、明度 | Hue, saturation, value color representation / 一种颜色表示方式 |
| Histogram | 直方图 | Counts grouped by value / 按数值分组统计数量 |
| Backprojection | 反向投影 | Weighting pixels by the target histogram / 按目标直方图赋予像素权重 |
| Oracle initialization | 使用参照答案的初始化 | Providing annotated first-appearance time and box / 提供人工标注的首次出现时间与框 |
