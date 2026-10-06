cmake_minimum_required(VERSION 3.22)
project(vision_lab CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Ubuntu's per-module OpenCV -dev packages ship headers and libraries but not
# OpenCVConfig.cmake (that comes with the much larger libopencv-dev), so the
# modules are located directly.
find_path(OpenCV_INCLUDE_DIR opencv2/core.hpp PATH_SUFFIXES opencv4 REQUIRED)
set(OpenCV_LIBS)
foreach(module core imgproc imgcodecs)
  find_library(OpenCV_${module}_LIB opencv_${module} REQUIRED)
  list(APPEND OpenCV_LIBS ${OpenCV_${module}_LIB})
endforeach()

set(ONNXRUNTIME_ROOT "$ENV{ONNXRUNTIME_ROOT}" CACHE PATH "ONNX Runtime install prefix")
find_library(ONNXRUNTIME_LIB onnxruntime PATHS "${ONNXRUNTIME_ROOT}/lib" REQUIRED NO_DEFAULT_PATH)
add_library(onnxruntime SHARED IMPORTED)
set_target_properties(onnxruntime PROPERTIES
  IMPORTED_LOCATION "${ONNXRUNTIME_LIB}"
  INTERFACE_INCLUDE_DIRECTORIES "${ONNXRUNTIME_ROOT}/include")

add_executable(env_check src/env_check.cpp)
target_include_directories(env_check PRIVATE ${OpenCV_INCLUDE_DIR})
target_link_libraries(env_check PRIVATE onnxruntime ${OpenCV_LIBS})

add_library(vl_detector STATIC src/detector.cpp)
target_include_directories(vl_detector PUBLIC src ${OpenCV_INCLUDE_DIR})
target_link_libraries(vl_detector PUBLIC onnxruntime ${OpenCV_LIBS})

add_executable(detect_frames src/detect_frames.cpp)
target_link_libraries(detect_frames PRIVATE vl_detector)

# Phase 3 additions; Phase 0-2 detector targets above remain unchanged.
find_package(Eigen3 REQUIRED)
add_library(vl_tracker STATIC src/tracker/tracker.cpp src/tracker/lapjv.cpp)
target_link_libraries(vl_tracker PUBLIC vl_detector Eigen3::Eigen)
add_executable(detect_sequence src/detect_sequence.cpp)
target_link_libraries(detect_sequence PRIVATE vl_detector)
add_executable(track_sequence src/track_sequence.cpp)
target_link_libraries(track_sequence PRIVATE vl_tracker)

# Artifact encoding uses the existing system OpenCV/FFmpeg video backend.
find_library(OpenCV_VIDEOIO_LIB opencv_videoio REQUIRED)
add_executable(transcode_demo src/transcode_demo.cpp)
target_include_directories(transcode_demo PRIVATE ${OpenCV_INCLUDE_DIR})
target_link_libraries(transcode_demo PRIVATE ${OpenCV_VIDEOIO_LIB} ${OpenCV_LIBS})

# Phase 4 additive benchmark; no changes to baseline detector/tracker targets.
add_executable(benchmark_pipeline src/benchmark_pipeline.cpp)
target_link_libraries(benchmark_pipeline PRIVATE vl_tracker)
