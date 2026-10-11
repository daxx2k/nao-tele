#pragma once
#include <string>
struct NativeActionFlow {
    enum Action {None,Resume,Stop};
    bool waiting=false,resumeStanding=false;
    unsigned revision=0,generation=0;
    double deadline=0;
    void cancel(){waiting=false;}
    void begin(bool resume,unsigned next,unsigned connection,double now){waiting=true;resumeStanding=resume;revision=next;generation=connection;deadline=now+120;}
    Action tick(unsigned connection,unsigned observed,bool busy,bool standing,bool fresh,const std::string& message,bool allowed,double now){
        if(!waiting)return None;
        if(connection!=generation||!allowed){cancel();return None;}
        if(now>deadline){cancel();return Stop;}
        if(observed<revision||busy)return None;
        if(message.find("Preparation failed")==0||message.find("cancelled")!=std::string::npos){cancel();return None;}
        if(!resumeStanding){cancel();return None;}
        if(!standing||!fresh)return None;
        cancel();return Resume;
    }
};
