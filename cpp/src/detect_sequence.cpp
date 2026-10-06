#include "sequence_io.h"
#include <opencv2/imgcodecs.hpp>
#include <iostream>
int main(int argc,char** argv) try {
  auto a=vl::arguments(argc,argv); vl::Sequence seq(vl::arg(a,"--sequence"));
  vl::DetectorConfig c; c.model_path=vl::arg(a,"--model");
  c.threads=std::stoi(vl::arg(a,"--threads","1"));
  int limit=std::min(seq.frames,std::stoi(vl::arg(a,"--limit",std::to_string(seq.frames))));
  std::string path=vl::arg(a,"--out"); std::filesystem::create_directories(std::filesystem::path(path).parent_path());
  std::ofstream out(path), timing(path+".timing.csv");
  if(!out||!timing) throw std::runtime_error("cannot create output");
  out.precision(9); timing<<"frame,threads,preprocess_ms,inference_ms,postprocess_ms\n";
  vl::Detector detector(c);
  for(int f=1;f<=limit;++f) {
    auto img=cv::imread(seq.image(f)); if(img.empty()) throw std::runtime_error("unreadable frame "+std::to_string(f));
    vl::StageTimes t; auto ds=detector.detect(img,&t);
    for(auto& d:ds) out<<f<<",-1,"<<d.x1<<','<<d.y1<<','<<d.x2<<','<<d.y2<<','<<d.score<<'\n';
    timing<<f<<','<<c.threads<<','<<t.preprocess_ms<<','<<t.inference_ms<<','<<t.postprocess_ms<<'\n';
    if(f%500==0) std::cout<<seq.name<<" frame "<<f<<'/'<<limit<<std::endl;
  }
  std::cout<<"wrote "<<limit<<" frames: "<<path<<std::endl;
  return 0;
} catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
