#include "../quest/src/main/cpp/drive_input.h"
#include <cassert>
#include <cstdio>
int main(){DriveInput d;
 assert(d.update(true,true,1,0,0)==(std::array<float,3>{0,0,0}));
 d.update(true,true,0,0,0);
 auto forward=d.update(true,true,0,1,0);assert(forward[0]>0&&forward[1]==0&&forward[2]==0);
 auto left=d.update(true,true,-1,0,0);assert(left[0]==0&&left[1]>0&&left[2]==0);
 auto turn=d.update(true,true,0,0,1);assert(turn[0]==0&&turn[1]==0&&turn[2]<0);
 assert(forward[0]==.5f&&left[1]==.5f&&turn[2]==-.5f);
 auto noisyTurn=d.update(true,true,0,0,.8f,.25f);
 assert(noisyTurn[2]<0&&DriveInput::heightAxis(.8f,.25f)==0);
 auto crouch=d.update(true,true,0,0,.25f,.8f);
 assert(crouch[2]==0&&DriveInput::heightAxis(.25f,.8f)>0);
 assert(DriveInput::turnAxis(.7f,.7f)>0&&DriveInput::heightAxis(.7f,.7f)==0);
 for(float v=-.14f;v<.15f;v+=.01f)assert(d.update(true,true,v,v,v)==(std::array<float,3>{0,0,0}));
 assert(d.update(false,true,1,1,1)==(std::array<float,3>{0,0,0}));
 std::puts("PASS left XY translation, right X rotation, centred-stick silence and pause");}
