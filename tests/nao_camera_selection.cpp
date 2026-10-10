#include "../quest/src/main/cpp/network.h"
#include <cassert>
#include <cstdio>
// This test never starts audio; provide its unused link dependency.
void Network::audioLoop(){}
int main(){
 Network network("127.0.0.1","test-camera-selection");
 assert(network.topStreaming&&!network.bottomStreaming);
 assert(network.cameraFrameRate(0)==30&&network.cameraFrameRate(1)==0);
 network.connected=true;network.armed=true;unsigned generation=network.generation;
 network.setCameraStreaming(1,true);
 assert(network.topStreaming&&network.bottomStreaming);
 assert(network.cameraFrameRate(0)==5&&network.cameraFrameRate(1)==5);
 network.setCameraStreaming(0,true);
 assert(network.topStreaming&&network.bottomStreaming);
 network.setCameraStreaming(0,false);
 assert(!network.topStreaming&&network.bottomStreaming);
 assert(network.cameraFrameRate(1)==30);
 network.setCameraStreaming(1,false);assert(!network.topStreaming&&!network.bottomStreaming);
 assert(network.connected&&network.armed&&network.generation==generation);
 std::puts("PASS NAO adaptive single/dual camera rate without control-session changes");
}
