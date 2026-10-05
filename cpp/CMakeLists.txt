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
