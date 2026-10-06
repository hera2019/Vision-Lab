// ByteTrack Python tracker port. Specification: FoundationVision/ByteTrack
// d1bf019, Copyright (c) 2021 Yifu Zhang, MIT (LICENSE.ByteTrack).
#pragma once
#include "detector.h"
#include <Eigen/Dense>
#include <memory>
#include <vector>

namespace vl {
struct TrackerConfig {
  double track_thresh = 0.6, match_thresh = 0.9;
  int track_buffer = 30, frame_rate = 30;
  bool fuse_score = true;
};
TrackerConfig sequence_config(const std::string& name);
struct Track {
  enum State { New, Tracked, Lost, Removed };
  Eigen::Matrix<double, 8, 1> mean;
  Eigen::Matrix<double, 8, 8> covariance;
  Eigen::Vector4d initial;
  double score;
  int id = 0, frame = 0, start = 0;
  State state = New;
  bool activated = false;
  Eigen::Vector4d tlwh() const;
  Eigen::Vector4d tlbr() const;
};
class Tracker {
 public:
  explicit Tracker(TrackerConfig config = {}) : config_(config) {}
  // Caller skips empty-detection frames, matching mot_evaluator.evaluate().
  std::vector<std::shared_ptr<Track>> update(const std::vector<Detection>& detections);
 private:
  TrackerConfig config_;
  int frame_ = 0, next_id_ = 0;
  std::vector<std::shared_ptr<Track>> tracked_, lost_, removed_;
};
}  // namespace vl
