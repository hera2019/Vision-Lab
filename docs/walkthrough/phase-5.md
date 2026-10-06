# Phase 5 walkthrough — seeing how tracking fails

# 第 5 阶段讲解：看清追踪怎样失败

Phase 5 documents three failure categories using existing nano FP32 outputs
on held-out MOT20. It adds evidence, not a new tracking algorithm. Each crop
shows three source frames from a stated interval, with the annotated target
in yellow and its associated prediction in cyan. The accepted pipeline and
all earlier scores remain unchanged. The full records are in
[the failure report](../../results/phase-5-failures.md).

阶段 5 使用现有 nano FP32 在 MOT20 留出集上的输出，记录三类失败。它增加的是证据，
没有引入新的追踪算法。每张局部图展示明确区间中的三张原始帧，黄色框是人工标注的
目标，青色框是与它对应的预测。已验收的流水线和之前的分数均保持不变。
完整记录见[失败报告](../../results/phase-5-failures.md)。

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
app access. That meets the mandatory Phase 5 documentation requirement;
independent review remains pending. The optional mean-shift bonus has not
been run. Phase 6 will address reproduction from a clean checkout; the INT8
root cause and continuous identity recovery remain unresolved.

我们特意选择能说明问题的错误，不是随机抽样。遮挡案例由用户先发现，另外两例
使用扫描前写好的固定选择规则。三个例子不能推出各类错误的频率、模型排名，或新的
整体准确率结论。每例都记录序列、完整帧区间、目标框、可见度、匹配历史、检测重叠、
源文件校验值和保留上下文的局部图。三张图片解码后与写入前完全一致，并直接作为
文件检查，没有读取屏幕或操作应用。这满足阶段 5 的必需失败文档要求，独立复核
仍待进行。可选的 mean-shift 加分实验没有运行。阶段 6 将处理干净检出后的复现；
INT8 的具体根因和身份连续恢复问题仍未解决。

## New terms / 新术语

| Term | 中文 | Meaning / 含义 |
|---|---|---|
| Correspondence | 对应关系 | Evaluator pairing between annotated person and predicted track / 评估器配对人工标注人物与预测轨迹 |
| Visibility | 可见度 | Dataset annotation of target visibility / 数据集标注的目标可见程度 |
| Truncation | 截断 | Part of a target outside the image / 目标一部分在画面之外 |
