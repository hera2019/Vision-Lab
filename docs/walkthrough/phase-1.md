# Phase 1 walkthrough — converting the model, and checking nothing got lost

# 第 1 阶段讲解：转换模型格式，并检查有没有「走样」

*English first, then Chinese. Terms already explained in
[Phase 0](phase-0.md) are not repeated.*

*先英文后中文。[第 0 阶段](phase-0.md)解释过的词不再重复。*

---

## 1. The goal / 目标

The ByteTrack authors saved their models in **PyTorch** format. PyTorch is
the most popular Python toolkit for building and training neural networks (a
**neural network** is the kind of model made of many layers of simple
calculations). Our C++ program cannot read PyTorch files, so we **export**
(convert) them to ONNX. Then we check the ONNX copy gives the same answers as
the original.

ByteTrack 作者用 **PyTorch** 格式保存模型。PyTorch 是最流行的 Python 工具包，用来搭建和训练神经网络（**神经网络**是由很多层简单计算组成的一类模型）。我们的 C++ 程序读不了 PyTorch 文件，所以要把模型**导出**（转换）成 ONNX，再检查 ONNX 版本给出的答案是否和原版一样。

---

## 2. Downloads / 下载了什么

We downloaded the two checkpoints (nano 7.6 MB, tiny 41 MB) from the authors'
Google Drive links, the ByteTrack source code from GitHub, and the MOT17 and
MOT20 datasets (5.9 GB and 5.0 GB as zip files). Every file's SHA-256 fingerprint
is written in `assets.json`, so anyone can check they got the same files. MOT17
contains three identical copies of its images (one per old detector it was
packaged with), so we unpacked just one copy: 861 MB instead of several GB.

我们从作者的 Google Drive 链接下载了两个检查点（nano 7.6 MB，tiny 41 MB），从 GitHub 下载了 ByteTrack 源代码，还下载了 MOT17 和 MOT20 数据集（压缩包分别是 5.9 GB 和 5.0 GB）。每个文件的 SHA-256 指纹都写在 `assets.json` 里，别人可以核对自己拿到的是不是同样的文件。MOT17 的图片有三份一模一样的副本（当年给三种旧检测器各打包了一份），所以只解压了一份：861 MB，而不是好几个 GB。

We also built a second Docker image, `pytools`, holding Python, PyTorch and the
other tools, with **pinned versions** (exact version numbers written down, so
the setup can be rebuilt identically later).

我们还建了第二个 Docker 镜像 `pytools`，里面装了 Python、PyTorch 和其他工具，而且**固定了版本**（把确切的版本号写下来，以后能原样重建同样的环境）。

---

## 3. Exporting / 导出

Export works by feeding the model one dummy image and recording every
calculation it performs into an ONNX file. The image size is fixed at
608 × 1088 pixels, the size the model was trained for. We used **opset** 13
(the version of ONNX's list of allowed operations; 13 or newer is needed later
for INT8). The nano file is 3.65 MB and tiny is 20.2 MB, smaller than the
checkpoints because the training-only data is left out.

导出的做法是：给模型喂一张假图片，把它做的每一步计算记录进 ONNX 文件。图片尺寸固定为 608 × 1088 像素，也就是模型训练时用的尺寸。我们用的是 **opset** 13（ONNX 允许使用的运算清单的版本号；之后做 INT8 需要 13 或更新的版本）。导出的 nano 文件 3.65 MB，tiny 20.2 MB，比检查点小，因为只在训练时用到的数据没有放进去。

---

## 4. How the model "sees" an image / 模型怎样「看」一张图

Before an image goes into the model it is **preprocessed**: shrunk to fit
608 × 1088 without stretching, with the leftover area filled with grey
(**letterboxing**, like black bars on a widescreen film), then
**normalised** (each colour value shifted and scaled into a small standard
range the model is used to).

图片进模型之前要先**预处理**：等比例缩小到 608 × 1088 以内，不拉伸变形，空出来的地方用灰色填满（叫 **letterbox**，就像宽银幕电影上下的黑边），然后**归一化**（把每个颜色值平移、缩放到模型习惯的一个小的标准范围里）。

The model's output is a **tensor** (a grid of numbers, here 13,566 rows ×
6 columns). Each row is an **anchor**: a fixed spot on the image where the
model checks "is there a person centred here?". Anchors are laid out in three
grids with a **stride** of 8, 16 and 32 pixels (the spacing between spots;
fine grids find small people, coarse grids find big ones). The 6 numbers per
anchor are 4 box values, an **objectness** score (is there *any* object
here?) and a **class score** (is it a person?). Their product is the
detection **confidence**.

模型的输出是一个**张量**（一个数字表格，这里是 13,566 行 × 6 列）。每一行叫一个**锚点**（anchor）：图上一个固定的位置，模型在那里判断「这里是不是有一个人的中心？」。锚点排成三层网格，**步长**（stride）分别是 8、16、32 像素（相邻位置的间距；细网格找小个子的人，粗网格找大个子的人）。每个锚点的 6 个数是：4 个框的数值、一个**物体性**分数（这里有没有*任何*物体？）、一个**类别分数**（是不是人？）。后两者相乘就是这个检测的**置信度**。

These raw values still need **decoding** (turning the 4 box values into real
pixel coordinates) and **NMS** (Non-Maximum Suppression: when several
overlapping boxes describe the same person, keep the best one and delete the
rest). Those steps are Phase 2's job, in C++.

这些原始数值还需要**解码**（把 4 个框数值换算成真正的像素坐标）和 **NMS**（非极大值抑制：几个重叠的框描述的是同一个人时，留下最好的一个，删掉其余的）。这两步是第 2 阶段用 C++ 来做的。

---

## 5. The parity check / 一致性检查

**Parity** means "the two versions behave the same". We picked 20 MOT17 frames
at random, but with a fixed **seed** (the starting number for a random
generator, so the same "random" frames are picked every time). Each frame went
through both PyTorch and ONNX Runtime, and we compared all
13,566 × 6 numbers. The pre-set rule was: the biggest **absolute
difference** (|a − b|) must be ≤ 0.001, called the **tolerance**.

**一致性**（parity）指「两个版本表现相同」。我们随机挑了 20 帧 MOT17 画面，但固定了**随机种子**（随机数生成器的起始数字，这样每次挑出来的「随机」帧都一样）。每帧分别送进 PyTorch 和 ONNX Runtime，比较全部 13,566 × 6 个数字。预先定的规则是：最大的**绝对误差**（|a − b|）必须 ≤ 0.001，这个上限叫**容差**。

Result: tiny passed (0.00016). **Nano failed (0.00118).**

结果：tiny 通过（0.00016），**nano 没通过（0.00118）**。

---

## 6. Investigating the failure / 追查失败原因

We did not change the rule after seeing the result. Instead we asked three
questions.

看到结果后，我们没有改规则，而是追问了三个问题。

**Where is the worst difference?** On an anchor whose confidence was
0.00000000078, i.e. empty background. Detections are only kept above about
0.1, so this anchor can never become a box.

**最大的误差在哪？** 在一个置信度只有 0.00000000078 的锚点上，也就是空背景。只有置信度大约 0.1 以上的才会留下当检测框，所以这个锚点永远不会变成框。

**Is ONNX Runtime's optimiser to blame?** ORT normally rewrites the
calculation graph to make it faster (**graph optimisation**: e.g. merging
two steps into one). We turned it fully off and the difference stayed exactly the
same, so the optimiser is innocent. Our best guess (a **hypothesis**, not
proven) is that PyTorch and ORT add up numbers in a slightly different order.
Computers store decimals as **float32** (32-bit floating point, about 7 digits
of precision), so a different order gives tiny rounding differences. Nano uses
**depthwise convolutions** (a cheaper type of image filter), which may be more
sensitive to this.

**是不是 ONNX Runtime 的优化器惹的祸？** ORT 通常会改写计算图让它跑得更快（叫**图优化**，比如把两步合成一步）。我们把优化完全关掉，误差还是一模一样，所以不是优化器的问题。我们的最佳猜测（只是**假设**，没有证明）是：PyTorch 和 ORT 做加法的先后顺序略有不同。电脑用 **float32**（32 位浮点数，大约 7 位有效数字）存小数，顺序不同就会产生极小的舍入误差。nano 用了**深度可分离卷积**（一种更省计算的图像滤波方式），可能对这种误差更敏感。

**Does it change any result?** No. On every anchor that could become a
detection, the two versions agree to 0.000024; decoded boxes differ by under
0.002 pixels; the number of candidate boxes was identical on all 20 frames.

**它会改变任何结果吗？** 不会。在所有可能变成检测框的锚点上，两个版本的差距只有 0.000024；解码后的框相差不到 0.002 像素；20 帧里候选框的数量全部相同。

---

## 7. What we learned / 学到了什么

The rule itself was poorly designed: it counted thousands of background anchors
that never affect the output. The honest response is to keep "nano: fail" in the
record, explain it, and make sure later rules measure what matters. Phase 2's
rule already compares final detections, after NMS. A failed test is not always a
broken system, just as a passed test is not always a working one. The question
is always *what the test actually measures*.

问题出在规则本身设计得不好：它把成千上万个永远不会影响结果的背景锚点也算了进去。诚实的做法是：在记录里保留「nano：未通过」，把原因讲清楚，并确保之后的规则测的是真正重要的东西。第 2 阶段的规则本来就比较最终的检测框（NMS 之后）。测试没通过不一定说明系统坏了，正如测试通过也不一定说明系统没问题。关键永远是：*这个测试到底测的是什么*。

---

## Terms / 术语表

| Term | 中文 | One-line meaning / 一句话解释 |
|---|---|---|
| PyTorch | — | Popular Python toolkit for neural networks / 流行的 Python 神经网络工具包 |
| Neural network | 神经网络 | Model built from many layers of simple calculations / 由多层简单计算组成的模型 |
| Export | 导出 | Convert a model to another format / 把模型转成另一种格式 |
| Pinned version | 固定版本 | Exact version recorded for exact rebuilds / 记下确切版本以便原样重建 |
| Opset | — | Version of ONNX's operation list / ONNX 运算清单的版本 |
| Preprocessing, letterbox, normalisation | 预处理、加边框、归一化 | Prepare the image: resize without stretching, pad, rescale values / 准备图片：等比缩放、填边、调整数值范围 |
| Tensor | 张量 | A multi-dimensional grid of numbers / 多维的数字表格 |
| Anchor, stride | 锚点、步长 | A fixed check spot; spacing between spots / 固定检查位置；位置间距 |
| Objectness, class score, confidence | 物体性、类别分数、置信度 | Is there an object; is it a person; their product / 有没有物体；是不是人；两者乘积 |
| Decoding | 解码 | Turn raw outputs into pixel boxes / 把原始输出换算成像素框 |
| NMS | 非极大值抑制 | Keep the best of overlapping duplicate boxes / 重叠的重复框只留最好的 |
| Parity | 一致性 | Two versions behave the same / 两个版本表现相同 |
| Seed | 随机种子 | Makes "random" choices repeatable / 让「随机」可以重复 |
| Absolute difference, tolerance | 绝对误差、容差 | \|a − b\|; the allowed maximum / \|a − b\|；允许的上限 |
| Graph optimisation | 图优化 | Rewriting calculations to run faster / 改写计算让它更快 |
| Hypothesis | 假设 | An unproven explanation / 尚未证明的解释 |
| float32 | 32 位浮点数 | Decimal storage with ~7 digits precision / 约 7 位有效数字的小数存储方式 |
| Depthwise convolution | 深度可分离卷积 | A cheaper kind of image filter layer / 更省计算的一种图像滤波层 |
