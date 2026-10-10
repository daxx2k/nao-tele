#pragma once
#include <array>
#include <cmath>
struct DriveInput {
    bool ready=false;
    static float deadzone(float x){return std::abs(x)<.15f?0.f:std::copysign((std::abs(x)-.15f)/.85f,x);}
    // Choose the dominant right-stick axis: unintended cross-axis input must not
    // start a height adjustment while the user is turning.
    static float turnAxis(float rx,float ry){float x=deadzone(rx),y=deadzone(ry);return std::abs(x)>=std::abs(y)?x:0.f;}
    static float heightAxis(float rx,float ry){float x=deadzone(rx),y=deadzone(ry);return std::abs(y)>std::abs(x)?y:0.f;}
    std::array<float,3> update(bool armed,bool active,float lx,float ly,float rx,float ry=0.f){
        if(!armed||!active){ready=false;return {0,0,0};}
        float x=deadzone(lx),y=deadzone(ly),turn=turnAxis(rx,ry);
        if(x==0&&y==0&&turn==0&&heightAxis(rx,ry)==0)ready=true;
        if(!ready)return {0,0,0};
        // NAOqi: +X forward, +Y left, +theta counterclockwise (left).
        return {y*.50f,-x*.50f,-turn*.50f};
    }
};
