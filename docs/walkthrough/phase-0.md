# Phase 0 walkthrough — planning and setting up the workshop

# 第 0 阶段讲解：定计划，搭好工作台

*Each paragraph is in English first, then in Chinese. Terms in **bold** are
defined the first time they appear; the table at the end collects them.*

*每段先英文、后中文。**粗体**的词在第一次出现时解释，文末有汇总表。*

---

## 1. What is this project about? / 这个项目要做什么？

The project teaches a computer to watch a video of a street, draw a box around
every person in every frame (**object detection**), and keep giving the same
person the same ID number as they walk across the screen (**multi-object
tracking**, MOT). Detection answers "where are people in this picture?";
tracking answers "which box in this frame is the same person as that box in the
previous frame?".

这个项目让电脑看一段街道视频，在每一帧画面里给每个人画一个框（**目标检测**），并且在人走动时始终给同一个人同一个编号（**多目标跟踪**，英文缩写 MOT）。检测回答「这张图里人在哪儿？」；跟踪回答「这一帧的这个框，和上一帧的哪个框是同一个人？」。

The twist is that everything must run on a modest **CPU** (the general-purpose
processor every computer has) with no **GPU** (the graphics chip that makes AI
fast). That imitates an **edge device**: a small computer inside a camera, a
robot or a car, where the AI has to run on the spot instead of in a data centre.

难点在于：整个流程只能用普通的 **CPU**（每台电脑都有的通用处理器）来跑，不能用 **GPU**（让 AI 跑得快的显卡芯片）。这是在模拟**边缘设备**：装在摄像头、机器人或汽车里的小电脑，AI 必须在设备上当场运行，而不是交给远方的数据中心。

---

## 2. Choosing the tools / 选工具

**The detector.** A **model** is a program whose behaviour was learned from
examples instead of written by hand. Its learned numbers are called
**weights** (or **parameters**), and a file holding them is a
**checkpoint**. We picked **YOLOX**, a family of detection models, in its two
smallest sizes: *nano* (0.9 million parameters) and *tiny* (5 million). Size
matters because every parameter costs computation, measured in **FLOPs**
(floating-point operations: the number of basic multiply/add steps). Nano needs
about 4 billion per image; tiny about 24 billion.

**检测器。** **模型**是一种程序，它的行为是从大量例子中「学」出来的，而不是人手写的规则。学到的那些数字叫**权重**（也叫**参数**），保存权重的文件叫**检查点**（checkpoint）。我们选了 **YOLOX** 这一系列检测模型里最小的两个：*nano*（90 万个参数）和 *tiny*（500 万个参数）。大小很重要，因为每个参数都要花计算量，计算量用 **FLOPs** 衡量（浮点运算次数，即基本的乘法、加法步骤有多少次）。nano 每张图约 40 亿次，tiny 约 240 亿次。

**The tracker.** **ByteTrack** is a well-known tracking method. Its trick is
to keep even the *low-confidence* boxes (for example a half-hidden person) and
use them to continue existing tracks, instead of throwing them away. Its authors
also published YOLOX nano/tiny checkpoints trained specifically on pedestrians,
which is why we use theirs.

**跟踪器。** **ByteTrack** 是一个很有名的跟踪方法。它的窍门是：连*把握不大*的框（比如被挡住一半的人）也不扔掉，而是用它们去接续已有的轨迹。它的作者还公开了专门用行人数据训练好的 YOLOX nano/tiny 检查点，所以我们直接用他们的。

**Why not the famous "YOLO" from Ultralytics?** Because of its **license**,
the legal terms for using code. Ultralytics uses **AGPL-3.0**, which would
force this whole repository to adopt the same terms. YOLOX uses
**Apache-2.0** and ByteTrack uses **MIT**, both **permissive**: you may
reuse them almost freely as long as you keep the copyright notice.

**为什么不用最有名的 Ultralytics YOLO？** 因为**许可证**，也就是使用代码的法律条款。Ultralytics 用的是 **AGPL-3.0**，会迫使整个仓库也采用同样的条款。YOLOX 用 **Apache-2.0**，ByteTrack 用 **MIT**，两者都是**宽松型**许可证：只要保留版权声明，几乎可以自由使用。

**The runtime.** **ONNX** (Open Neural Network Exchange) is a standard file
format for models, like PDF is for documents: many programs can read it.
**ONNX Runtime** (ORT) is Microsoft's engine that runs ONNX files fast. Running
a trained model to get answers is called **inference** (as opposed to
**training**, which is how the model learned). We call ORT from **C++**, a
fast, compiled programming language widely used in embedded and edge devices.
**Python** is used only for side jobs such as converting and checking.

**运行引擎。** **ONNX**（开放神经网络交换格式）是模型的标准文件格式，就像 PDF 之于文档，很多程序都能读。**ONNX Runtime**（简称 ORT）是微软出的引擎，能快速运行 ONNX 文件。用训练好的模型来得出答案，这个过程叫**推理**（inference）；与之相对的是**训练**，也就是模型学习的过程。我们用 **C++** 调用 ORT。C++ 是一种需要编译、运行很快的编程语言，在嵌入式和边缘设备上用得很广。**Python** 只做辅助工作，比如格式转换和核对。

---

## 3. The data, and a trap we found / 数据，以及我们发现的一个陷阱

A **dataset** is a collection of examples. Ours are **MOT17** and **MOT20**,
public street videos from the MOTChallenge benchmark (a **benchmark** is a
shared test everyone uses so results are comparable). They come with
**ground truth**, the correct boxes and IDs drawn by humans, so we can score
the computer's answers.

**数据集**就是一批例子。我们用的是 **MOT17** 和 **MOT20**，都是 MOTChallenge **基准**里公开的街道视频（**基准**就是大家共用的一套考题，这样不同方法的成绩才能比较）。它们带有**真值**（ground truth），即人工标好的正确框和编号，所以可以给电脑的答案打分。

The scores we will report are **MOTA** (overall tracking accuracy: it
penalises missed people, false boxes and ID mix-ups), **IDF1** (how well IDs
stay consistent over time) and **HOTA** (a newer score balancing detection and
association).

我们会报告的分数有：**MOTA**（整体跟踪准确度，漏掉的人、多出来的错框、编号混淆都会扣分）、**IDF1**（编号在时间上能否保持一致）和 **HOTA**（较新的分数，兼顾检测和关联两方面）。

**The trap.** The published scores for ByteTrack nano/tiny were measured on
MOT17 *train*, but the models were also *trained* on MOT17 train. That is like
grading a student with the exact questions they practised on. This mistake is
called **data contamination** (or **data leakage**). So we decided: MOT17 is
used only to check that our code reproduces the published numbers
(a **fidelity** check). Real accuracy is measured on MOT20, which the model
has never seen (**held-out** data).

**陷阱。** ByteTrack nano/tiny 公布的分数是在 MOT17 *训练集*上测的，而模型恰好也是用 MOT17 训练集*训练*出来的。这就像用学生练过的原题考试。这种错误叫**数据污染**（也叫**数据泄漏**）。所以我们决定：MOT17 只用来检查我们的代码能不能复现官方数字（**还原度检查**）；真正的准确度在 MOT20 上测，模型从没见过这份数据（**留出数据**）。

Both datasets use the **CC BY-NC-SA 3.0** license: credit the authors (BY),
no commercial use (NC), and share derivatives under the same terms (SA).

两个数据集都采用 **CC BY-NC-SA 3.0** 许可证：要注明作者（BY）、不能商用（NC）、衍生作品要用同样条款发布（SA）。

---

## 4. Writing the test plan first / 先写测试计划

Before downloading anything, we wrote down what "pass" means for each phase,
with numbers. These are **acceptance criteria**. Writing them first stops us
from quietly moving the goalposts after seeing results. Examples: "C++ boxes must
overlap the Python boxes by **IoU** ≥ 0.99" (IoU, Intersection over Union, is
the overlap area divided by the combined area of two boxes: 1.0 means identical),
and "real time means ≥ 25 **FPS**" (frames per second).

下载任何东西之前，我们先用数字写清楚每个阶段怎样才算「通过」，这叫**验收标准**。先写下来，是为了防止看到结果后再悄悄改标准。例如：「C++ 画的框和 Python 画的框，重合度 **IoU** 要 ≥ 0.99」（IoU 即交并比：两个框重叠部分的面积除以两个框合起来的面积，1.0 表示完全重合）；「实时」指每秒处理 ≥ 25 **帧**（FPS，每秒帧数）。

We will also measure **latency** (time to process one frame), reported as
**p50** and **p95** (the median, and the time that 95% of frames beat; p95
shows the slow cases), and memory as peak **RSS** (Resident Set Size: how
much RAM the program actually occupies).

我们还会测**延迟**（处理一帧要多久），用 **p50** 和 **p95** 报告（p50 是中位数；p95 指 95% 的帧都比它快，能反映慢的情况）。内存用峰值 **RSS**（常驻内存大小，即程序实际占用的内存）来衡量。

Later we will test **INT8 quantization**: storing the weights as 8-bit
integers instead of 32-bit decimals (**FP32**). It makes models smaller and
often faster, but can cost accuracy, and we will measure how much.

之后我们会测试 **INT8 量化**：把权重从 32 位小数（**FP32**）改存成 8 位整数。这样模型更小、通常也更快，但可能损失准确度，损失多少就是我们要测的。

---

## 5. Docker: a sealed, repeatable workshop / Docker：一个封闭、可复现的工作间

**Docker** packages a program together with everything it needs (operating
system files, libraries, tools) so it runs the same on any computer. The recipe
is a text file called a **Dockerfile**; following it produces an **image** (a
frozen snapshot); running an image gives a **container** (a live, isolated
copy). Our image is based on **Ubuntu 24.04**, a popular version of **Linux**,
the operating system most servers and edge devices use. On a Mac, Docker quietly
runs a small Linux **virtual machine** (VM: a computer simulated in software).

**Docker** 会把程序和它需要的一切（操作系统文件、库、工具）打包在一起，让它在任何电脑上都以同样的方式运行。打包的配方是一个文本文件，叫 **Dockerfile**；按配方做出来的是**镜像**（一个冻结的快照）；把镜像跑起来就得到**容器**（一个正在运行、与外界隔离的副本）。我们的镜像基于 **Ubuntu 24.04**，这是一个流行的 **Linux** 版本，大多数服务器和边缘设备用的都是 Linux。在 Mac 上，Docker 会在后台悄悄运行一台小的 Linux **虚拟机**（VM，用软件模拟出来的电脑）。

Inside the image we install a **compiler** (a tool that turns C++ source code
into a runnable program), **CMake** (a tool that organises the compile
steps), **OpenCV** (a classic library for reading and editing images) and
ONNX Runtime. For ONNX Runtime we pin the exact version (1.30.0) and its
**SHA-256** fingerprint. SHA-256 is a 64-character code computed from a file's
contents; if even one byte changes, the code changes completely, so it proves we
got exactly the file we expected.

我们在镜像里装了**编译器**（把 C++ 源代码变成可运行程序的工具）、**CMake**（组织编译步骤的工具）、**OpenCV**（读取和处理图片的经典库），以及 ONNX Runtime。ONNX Runtime 固定了确切版本（1.30.0）和它的 **SHA-256** 指纹。SHA-256 是根据文件内容算出来的 64 位字符串，哪怕改动一个字节，结果都会完全不同，所以它能证明我们拿到的正是预期的那个文件。

---

## 6. What we actually ran / 实际跑了什么

We wrote a tiny C++ program, `env_check`, that asks ONNX Runtime its version,
lists which hardware it can use (only the CPU, as intended), and makes OpenCV
save and reload a small picture as **JPEG** (the common photo format). It
printed the answers as **JSON** (a simple text format that both people and
programs can read). Everything worked, which was Phase 0's acceptance criterion.

我们写了一个很小的 C++ 程序 `env_check`。它向 ONNX Runtime 询问版本号，列出能用的硬件（按设计只有 CPU），并让 OpenCV 把一张小图存成 **JPEG**（常见的照片格式）再读回来。它把结果输出成 **JSON**（一种人和程序都能读的简单文本格式）。全部正常，这就是第 0 阶段的验收标准。

One small hiccup: the first build failed because Ubuntu's slimmed-down OpenCV
packages lack a configuration file CMake looks for. Rather than install the
full, much larger package, we told CMake where the files are directly. This
problem and its fix are recorded in the results, as all problems are.

一个小插曲：第一次构建失败了，因为 Ubuntu 精简版的 OpenCV 包里缺少 CMake 要找的一个配置文件。我们没有改装体积大得多的完整版，而是直接告诉 CMake 文件在哪里。这个问题和解决办法都记在了结果里，所有问题都会这样记录。

Finally we saved everything with a **git commit**. **Git** is a version-control
tool: a commit is a labelled snapshot of the project you can always return to.

最后，我们用 **git 提交**（commit）保存了全部内容。**Git** 是版本管理工具，一次提交就是项目的一个带说明的快照，以后随时可以回到这个状态。

---

## Terms / 术语表

| Term | 中文 | One-line meaning / 一句话解释 |
|---|---|---|
| Object detection | 目标检测 | Draw a box around each object in an image / 在图中给每个物体画框 |
| MOT (Multi-Object Tracking) | 多目标跟踪 | Keep the same ID for the same object across frames / 跨帧给同一物体保持同一编号 |
| CPU / GPU | 中央处理器 / 图形处理器 | General processor / graphics chip that speeds up AI / 通用处理器 / 加速 AI 的显卡芯片 |
| Edge device | 边缘设备 | Small computer where AI runs on the spot / 在现场运行 AI 的小型设备 |
| Model, weights, parameters, checkpoint | 模型、权重、参数、检查点 | A learned program; its learned numbers; the file storing them / 学出来的程序；学到的数字；保存它们的文件 |
| FLOPs | 浮点运算次数 | Count of basic arithmetic steps; a measure of compute cost / 基本算术步骤的数量，衡量计算量 |
| YOLOX | — | A family of object-detection models / 一系列目标检测模型 |
| ByteTrack | — | A tracking method that also uses low-confidence boxes / 连低分框也利用的跟踪方法 |
| License (MIT, Apache-2.0, AGPL-3.0) | 许可证 | Legal terms for reuse; MIT/Apache are permissive, AGPL is strict / 使用条款；MIT/Apache 宽松，AGPL 严格 |
| ONNX / ONNX Runtime (ORT) | — | Standard model file format / engine that runs it / 标准模型格式 / 运行它的引擎 |
| Inference / Training | 推理 / 训练 | Using a model / teaching a model / 使用模型 / 教模型 |
| C++ / Python | — | Fast compiled language / convenient scripting language / 编译型快速语言 / 方便的脚本语言 |
| Dataset, benchmark, ground truth | 数据集、基准、真值 | Examples; a shared test; human-made correct answers / 例子；公共考题；人工标注的正确答案 |
| MOTA, IDF1, HOTA | — | Tracking scores (overall; ID consistency; balanced) / 跟踪分数（整体；编号一致性；综合） |
| Data contamination / leakage | 数据污染 / 泄漏 | Testing on data the model trained on / 用训练过的数据来考试 |
| Held-out data | 留出数据 | Data never used in training / 训练中从未用过的数据 |
| Fidelity check | 还原度检查 | Do we reproduce the original's results? / 能否复现原作的结果 |
| CC BY-NC-SA | — | Credit, non-commercial, share-alike / 署名、非商用、相同方式共享 |
| Acceptance criteria | 验收标准 | Pre-written numeric pass/fail rules / 预先写好的数字化通过标准 |
| IoU | 交并比 | Overlap ÷ union of two boxes (1 = identical) / 重叠面积 ÷ 合并面积（1 为完全相同） |
| FPS / latency / p50 / p95 | 帧率 / 延迟 / 中位数 / 95 分位 | Speed measures / 速度指标 |
| RSS | 常驻内存 | RAM actually used / 实际占用的内存 |
| INT8 / FP32 / quantization | 8 位整数 / 32 位浮点 / 量化 | Storing weights with fewer bits / 用更少的位数存权重 |
| Docker, Dockerfile, image, container | — | Packaging tool; recipe; snapshot; running copy / 打包工具；配方；快照；运行中的副本 |
| Linux, Ubuntu, VM | 虚拟机 | Server OS; a Linux version; software-simulated computer / 服务器操作系统；Linux 的一个版本；软件模拟的电脑 |
| Compiler, CMake | 编译器 | Turns source into programs; organises the build / 把源码变程序；组织构建 |
| OpenCV | — | Image-processing library / 图像处理库 |
| SHA-256 | — | A file fingerprint / 文件指纹 |
| JPEG / JSON | — | Photo format / readable data text format / 照片格式 / 可读的数据文本格式 |
| Git, commit | 提交 | Version control; a saved snapshot / 版本管理；一次保存的快照 |
