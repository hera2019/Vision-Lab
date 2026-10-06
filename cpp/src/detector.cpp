#include "detector.h"

#include <opencv2/imgproc.hpp>

#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <stdexcept>

namespace vl {
namespace {

// Normalisation used by ByteTrack's tracking tools, in RGB order.
constexpr std::array<float, 3> kMean = {0.485f, 0.456f, 0.406f};
constexpr std::array<float, 3> kStd = {0.229f, 0.224f, 0.225f};
constexpr float kPadValue = 114.0f;
constexpr std::array<int, 3> kStrides = {8, 16, 32};
constexpr int kOutputColumns = 6;  // x, y, w, h, objectness, class score

using Clock = std::chrono::steady_clock;

double ms_since(Clock::time_point start) {
  return std::chrono::duration<double, std::milli>(Clock::now() - start).count();
}

float iou(const Detection& a, const Detection& b) {
  const float ix1 = std::max(a.x1, b.x1), iy1 = std::max(a.y1, b.y1);
  const float ix2 = std::min(a.x2, b.x2), iy2 = std::min(a.y2, b.y2);
  const float inter = std::max(0.0f, ix2 - ix1) * std::max(0.0f, iy2 - iy1);
  const float area_a = (a.x2 - a.x1) * (a.y2 - a.y1);
  const float area_b = (b.x2 - b.x1) * (b.y2 - b.y1);
  return inter / (area_a + area_b - inter);
}

}  // namespace

Detector::Detector(const DetectorConfig& config)
    : config_(config), env_(ORT_LOGGING_LEVEL_WARNING, "vision_lab") {
  Ort::SessionOptions options;
  options.SetIntraOpNumThreads(config_.threads);
  options.SetInterOpNumThreads(1);
  options.SetExecutionMode(ExecutionMode::ORT_SEQUENTIAL);
  options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);
  session_ = Ort::Session(env_, config_.model_path.c_str(), options);

  input_.resize(3 * static_cast<size_t>(config_.input_h) * config_.input_w);
  // Anchor order matches YOLOXHead: stride levels in turn, each row-major (y outer, x inner).
  for (int s : kStrides) {
    const int hs = config_.input_h / s, ws = config_.input_w / s;
    for (int y = 0; y < hs; ++y) {
      for (int x = 0; x < ws; ++x) {
        grid_x_.push_back(static_cast<float>(x));
        grid_y_.push_back(static_cast<float>(y));
        stride_.push_back(static_cast<float>(s));
      }
    }
  }
}

double Detector::preprocess(const cv::Mat& bgr) {
  const int h = config_.input_h, w = config_.input_w;
  const double r = std::min(static_cast<double>(h) / bgr.rows, static_cast<double>(w) / bgr.cols);
  const int rh = static_cast<int>(bgr.rows * r), rw = static_cast<int>(bgr.cols * r);
  cv::Mat resized;
  cv::resize(bgr, resized, cv::Size(rw, rh), 0, 0, cv::INTER_LINEAR);

  const size_t plane = static_cast<size_t>(h) * w;
  // Output channel c is RGB; source pixel is BGR, so it reads index 2 - c.
  for (int c = 0; c < 3; ++c) {
    const float pad = (kPadValue / 255.0f - kMean[c]) / kStd[c];
    float* dst = input_.data() + c * plane;
    for (int y = 0; y < h; ++y) {
      const uchar* src = y < rh ? resized.ptr<uchar>(y) : nullptr;
      for (int x = 0; x < w; ++x) {
        dst[y * w + x] = (src && x < rw)
            ? (src[x * 3 + (2 - c)] / 255.0f - kMean[c]) / kStd[c]
            : pad;
      }
    }
  }
  return r;
}

std::vector<Detection> Detector::postprocess(const float* out, double ratio) const {
  std::vector<Detection> candidates;
  const size_t n = stride_.size();
  for (size_t i = 0; i < n; ++i) {
    const float* row = out + i * kOutputColumns;
    const float score = row[4] * row[5];
    if (score < config_.conf_threshold) continue;
    const float cx = (row[0] + grid_x_[i]) * stride_[i];
    const float cy = (row[1] + grid_y_[i]) * stride_[i];
    const float bw = std::exp(row[2]) * stride_[i];
    const float bh = std::exp(row[3]) * stride_[i];
    candidates.push_back({cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2, score});
  }
  std::vector<Detection> kept = nms(std::move(candidates), config_.nms_threshold);
  const float inv = static_cast<float>(1.0 / ratio);
  for (Detection& d : kept) {
    d.x1 *= inv; d.y1 *= inv; d.x2 *= inv; d.y2 *= inv;
  }
  return kept;
}

std::vector<Detection> Detector::detect(const cv::Mat& bgr, StageTimes* times) {
  if (bgr.empty() || bgr.type() != CV_8UC3) throw std::invalid_argument("expected 8-bit BGR image");

  auto t0 = Clock::now();
  const double ratio = preprocess(bgr);
  const double pre_ms = ms_since(t0);

  t0 = Clock::now();
  const std::array<int64_t, 4> shape = {1, 3, config_.input_h, config_.input_w};
  Ort::MemoryInfo mem = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
  Ort::Value input = Ort::Value::CreateTensor<float>(mem, input_.data(), input_.size(),
                                                     shape.data(), shape.size());
  const char* in_names[] = {"images"};
  const char* out_names[] = {"output"};
  auto outputs = session_.Run(Ort::RunOptions{nullptr}, in_names, &input, 1, out_names, 1);
  const double infer_ms = ms_since(t0);

  const auto out_shape = outputs[0].GetTensorTypeAndShapeInfo().GetShape();
  if (out_shape.size() != 3 || static_cast<size_t>(out_shape[1]) != stride_.size() ||
      out_shape[2] != kOutputColumns) {
    throw std::runtime_error("unexpected model output shape");
  }

  t0 = Clock::now();
  std::vector<Detection> dets = postprocess(outputs[0].GetTensorData<float>(), ratio);
  const double post_ms = ms_since(t0);

  if (times) *times = {pre_ms, infer_ms, post_ms};
  return dets;
}

std::vector<Detection> nms(std::vector<Detection> boxes, float iou_threshold) {
  std::stable_sort(boxes.begin(), boxes.end(),
                   [](const Detection& a, const Detection& b) { return a.score > b.score; });
  std::vector<Detection> kept;
  std::vector<bool> removed(boxes.size(), false);
  for (size_t i = 0; i < boxes.size(); ++i) {
    if (removed[i]) continue;
    kept.push_back(boxes[i]);
    for (size_t j = i + 1; j < boxes.size(); ++j) {
      if (!removed[j] && iou(boxes[i], boxes[j]) > iou_threshold) removed[j] = true;
    }
  }
  return kept;
}

}  // namespace vl
