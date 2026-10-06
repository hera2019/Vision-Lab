// ByteTrack Python tracker port; see tracker.h and LICENSE.ByteTrack.
#include "tracker.h"
#include "lapjv.h"

#include <algorithm>
#include <set>
#include <stdexcept>
#include <tuple>

namespace vl {
namespace {

using TrackPtr = std::shared_ptr<Track>;
using TrackList = std::vector<TrackPtr>;
using StateVector = Eigen::Matrix<double, 8, 1>;
using StateCovariance = Eigen::Matrix<double, 8, 8>;

Eigen::Vector4d measurement(const Track& track) {
  auto box = track.tlwh();
  box[0] += box[2] / 2;
  box[1] += box[3] / 2;
  box[2] /= box[3];
  return box;
}

void initiate(Track& track) {
  track.mean.setZero();
  track.mean.head<4>() = measurement(track);
  double height = track.mean[3];
  StateVector deviation;
  deviation << height / 10, height / 10, 1e-2, height / 10,
      height / 16, height / 16, 1e-5, height / 16;
  track.covariance = deviation.array().square().matrix().asDiagonal();
}

void predict(Track& track) {
  if (track.state != Track::Tracked) {
    track.mean[7] = 0;
  }
  double height = track.mean[3];
  StateVector deviation;
  deviation << height / 20, height / 20, 1e-2, height / 20,
      height / 160, height / 160, 1e-5, height / 160;
  StateCovariance motion = StateCovariance::Identity();
  motion.block<4, 4>(0, 4).setIdentity();
  track.mean = (motion * track.mean).eval();
  track.covariance = (motion * track.covariance * motion.transpose()).eval();
  track.covariance.diagonal() += deviation.array().square().matrix();
}

void update_track(Track& track, const Track& detection, int frame) {
  double height = track.mean[3];
  Eigen::Vector4d deviation;
  deviation << height / 20, height / 20, 1e-1, height / 20;
  Eigen::Matrix4d projection = track.covariance.topLeftCorner<4, 4>();
  projection.diagonal() += deviation.array().square().matrix();
  // Cholesky solve, as scipy.linalg.cho_solve in the Python filter.
  Eigen::Matrix<double, 8, 4> gain = projection.llt().solve(
      track.covariance.leftCols<4>().transpose()).transpose();
  track.mean += gain * (measurement(detection) - track.mean.head<4>());
  track.covariance -= (gain * projection * gain.transpose()).eval();
  track.score = detection.score;
  track.frame = frame;
  track.state = Track::Tracked;
  track.activated = true;
}

TrackList joint(const TrackList& first, const TrackList& second) {
  TrackList output = first;
  std::set<int> ids;
  for (const auto& track : first) {
    ids.insert(track->id);
  }
  for (const auto& track : second) {
    if (ids.insert(track->id).second) {
      output.push_back(track);
    }
  }
  return output;
}

TrackList sub(const TrackList& first, const TrackList& second) {
  std::set<int> ids;
  for (const auto& track : second) {
    ids.insert(track->id);
  }
  TrackList output;
  for (const auto& track : first) {
    if (!ids.count(track->id)) {
      output.push_back(track);
    }
  }
  return output;
}

// cython_bbox uses inclusive pixel geometry (+1), unlike detector NMS.
double iou(const Track& first, const Track& second) {
  auto first_box = first.tlbr();
  auto second_box = second.tlbr();
  double width = std::min(first_box[2], second_box[2]) -
      std::max(first_box[0], second_box[0]) + 1;
  double height = std::min(first_box[3], second_box[3]) -
      std::max(first_box[1], second_box[1]) + 1;
  if (width <= 0 || height <= 0) {
    return 0;
  }
  double intersection = width * height;
  return intersection / ((first_box[2] - first_box[0] + 1) *
                         (first_box[3] - first_box[1] + 1) +
                         (second_box[2] - second_box[0] + 1) *
                         (second_box[3] - second_box[1] + 1) - intersection);
}

struct Assignment {
  std::vector<std::pair<int, int>> matches;
  std::vector<int> rows, cols;
};

Assignment associate(const TrackList& tracks, const TrackList& detections,
                     double limit, bool fuse) {
  Assignment output;
  int row_count = tracks.size();
  int column_count = detections.size();
  if (!row_count || !column_count) {
    for (int i = 0; i < row_count; ++i) {
      output.rows.push_back(i);
    }
    for (int j = 0; j < column_count; ++j) {
      output.cols.push_back(j);
    }
    return output;
  }

  // Equivalent to lap.lapjv(extend_cost=True, cost_limit=limit):
  // unmatched row and column each pay limit/2; dummy-to-dummy is zero.
  int size = row_count + column_count;
  std::vector<std::vector<double>> costs(
      size, std::vector<double>(size, limit / 2));
  for (int i = 0; i < row_count; ++i) {
    for (int j = 0; j < column_count; ++j) {
      costs[i][j] = 1 - iou(*tracks[i], *detections[j]) *
          (fuse ? detections[j]->score : 1);
    }
  }
  for (int i = row_count; i < size; ++i) {
    for (int j = column_count; j < size; ++j) {
      costs[i][j] = 0;
    }
  }
  std::vector<double*> row_pointers;
  for (auto& row : costs) {
    row_pointers.push_back(row.data());
  }
  std::vector<int> row_assignment(size), column_assignment(size);
  if (lapjv_internal(size, row_pointers.data(), row_assignment.data(),
                     column_assignment.data()) != 0) {
    throw std::runtime_error("lapjv failed");
  }
  for (int i = 0; i < row_count; ++i) {
    if (row_assignment[i] < column_count) {
      output.matches.emplace_back(i, row_assignment[i]);
    } else {
      output.rows.push_back(i);
    }
  }
  for (int j = 0; j < column_count; ++j) {
    if (column_assignment[j] >= row_count) {
      output.cols.push_back(j);
    }
  }
  return output;
}

TrackList select(const TrackList& list, const std::vector<int>& indexes) {
  TrackList output;
  for (int index : indexes) {
    output.push_back(list[index]);
  }
  return output;
}

}  // namespace

TrackerConfig sequence_config(const std::string& name) {
  TrackerConfig config;
  if (name == "MOT17-05-FRCNN" || name == "MOT17-06-FRCNN") {
    config.track_buffer = 14;
  } else if (name == "MOT17-13-FRCNN" || name == "MOT17-14-FRCNN") {
    config.track_buffer = 25;
  }
  if (name == "MOT17-01-FRCNN" || name == "MOT17-06-FRCNN") {
    config.track_thresh = .65;
  } else if (name == "MOT17-12-FRCNN") {
    config.track_thresh = .7;
  } else if (name == "MOT17-14-FRCNN") {
    config.track_thresh = .67;
  }
  // MOT20 deliberately retains A1 held-out defaults, including fuse_score.
  return config;
}

Eigen::Vector4d Track::tlwh() const {
  if (!id) {
    return initial;
  }
  Eigen::Vector4d box = mean.head<4>();
  box[2] *= box[3];
  box.head<2>() -= box.tail<2>() / 2;
  return box;
}

Eigen::Vector4d Track::tlbr() const {
  auto box = tlwh();
  box.tail<2>() += box.head<2>();
  return box;
}

std::vector<std::shared_ptr<Track>> Tracker::update(
    const std::vector<Detection>& detections) {
  ++frame_;
  TrackList high, low, active, unconfirmed, activated, refound;
  TrackList newly_lost, newly_removed;
  // NumPy compares float32 scores with weak Python scalars in float32.
  // Promoting the score alone to double misclassifies exact threshold values.
  const float threshold = static_cast<float>(config_.track_thresh);
  for (const auto& detection : detections) {
    auto track = std::make_shared<Track>();
    track->initial << detection.x1, detection.y1,
        detection.x2 - detection.x1, detection.y2 - detection.y1;
    track->score = detection.score;
    if (detection.score > threshold) {
      high.push_back(track);
    } else if (detection.score > .1f && detection.score < threshold) {
      low.push_back(track);
    }
  }
  for (const auto& track : tracked_) {
    (track->activated ? active : unconfirmed).push_back(track);
  }

  // First association: active/lost tracks and high-confidence detections.
  auto pool = joint(active, lost_);
  for (auto& track : pool) {
    predict(*track);
  }
  auto first = associate(pool, high, config_.match_thresh, config_.fuse_score);
  for (auto [i, j] : first.matches) {
    bool was_tracked = pool[i]->state == Track::Tracked;
    update_track(*pool[i], *high[j], frame_);
    (was_tracked ? activated : refound).push_back(pool[i]);
  }

  // Second association: only unmatched currently tracked targets may use low scores.
  TrackList remaining;
  for (int i : first.rows) {
    if (pool[i]->state == Track::Tracked) {
      remaining.push_back(pool[i]);
    }
  }
  auto second = associate(remaining, low, .5, false);
  for (auto [i, j] : second.matches) {
    update_track(*remaining[i], *low[j], frame_);
    activated.push_back(remaining[i]);
  }
  for (int i : second.rows) {
    remaining[i]->state = Track::Lost;
    newly_lost.push_back(remaining[i]);
  }

  // Confirm recent tracks, then create new tracks from confident unused boxes.
  auto unused = select(high, first.cols);
  auto confirm = associate(unconfirmed, unused, .7, config_.fuse_score);
  for (auto [i, j] : confirm.matches) {
    update_track(*unconfirmed[i], *unused[j], frame_);
    activated.push_back(unconfirmed[i]);
  }
  for (int i : confirm.rows) {
    unconfirmed[i]->state = Track::Removed;
    newly_removed.push_back(unconfirmed[i]);
  }
  for (int j : confirm.cols) {
    auto track = unused[j];
    if (track->score < static_cast<float>(config_.track_thresh + .1)) {
      continue;
    }
    initiate(*track);
    track->id = ++next_id_;
    track->state = Track::Tracked;
    track->activated = frame_ == 1;
    track->frame = track->start = frame_;
    activated.push_back(track);
  }

  // Expire lost tracks and preserve Python's list-update order.
  int max_lost = static_cast<int>(config_.frame_rate / 30.0 * config_.track_buffer);
  for (auto& track : lost_) {
    if (frame_ - track->frame > max_lost) {
      track->state = Track::Removed;
      newly_removed.push_back(track);
    }
  }
  TrackList keep;
  for (auto& track : tracked_) {
    if (track->state == Track::Tracked) {
      keep.push_back(track);
    }
  }
  tracked_ = joint(joint(keep, activated), refound);
  lost_ = sub(lost_, tracked_);
  lost_.insert(lost_.end(), newly_lost.begin(), newly_lost.end());
  // Preserve Python's one-update delay in removal from lost_.
  lost_ = sub(lost_, removed_);
  removed_.insert(removed_.end(), newly_removed.begin(), newly_removed.end());

  // Remove overlapping active/lost duplicates, retaining the longer-lived track.
  std::set<int> drop_tracked, drop_lost;
  for (size_t i = 0; i < tracked_.size(); ++i) {
    for (size_t j = 0; j < lost_.size(); ++j) {
      if (1 - iou(*tracked_[i], *lost_[j]) < .15) {
        if (tracked_[i]->frame - tracked_[i]->start >
            lost_[j]->frame - lost_[j]->start) {
          drop_lost.insert(j);
        } else {
          drop_tracked.insert(i);
        }
      }
    }
  }
  keep.clear();
  for (size_t i = 0; i < tracked_.size(); ++i) {
    if (!drop_tracked.count(i)) {
      keep.push_back(tracked_[i]);
    }
  }
  tracked_ = keep;
  keep.clear();
  for (size_t j = 0; j < lost_.size(); ++j) {
    if (!drop_lost.count(j)) {
      keep.push_back(lost_[j]);
    }
  }
  lost_ = keep;
  keep.clear();
  for (auto& track : tracked_) {
    if (track->activated) {
      keep.push_back(track);
    }
  }
  return keep;
}

}  // namespace vl
