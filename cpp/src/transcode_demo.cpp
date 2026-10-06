// Artifact-only H.264 encoding through the already installed system OpenCV.
// This never runs a detector or changes tracking data.
#include <opencv2/videoio.hpp>
#include <iostream>
int main(int argc,char** argv) {
  if(argc!=3) {std::cerr<<"usage: transcode_demo input.mp4 output.mp4\n";return 2;}
  cv::VideoCapture input(argv[1]);
  if(!input.isOpened()) return 1;
  cv::Size size(input.get(cv::CAP_PROP_FRAME_WIDTH),input.get(cv::CAP_PROP_FRAME_HEIGHT));
  double fps=input.get(cv::CAP_PROP_FPS);
  cv::VideoWriter output(argv[2],cv::VideoWriter::fourcc('a','v','c','1'),fps,size);
  if(!output.isOpened()) {std::cerr<<"H.264 encoder unavailable\n";return 1;}
  cv::Mat image;int frames=0;
  while(input.read(image)) {output.write(image);++frames;}
  output.release(); input.release();
  cv::VideoCapture verify(argv[2]);int decoded=0;
  while(verify.read(image)) {
    if(image.size()!=size) return 1;
    ++decoded;
  }
  if(!frames || frames!=decoded) return 1;
  std::cout<<"H.264 verified: "<<decoded<<" frames, "<<fps<<" fps\n";
  return 0;
}
