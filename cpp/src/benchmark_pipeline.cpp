// Phase 4 controlled image-to-track benchmark; baseline detector/tracker reused.
#include "sequence_io.h"
#include "tracker/tracker.h"
#include <opencv2/imgcodecs.hpp>
#include <chrono>
#include <iostream>

namespace {
using Clock = std::chrono::steady_clock;
double elapsed_ms(Clock::time_point start) {
  return std::chrono::duration<double, std::milli>(Clock::now()-start).count();
}
long peak_rss_kib() {
  std::ifstream status("/proc/self/status");
  for (std::string line; std::getline(status, line);) {
    if (line.rfind("VmHWM:", 0) == 0) {
      return std::stol(line.substr(6));
    }
  }
  throw std::runtime_error("VmHWM unavailable");
}
}  // namespace

int main(int argc, char** argv) try {
  auto args = vl::arguments(argc, argv);
  vl::Sequence sequence(vl::arg(args, "--sequence"));
  const int warmup = std::stoi(vl::arg(args, "--warmup", "50"));
  const int measured = std::stoi(vl::arg(args, "--frames", "100"));
  if (warmup < 50 || measured < 1 || warmup+measured > sequence.frames) {
    throw std::runtime_error("invalid benchmark frame range");
  }
  cv::setNumThreads(1);
  vl::DetectorConfig config;
  config.model_path = vl::arg(args, "--model");
  config.threads = std::stoi(vl::arg(args, "--threads"));
  vl::Detector detector(config);
  vl::Tracker tracker(vl::sequence_config(sequence.name));
  std::ofstream output(vl::arg(args, "--out"));
  if (!output) throw std::runtime_error("cannot open timing output");
  output << "frame,decode_ms,preprocess_ms,inference_ms,postprocess_ms,tracking_ms,end_to_end_ms,kept_tracks\n";
  output.precision(12);
  int total_tracks = 0;
  for (int frame = 1; frame <= warmup+measured; ++frame) {
    auto begin = Clock::now();
    auto image = cv::imread(sequence.image(frame));
    if (image.empty()) throw std::runtime_error("unreadable frame");
    double decode = elapsed_ms(begin);
    vl::StageTimes stages;
    auto detections = detector.detect(image, &stages);
    auto track_start = Clock::now();
    int kept = 0;
    if (!detections.empty()) {
      for (const auto& track : tracker.update(detections)) {
        auto box = track->tlwh();
        if (box[2]*box[3] > 100 && box[2]/box[3] <= 1.6) ++kept;
      }
    }
    double tracking = elapsed_ms(track_start);
    double end_to_end = elapsed_ms(begin);
    total_tracks += kept;
    if (frame > warmup) {
      output << frame << ',' << decode << ',' << stages.preprocess_ms << ','
             << stages.inference_ms << ',' << stages.postprocess_ms << ','
             << tracking << ',' << end_to_end << ',' << kept << '\n';
    }
  }
  std::cout << "{\"warmup\":" << warmup << ",\"measured\":" << measured
            << ",\"threads\":" << config.threads << ",\"peak_rss_kib\":"
            << peak_rss_kib() << ",\"total_tracks_including_warmup\":" << total_tracks
            << ",\"opencv_threads\":" << cv::getNumThreads();
  std::ifstream quota_file("/sys/fs/cgroup/cpu.max");
  std::string quota;
  if (!std::getline(quota_file, quota)) throw std::runtime_error("CPU quota unavailable");
  std::cout << ",\"cpu_max\":\"" << quota
            << "\",\"input_height\":608,\"input_width\":1088}" << std::endl;
  return 0;
} catch (const std::exception& error) {
  std::cerr << error.what() << '\n';
  return 1;
}
