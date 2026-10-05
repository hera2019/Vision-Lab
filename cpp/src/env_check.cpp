// Phase 0 environment check: prints toolchain versions as JSON and exits
// non-zero if ONNX Runtime or OpenCV is not usable.
#include <onnxruntime_cxx_api.h>
#include <opencv2/core.hpp>
#include <opencv2/imgcodecs.hpp>

#include <algorithm>
#include <iostream>
#include <string>
#include <thread>
#include <vector>

int main() {
  const std::string ort_version = Ort::GetVersionString();
  const std::vector<std::string> providers = Ort::GetAvailableProviders();
  const bool has_cpu =
      std::find(providers.begin(), providers.end(), "CPUExecutionProvider") != providers.end();

  Ort::Env env(ORT_LOGGING_LEVEL_WARNING, "env_check");

  cv::Mat img(64, 64, CV_8UC3, cv::Scalar(10, 20, 30));
  std::vector<uchar> buf;
  const bool encoded = cv::imencode(".jpg", img, buf);
  const cv::Mat decoded = encoded ? cv::imdecode(buf, cv::IMREAD_COLOR) : cv::Mat();
  const bool jpeg_ok = !decoded.empty() && decoded.size() == img.size();

  std::cout << "{\n"
            << "  \"onnxruntime_version\": \"" << ort_version << "\",\n"
            << "  \"providers\": [";
  for (size_t i = 0; i < providers.size(); ++i) {
    std::cout << (i ? ", " : "") << '"' << providers[i] << '"';
  }
  std::cout << "],\n"
            << "  \"opencv_version\": \"" << CV_VERSION << "\",\n"
            << "  \"jpeg_roundtrip\": " << (jpeg_ok ? "true" : "false") << ",\n"
            << "  \"hardware_concurrency\": " << std::thread::hardware_concurrency() << "\n"
            << "}\n";

  return (has_cpu && jpeg_ok) ? 0 : 1;
}
