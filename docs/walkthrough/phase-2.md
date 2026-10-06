# Phase 2 walkthrough — writing the detector in C++

# 第 2 阶段讲解：用 C++ 写检测器

*English first, then Chinese. Terms explained in [Phase 0](phase-0.md) and
[Phase 1](phase-1.md) are not repeated.*

*先英文后中文。[第 0 阶段](phase-0.md)和[第 1 阶段](phase-1.md)解释过的词不再重复。*

---

## 1. The goal / 目标

In Phase 1 we turned the model into an ONNX file. A model file alone does
nothing: some program has to prepare each image, hand it to the model, and turn
the 13,566 × 6 numbers that come out into a short list of boxes. In Phase 2 we
wrote that program in C++, the language real edge products use, and proved it
gives the same boxes as the authors' Python code.

第 1 阶段我们把模型转成了 ONNX 文件。但光有模型文件什么也做不了：需要一个程序来准备每张图片、交给模型，再把模型吐出来的 13,566 × 6 个数字整理成一份简短的框列表。第 2 阶段我们用 C++ 写了这个程序（真正的边缘产品就用这种语言），并证明它画出的框和作者的 Python 代码一样。

---

## 2. The three steps around the model / 模型前后的三个步骤

**Step 1: preprocessing.** Same as Phase 1 explained (letterbox, normalise),
now written in C++. One detail: images are stored as **BGR** (blue, green, red
order, OpenCV's habit) but the model expects **RGB**, so the code swaps the
order. Computer images are stored as **pixels** (tiny coloured dots), each
colour channel a number from 0 to 255.

**第 1 步：预处理。** 和第 1 阶段讲的一样（加边框、归一化），现在用 C++ 写。有一个细节：OpenCV 习惯按 **BGR**（蓝、绿、红）的顺序存图片，而模型要的是 **RGB** 顺序，所以代码要把顺序调过来。电脑里的图片由**像素**（一个个彩色小点）组成，每个颜色通道是 0 到 255 之间的一个数。

**Step 2: inference.** The C++ code creates an ONNX Runtime **session** (the
loaded, ready-to-run model) and calls `Run`. We can choose how many
**threads** it uses. A thread is one line of work a CPU core can carry out, so
more threads means more cores working on one image at once. This run used 1
thread; Phase 4 will compare 1, 2 and 4.

**第 2 步：推理。** C++ 代码先建一个 ONNX Runtime **会话**（session，即已经加载好、随时可以运行的模型），再调用 `Run`。我们可以指定它用几个**线程**。线程就是 CPU 核心能执行的一条工作线，线程越多，同时处理一张图的核心就越多。这次用的是 1 个线程，第 4 阶段会比较 1、2、4 个线程。

**Step 3: postprocessing.** For each of the 13,566 anchors:
(a) multiply objectness by class score; skip the anchor if the result is below
0.01; (b) **decode** the 4 box numbers into a real rectangle (centre = grid
position plus offset, times stride; width and height = e^value × stride, where
*e* ≈ 2.718 and e^x is the **exponential function**); (c) run **NMS** to
delete duplicates: sort boxes by score, keep the best, delete any other box
overlapping it with IoU above 0.7, repeat. Finally, scale boxes back from the
608 × 1088 model image to the original photo size.

**第 3 步：后处理。** 对 13,566 个锚点逐个处理：(a) 物体性分数乘以类别分数，结果低于 0.01 就跳过；(b) 把 4 个框数值**解码**成真正的矩形（中心 = 网格位置加偏移，再乘步长；宽和高 = e 的该数值次方乘以步长，*e* ≈ 2.718，e^x 叫**指数函数**）；(c) 用 **NMS** 删掉重复的框：按分数排序，留下最好的，删掉和它 IoU 超过 0.7 的其他框，如此重复。最后把框从 608 × 1088 的模型图片尺寸换算回原照片的尺寸。

The thresholds 0.01 and 0.7 are not our choice: they are the defaults in
ByteTrack's own evaluation script, and copying them is what lets us compare with
the published results later.

0.01 和 0.7 这两个门槛不是我们定的，而是 ByteTrack 自己评测脚本里的默认值。照搬它们，之后才能和官方公布的结果比较。

---

## 3. How the code is organised / 代码是怎么组织的

C++ code is usually split into a **header** file (`.h`: a list of what
exists, like a table of contents) and a **source** file (`.cpp`: the actual
instructions). `detector.h` / `detector.cpp` hold a reusable `Detector`
**class** (a bundle of data plus the functions that work on it).
`detect_frames.cpp` is a small **command-line tool** (a program run by typing
a command, not by clicking) that runs the detector on a list of images and saves
the boxes as JSON. CMake compiles the detector into a **library** (reusable
compiled code) so Phase 3's tracker program can use the same detector.

C++ 代码通常分成**头文件**（`.h`，列出有哪些东西，像目录）和**源文件**（`.cpp`，具体的执行指令）。`detector.h` / `detector.cpp` 里是一个可重复使用的 `Detector` **类**（把数据和处理这些数据的函数打包在一起）。`detect_frames.cpp` 是一个小的**命令行工具**（敲命令运行、而不是点鼠标运行的程序），它对一串图片运行检测器，把框存成 JSON。CMake 把检测器编译成一个**库**（可重复使用的、编译好的代码），这样第 3 阶段的跟踪程序也能用同一个检测器。

---

## 4. The check / 检查

We ran both versions on the same 20 frames as Phase 1. The **reference**
(the trusted version we compare against) is ByteTrack's own Python code. Then
each Python box was paired with its closest C++ box. The pre-set rule: same
number of boxes on every frame, every pair overlapping with IoU ≥ 0.99, and
scores within 0.001.

我们用和第 1 阶段相同的 20 帧画面跑两个版本。**参照**（我们信任、拿来对比的版本）是 ByteTrack 自己的 Python 代码。然后把每个 Python 框和最接近的 C++ 框配成一对。预先定的规则是：每帧框的数量相同；每一对的 IoU ≥ 0.99；分数相差不超过 0.001。

Result: both models passed comfortably. All 1,516 nano boxes and all 1,166
tiny boxes matched. The worst pair still overlapped 99.998%, and scores differed
by at most 0.000005. This holds even though the two sides use different OpenCV
versions (4.10 vs 4.6) and different decimal precision (Python's 64-bit vs our
32-bit). That was a real risk, because image resizing is done by OpenCV and
could differ by one brightness step between versions.

结果：两个模型都轻松通过。nano 的 1,516 个框、tiny 的 1,166 个框全部配对成功。最差的一对重合度仍有 99.998%，分数最多差 0.000005。要知道两边用的 OpenCV 版本不同（4.10 和 4.6），小数精度也不同（Python 用 64 位，我们用 32 位），所以这个结果并不是理所当然的：缩放图片是 OpenCV 做的，不同版本可能差一个亮度等级。

We also drew the boxes on one frame to look with our own eyes
(`results/phase-2/sample-nano.jpg`). Numbers can all match while both sides are
wrong in the same way; a picture catches that kind of shared mistake. The boxes
sit on people. But this frame is from MOT17, which the model trained on, so a
good picture here proves little about accuracy.

我们还在一帧画面上把框画出来，亲眼看一看（`results/phase-2/sample-nano.jpg`）。数字可能全部对得上，但两边错得一模一样；看图能发现这种「一起错」的情况。图里的框确实框在人身上。不过这帧来自 MOT17，模型训练时见过，所以图好看并不能说明准确度。

---

## 5. A first glimpse of speed / 速度的初步印象

While checking, the program also timed each step (1 thread, not a proper
benchmark). Nano takes about 77 **ms** (milliseconds, thousandths of a second)
per frame for inference, which is about 13 frames per second on one core. Tiny
takes about 304 ms. Preprocessing and postprocessing together cost under 2 ms.
So the model itself is nearly all the cost, which tells us where Phase 4 should
look.

检查过程中，程序顺便记录了每一步的耗时（1 个线程，不算正式测速）。nano 每帧推理约 77 **毫秒**（ms，千分之一秒），相当于用一个核心每秒处理约 13 帧；tiny 约 304 毫秒。预处理和后处理加起来不到 2 毫秒。可见几乎全部时间都花在模型本身，这就告诉我们第 4 阶段该重点看哪里。

---

## 6. What comes next / 下一步

Phase 3 adds the tracker: ByteTrack's matching logic, rewritten in C++, which
links boxes across frames into tracks with IDs. Then we score it on all MOT17
training frames and compare with the published numbers.

第 3 阶段加上跟踪器：把 ByteTrack 的匹配逻辑用 C++ 重写，把各帧的框连成带编号的轨迹。然后在全部 MOT17 训练帧上打分，并和官方公布的数字比较。

---

## Terms / 术语表

| Term | 中文 | One-line meaning / 一句话解释 |
|---|---|---|
| Pixel | 像素 | One coloured dot of an image / 图片里的一个彩色小点 |
| BGR / RGB | — | Colour channel orders (blue-green-red / red-green-blue) / 颜色通道的排列顺序 |
| Session | 会话 | A loaded model ready to run / 加载好、随时可以运行的模型 |
| Thread | 线程 | One line of work a CPU core runs / CPU 核心执行的一条工作线 |
| Exponential function (e^x) | 指数函数 | e ≈ 2.718 raised to a power; used to decode box size / e 的 x 次方，用来解码框的大小 |
| Header / source file | 头文件 / 源文件 | Table of contents / actual instructions / 目录 / 具体指令 |
| Class | 类 | Data bundled with the functions that use it / 数据和处理它的函数打包在一起 |
| Command-line tool | 命令行工具 | Program run by typing a command / 敲命令运行的程序 |
| Library | 库 | Reusable compiled code / 可重复使用的编译好的代码 |
| Reference | 参照 | The trusted version you compare against / 拿来对比的可信版本 |
| ms (millisecond) | 毫秒 | 1/1000 of a second / 千分之一秒 |
