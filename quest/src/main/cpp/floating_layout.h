#pragma once
#include "dashboard_layout.h"
#include "panel_anchor.h"
#include <array>
#include <limits>
namespace floating_layout {
using dashboard_layout::Rect;
constexpr int count=10;
constexpr Rect groupCard(int g){return {dashboard_layout::x[g],dashboard_layout::groupY[g],dashboard_layout::width[g],dashboard_layout::groupHeight[g]};}
constexpr std::array<Rect,count> cards{{dashboard_layout::visionPanel,dashboard_layout::comparison,dashboard_layout::temperatures,groupCard(4),groupCard(0),groupCard(1),groupCard(6),{20,0,1360,56},{20,958,1360,102},groupCard(2)}};
inline XrPosef initial(int i){auto r=cards.at(i);return {{0,0,0,1},{(r.x+r.w*.5f)/1400.f-.5f,(.5f-(r.y+r.h*.5f)/1060.f)*1060.f/1400.f,0}};}
inline void migrateDefault(int i,XrPosef& p,float scale){
    float oldCentre=i==0?432.f:i==5?502.f:i==6?727.f:i==9?878.f:-1.f;
    if(oldCentre<0)return;
    if(std::abs(p.position.x-((i==0?710.f:1170.f)/1400.f-.5f))<1e-5f&&std::abs(p.position.y-(530.f-oldCentre)/1400.f)<1e-5f&&std::abs(p.position.z)<1e-5f&&std::abs(p.orientation.x)+std::abs(p.orientation.y)+std::abs(p.orientation.z)<1e-5f&&std::abs(std::abs(p.orientation.w)-1)<1e-5f&&std::abs(scale-1)<1e-5f)p=initial(i);
}
// Positions are stored in workspace-width units so global resizing keeps the arrangement.
inline XrPosef world(XrPosef root,XrPosef relative,float width){relative.position.x*=width;relative.position.y*=width;relative.position.z*=width;return panel_anchor::compose(root,relative);}
inline XrPosef relative(XrPosef root,XrPosef world,float width){auto p=panel_anchor::compose(panel_anchor::inverse(root),world);p.position.x/=width;p.position.y/=width;p.position.z/=width;return p;}
inline bool valid(XrPosef& p){float q=p.orientation.x*p.orientation.x+p.orientation.y*p.orientation.y+p.orientation.z*p.orientation.z+p.orientation.w*p.orientation.w;if(!std::isfinite(q)||q<.01f)return false;for(float v:{p.position.x,p.position.y,p.position.z})if(!std::isfinite(v)||std::abs(v)>10)return false;float k=1/std::sqrt(q);p.orientation.x*=k;p.orientation.y*=k;p.orientation.z*=k;p.orientation.w*=k;return true;}
inline float distance(XrPosef ray,XrPosef panel){auto r=panel_anchor::compose(panel_anchor::inverse(panel),ray);auto d=panel_anchor::rotate(r.orientation,{0,0,-1});return d.z<-.001f?-r.position.z/d.z:std::numeric_limits<float>::infinity();}
}
