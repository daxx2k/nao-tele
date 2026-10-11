#pragma once
#include <arpa/inet.h>
#include <netinet/tcp.h>
#include <sys/socket.h>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>
#include <cerrno>
#include <stdexcept>
#include <string>
#include <atomic>
#include <chrono>
#include <algorithm>
namespace transport {
inline int connectTo(const std::string& host,int port,int type=SOCK_STREAM,int deadlineMs=1500,const std::atomic<bool>* running=nullptr){
    if(running&&!running->load())throw std::runtime_error("Connection cancelled");
    int s=socket(AF_INET,type,0);if(s<0)throw std::runtime_error("Socket unavailable");
    try{
        sockaddr_in addr{};addr.sin_family=AF_INET;addr.sin_port=htons(port);
        if(inet_pton(AF_INET,host.c_str(),&addr.sin_addr)!=1)throw std::runtime_error("Invalid NAO address: open Connection settings");
        int flags=fcntl(s,F_GETFL,0);
        if(flags<0||fcntl(s,F_SETFL,flags|O_NONBLOCK)<0)throw std::runtime_error("Socket setup failed");
        if(connect(s,(sockaddr*)&addr,sizeof(addr))<0){
            if(errno!=EINPROGRESS)throw std::runtime_error("NAO unreachable: check network and robot service");
            pollfd p{s,POLLOUT,0};int ready=0,error=0;socklen_t size=sizeof(error);
            auto deadline=std::chrono::steady_clock::now()+std::chrono::milliseconds(deadlineMs);
            while(ready==0){
                if(running&&!running->load())throw std::runtime_error("Connection cancelled");
                int remaining=int(std::chrono::duration_cast<std::chrono::milliseconds>(deadline-std::chrono::steady_clock::now()).count());
                if(remaining<=0)break;
                ready=poll(&p,1,std::min(remaining,50));
                if(ready<0&&errno==EINTR)ready=0;
            }
            if(ready<=0||getsockopt(s,SOL_SOCKET,SO_ERROR,&error,&size)<0||error)
                throw std::runtime_error("NAO did not respond: retrying automatically");
        }
        if(fcntl(s,F_SETFL,flags)<0)throw std::runtime_error("Socket setup failed");
        timeval timeout{2,0};setsockopt(s,SOL_SOCKET,SO_RCVTIMEO,&timeout,sizeof(timeout));setsockopt(s,SOL_SOCKET,SO_SNDTIMEO,&timeout,sizeof(timeout));
        int yes=1;if(type==SOCK_STREAM){setsockopt(s,IPPROTO_TCP,TCP_NODELAY,&yes,sizeof(yes));setsockopt(s,SOL_SOCKET,SO_KEEPALIVE,&yes,sizeof(yes));}
        return s;
    }catch(...){close(s);throw;}
}
}
