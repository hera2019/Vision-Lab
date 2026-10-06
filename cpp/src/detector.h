// YOLOX detector on ONNX Runtime (CPU): letterbox preprocessing, inference,
// box decoding and NMS, matching ByteTrack's Python evaluation path.
#pragma once

#include <onnxruntime_cxx_api.h>
#include <opencv2/core.hpp>

#include <string>
#include <vector>

namespace vl {

struct Detection {
  float x1, y1, x2, y2;  // original-image pixel coordinates
  float score;           // objectness * class score
};

struct DetectorConfig {
  std::string model_path;
  int input_h = 608;
  int input_w = 1088;
  float conf_threshold = 0.01f;  // ByteTrack tools/track.py --conf default
  float nms_threshold = 0.7f;    // ByteTrack tools/track.py --nms default
  int threads = 1;               // ONNX Runtime intra-op threads
};

// Wall-clock milliseconds spent in each stage of the last detect() call.
struct StageTimes {
  double preprocess_ms = 0;
  double inference_ms = 0;
  double postprocess_ms = 0;
};

class Detector {
 public:
  explicit Detector(const DetectorConfig& config);
  std::vector<Detection> detect(const cv::Mat& bgr, StageTimes* times = nullptr);

 private:
  // Fills input_ (CHW float32) and returns the resize ratio.
  double preprocess(const cv::Mat& bgr);
  std::vector<Detection> postprocess(const float* out, double ratio) const;

  DetectorConfig config_;
  Ort::Env env_;
  Ort::Session session_{nullptr};
  std::vector<float> input_;
  // Per-anchor grid x, grid y and stride, in the model's output order.
  std::vector<float> grid_x_, grid_y_, stride_;
};

// Greedy NMS on boxes sorted by descending score; suppresses IoU > threshold
// (same rule as torchvision.ops.nms).
std::vector<Detection> nms(std::vector<Detection> boxes, float iou_threshold);

}  // namespace vl
