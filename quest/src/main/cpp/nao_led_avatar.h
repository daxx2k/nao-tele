#pragma once
#include <array>
#include "dashboard_theme.h"
#include "dashboard_layout.h"
namespace nao_led_avatar {
constexpr int width=1024,height=1536;
constexpr std::array<std::array<float,4>,3> crops{{{{.286f,.008f,.713f,.211f}},{{.125f,.210f,.875f,.395f}},{{.143f,.827f,.883f,.965f}}}};
inline dashboard_layout::Rect imageBox(int zone){
    auto card=dashboard_layout::ledAvatar;auto uv=crops[zone];float w=card.w/3;
    return dashboard_layout::contain({card.x+zone*w+6,card.y+3,w-12,91},int((uv[2]-uv[0])*width),int((uv[3]-uv[1])*height));
}
inline bool contains(dashboard_layout::Rect r,float x,float y){return x>=r.x&&x<r.x+r.w&&y>=r.y&&y<r.y+r.h;}
inline int targetAt(float x,float y){
    for(int zone=0;zone<3;++zone){auto box=imageBox(zone);if(!contains(box,x,y))continue;
        if(zone==1)return 1;
        if(zone==2)return 4;
        auto crop=crops[zone];float u=crop[0]+(x-box.x)/box.w*(crop[2]-crop[0]),v=crop[1]+(y-box.y)/box.h*(crop[3]-crop[1]);
        if(v<.080f)return 3;
        return u<.365f||u>.635f?2:0;
    }
    return -1;
}
inline dashboard_layout::Rect uvBox(int zone,float u,float v,float w,float h){
    auto crop=crops[zone];auto box=imageBox(zone);
    return {box.x+(u-crop[0])*box.w/(crop[2]-crop[0]),box.y+(v-crop[1])*box.h/(crop[3]-crop[1]),w*box.w/(crop[2]-crop[0]),h*box.h/(crop[3]-crop[1])};
}
inline std::array<dashboard_layout::Rect,2> selection(int target){
    if(target==0)return {{uvBox(0,.375f,.093f,.245f,.071f),{}}};
    if(target==1)return {{uvBox(1,.435f,.285f,.130f,.085f),{}}};
    if(target==2)return {{uvBox(0,.289f,.084f,.054f,.091f),uvBox(0,.658f,.084f,.054f,.091f)}};
    if(target==3)return {{uvBox(0,.433f,.009f,.135f,.060f),{}}};
    return {{uvBox(2,.198f,.835f,.185f,.080f),uvBox(2,.621f,.835f,.185f,.080f)}};
}
// Match the Appearance selectors: eyes/chest/feet RGB; ears blue and head white intensity.
inline std::array<dashboard_theme::Color,5> colours(const std::array<int,5>& swatches){
    const unsigned rgbColours[]={0xffffff,0x4388ff,0x46f0aa,0xff5050,0xffb020,0xa050ff,0};
    const float intensity[]={0,.15f,.30f,.50f,.70f,.85f,1};
    std::array<dashboard_theme::Color,5> result{};
    for(int i=0;i<5;++i){int slot=std::max(0,std::min(6,swatches[i]));result[i]=dashboard_theme::rgb(i==2?0x4388ff:i==3?0xffffff:rgbColours[slot]);
        if(i==2||i==3)for(float& v:result[i])v*=intensity[slot];}
    return result;
}
}
