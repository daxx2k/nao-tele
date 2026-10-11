#pragma once
#include <array>
#include "dashboard_theme.h"
namespace nao_led_avatar {
constexpr int width=1024,height=1536;
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
