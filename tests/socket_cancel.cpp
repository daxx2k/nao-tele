#include "../quest/src/main/cpp/socket_io.h"
#include <thread>
#include <cassert>
#include <cstdio>
int main(){
 int listener=socket(AF_INET,SOCK_STREAM,0);assert(listener>=0);
 sockaddr_in a{};a.sin_family=AF_INET;a.sin_addr.s_addr=htonl(INADDR_LOOPBACK);a.sin_port=0;
 assert(bind(listener,(sockaddr*)&a,sizeof(a))==0&&listen(listener,1)==0);
 socklen_t len=sizeof(a);assert(getsockname(listener,(sockaddr*)&a,&len)==0);
 int clients[2];for(int& s:clients){s=socket(AF_INET,SOCK_STREAM,0);assert(connect(s,(sockaddr*)&a,sizeof(a))==0);}
 std::atomic<bool> running{true};std::thread cancel([&]{std::this_thread::sleep_for(std::chrono::milliseconds(80));running=false;});
 auto began=std::chrono::steady_clock::now();bool stopped=false;
 try{int s=transport::connectTo("127.0.0.1",ntohs(a.sin_port),SOCK_STREAM,5000,&running);close(s);}catch(const std::exception&){stopped=true;}
 cancel.join();auto elapsed=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::steady_clock::now()-began).count();
 for(int s:clients)close(s);close(listener);assert(stopped&&elapsed<750);
 std::printf("PASS cancelled pending connect in %lld ms\n",(long long)elapsed);
}
