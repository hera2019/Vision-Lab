#include "sequence_io.h"
#include "tracker/tracker.h"
#include <opencv2/imgcodecs.hpp>
#include <chrono>
#include <iomanip>
#include <iostream>
int main(int argc,char** argv) try {
  auto a=vl::arguments(argc,argv); vl::Sequence seq(vl::arg(a,"--sequence"));
  std::string path=vl::arg(a,"--out"); std::filesystem::create_directories(std::filesystem::path(path).parent_path());
  std::ofstream out(path), timing(path+".timing.csv");
  if(!out||!timing) throw std::runtime_error("cannot create output");
  int threads=std::stoi(vl::arg(a,"--threads","1"));
  timing<<"frame,threads,preprocess_ms,inference_ms,postprocess_ms,tracking_ms\n";
  std::unique_ptr<vl::Detector> detector;
  std::vector<std::vector<vl::Detection>> cache;
  if(a.count("--cache")) cache=vl::read_cache(a.at("--cache"),seq.frames);
  else {vl::DetectorConfig c;c.model_path=vl::arg(a,"--model");c.threads=threads;detector=std::make_unique<vl::Detector>(c);}
  vl::Tracker tracker(vl::sequence_config(seq.name));
  int limit=std::min(seq.frames,std::stoi(vl::arg(a,"--limit",std::to_string(seq.frames))));
  for(int f=1;f<=limit;++f) {
    std::vector<vl::Detection> ds; vl::StageTimes dt;
    if(detector) {
      auto img=cv::imread(seq.image(f)); if(img.empty()) throw std::runtime_error("unreadable image");
      ds=detector->detect(img,&dt);
    } else ds=cache[f];
    auto begin=std::chrono::steady_clock::now();
    if(!ds.empty()) for(auto& t:tracker.update(ds)) {
      auto b=t->tlwh(); if(b[2]*b[3]<=100 || b[2]/b[3]>1.6) continue;
      out<<f<<','<<t->id<<','<<std::fixed<<std::setprecision(1)<<b[0]<<','<<b[1]<<','<<b[2]<<','<<b[3]
         <<','<<std::setprecision(2)<<t->score<<",-1,-1,-1\n";
    }
    double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-begin).count();
    timing<<f<<','<<threads<<','<<dt.preprocess_ms<<','<<dt.inference_ms<<','<<dt.postprocess_ms<<','<<ms<<'\n';
    if(f%500==0) std::cout<<seq.name<<" frame "<<f<<'/'<<limit<<std::endl;
  }
  std::cout<<"wrote tracks: "<<path<<std::endl; return 0;
} catch(const std::exception& e) {std::cerr<<e.what()<<'\n';return 1;}
