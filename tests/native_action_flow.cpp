#include "../quest/src/main/cpp/native_action_flow.h"
#include <cassert>
#include <cstdio>
int main(){NativeActionFlow f;
 f.begin(true,4,2,0);assert(f.tick(2,3,false,true,true,"ready",true,1)==f.None);
 assert(f.tick(2,4,true,true,true,"playing",true,2)==f.None);
 assert(f.tick(2,4,false,false,true,"complete",true,3)==f.None);
 assert(f.tick(2,4,false,true,true,"complete",true,4)==f.Resume&&!f.waiting);
 f.begin(false,5,2,5);assert(f.tick(2,5,false,false,true,"Sit ready",true,6)==f.None&&!f.waiting);
 for(auto message:{"Preparation failed: motor error","Posture cancelled: STOP"}){f.begin(true,6,2,7);assert(f.tick(2,6,false,true,true,message,true,8)==f.None&&!f.waiting);}
 f.begin(true,6,2,9);assert(f.tick(3,6,false,true,true,"complete",true,10)==f.None&&!f.waiting);
 f.begin(true,6,2,9);assert(f.tick(2,6,true,true,true,"playing",false,10)==f.None&&!f.waiting);
 f.begin(true,6,2,0);assert(f.tick(2,6,true,true,true,"playing",true,46)==f.None&&f.waiting);assert(f.tick(2,6,true,true,true,"playing",true,121)==f.Stop);
 std::puts("PASS standing resume, seated pause, failure, cancellation, reconnect and timeout");}
