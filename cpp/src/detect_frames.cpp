// Runs the detector on a list of image files and writes detections as JSON.
//
//   detect_frames --model M.onnx --frames list.txt --out dets.json [--threads N]
//
// list.txt holds one image path per line. Output boxes are x1, y1, x2, y2,
// score in original-image pixels.
#include "detector.h"

#include <opencv2/imgcodecs.hpp>

#include <cstdio>
#include <fstream>
#include <iostream>
#include <map>
#include <string>
#include <vector>

namespace {

std::map<std::string, std::string> parse_args(int argc, char** argv) {
  std::map<std::string, std::string> args;
  for (int i = 1; i + 1 < argc; i += 2) args[argv[i]] = argv[i + 1];
  return args;
}

std::string get(const std::map<std::string, std::string>& args, const std::string& key,
                const std::string& fallback = "") {
  auto it = args.find(key);
  if (it != args.end()) return it->second;
  if (fallback.empty()) {
    std::cerr << "missing " << key << "\n";
    std::exit(2);
  }
  return fallback;
}

}  // namespace

int main(int argc, char** argv) {
  const auto args = parse_args(argc, argv);
  vl::DetectorConfig config;
  config.model_path = get(args, "--model");
  config.threads = std::stoi(get(args, "--threads", "1"));
  const std::string frames_path = get(args, "--frames");
  const std::string out_path = get(args, "--out");

  std::vector<std::string> frames;
  std::ifstream list(frames_path);
  for (std::string line; std::getline(list, line);) {
    if (!line.empty()) frames.push_back(line);
  }

  vl::Detector detector(config);
  FILE* out = std::fopen(out_path.c_str(), "w");
  if (!out) {
    std::cerr << "cannot write " << out_path << "\n";
    return 1;
  }
  std::fprintf(out, "{\n  \"model\": \"%s\",\n  \"conf_threshold\": %g,\n  \"nms_threshold\": %g,\n"
               "  \"threads\": %d,\n  \"frames\": [\n",
               config.model_path.c_str(), config.conf_threshold, config.nms_threshold, config.threads);
  for (size_t f = 0; f < frames.size(); ++f) {
    const cv::Mat img = cv::imread(frames[f], cv::IMREAD_COLOR);
    if (img.empty()) {
      std::cerr << "cannot read " << frames[f] << "\n";
      return 1;
    }
    vl::StageTimes t;
    const auto dets = detector.detect(img, &t);
    std::fprintf(out, "    {\"frame\": \"%s\", \"times_ms\": [%.3f, %.3f, %.3f], \"detections\": [",
                 frames[f].c_str(), t.preprocess_ms, t.inference_ms, t.postprocess_ms);
    for (size_t i = 0; i < dets.size(); ++i) {
      const auto& d = dets[i];
      std::fprintf(out, "%s[%.9g, %.9g, %.9g, %.9g, %.9g]", i ? ", " : "", d.x1, d.y1, d.x2, d.y2,
                   d.score);
    }
    std::fprintf(out, "]}%s\n", f + 1 < frames.size() ? "," : "");
  }
  std::fprintf(out, "  ]\n}\n");
  std::fclose(out);
  std::cout << "wrote " << frames.size() << " frames to " << out_path << "\n";
  return 0;
}
