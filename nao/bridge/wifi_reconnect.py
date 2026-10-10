"""Reconnect a saved Wi-Fi network only while robot control is stopped."""
class WifiReconnect(object):
    def __init__(self,manager,clock):
        self.manager=manager;self.clock=clock;self.pending=None;self.retry_at=0.
    def tick(self,stopped):
        now=self.clock()
        if self.pending:
            kind,future=self.pending
            if not future.isFinished():return
            self.pending=None
            try:result=future.value(0)
            except Exception:return
            if kind=='services' and stopped:
                services=[dict(item) for item in result]
                if any(item.get('Type')=='wifi' and item.get('State') in ('ready','online','association','configuration') for item in services):return
                for item in services:
                    if item.get('Type')=='wifi' and item.get('Favorite') and item.get('Autoconnect') and item.get('State') in ('idle','failure'):
                        self.retry_at=now+15.
                        self.pending=('connect',self.manager.connect(item['ServiceId'],_async=True))
                        print('Saved Wi-Fi reconnect requested / motion remains stopped')
                        return
        if stopped and now>=self.retry_at:
            self.retry_at=now+5.
            self.pending=('services',self.manager.services(_async=True))
