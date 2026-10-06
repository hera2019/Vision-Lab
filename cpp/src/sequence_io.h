#pragma once
#include "detector.h"
#include <filesystem>
#include <fstream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <vector>
namespace vl {
inline std::map<std::string,std::string> arguments(int argc,char** argv) {
  if (argc%2==0) throw std::runtime_error("arguments must be --key value pairs");
  std::map<std::string,std::string> a;
  for(int i=1;i<argc;i+=2) a[argv[i]]=argv[i+1]; return a;
}
inline std::string arg(const std::map<std::string,std::string>& a,
                       const std::string& k,const std::string& fallback="") {
  auto it=a.find(k); if(it!=a.end()) return it->second;
  if(!fallback.empty()) return fallback; throw std::runtime_error("missing "+k);
}
struct Sequence {
  std::string name, root, image_dir, extension;
  int frames, width, height, fps;
  explicit Sequence(const std::string& path) : root(path) {
    std::ifstream in(path+"/seqinfo.ini");
    if(!in) throw std::runtime_error("cannot open seqinfo.ini: "+path);
    std::map<std::string,std::string> c;
    for(std::string s;std::getline(in,s);) {
      if(!s.empty() && s.back()=='\r') s.pop_back();
      auto p=s.find('='); if(p!=s.npos) c[s.substr(0,p)]=s.substr(p+1);
    }
    name=c.at("name"); image_dir=c.at("imDir"); extension=c.at("imExt");
    frames=std::stoi(c.at("seqLength")); width=std::stoi(c.at("imWidth"));
    height=std::stoi(c.at("imHeight")); fps=std::stoi(c.at("frameRate"));
  }
  std::string image(int frame) const {
    char number[32]; std::snprintf(number,sizeof(number),"%06d",frame);
    return root+"/"+image_dir+"/"+number+extension;
  }
};
inline std::vector<std::vector<Detection>> read_cache(const std::string& path,int frames) {
  std::ifstream in(path); if(!in) throw std::runtime_error("cannot read "+path);
  std::vector<std::vector<Detection>> ds(frames+1);
  for(std::string s;std::getline(in,s);) {
    for(char& c:s) if(c==',') c=' ';
    std::istringstream row(s); int f,id; Detection d;
    if(!(row>>f>>id>>d.x1>>d.y1>>d.x2>>d.y2>>d.score) || f<1 || f>frames)
      throw std::runtime_error("invalid cache row in "+path);
    ds[f].push_back(d);
  }
  return ds;
}
}  // namespace vl
