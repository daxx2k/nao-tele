#include "../quest/src/main/cpp/nao_led_avatar.h"
#include <cassert>
#include <cstdio>
int main(){
    using namespace nao_led_avatar;
    for(int target=0;target<5;++target)for(auto r:selection(target))if(r.w>0){
        assert(targetAt(r.x+r.w*.5f,r.y+r.h*.5f)==target);
        auto card=dashboard_layout::ledAvatar;
        assert(r.x>=card.x&&r.x+r.w<=card.x+card.w&&r.y>=card.y&&r.y+r.h<card.y+95);
    }
    auto card=dashboard_layout::ledAvatar;
    assert(targetAt(card.x+1,card.y+10)==-1);
    assert(targetAt(card.x+card.w/3,card.y+40)==-1);
    assert(targetAt(card.x+30,card.y+115)==-1);
    assert(targetAt(card.x-1,card.y+40)==-1);
    assert(targetAt(card.x+card.w+1,card.y+40)==-1);
    for(int zone=1;zone<3;++zone){auto r=imageBox(zone);assert(targetAt(r.x+r.w*.1f,r.y+r.h*.5f)==(zone==1?1:4));}
    std::puts("PASS all five image targets, both ears and feet, crop transforms, gutters and footer isolation");
}
