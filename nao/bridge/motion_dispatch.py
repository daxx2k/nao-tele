"""Bounded SDK submission off the tracking lock, with a STOP generation barrier."""
import threading
try:import Queue as queue
except ImportError:import queue

class DispatchFuture(object):
    def __init__(self):self.ready=threading.Event();self.native=None;self.error=None
    def isFinished(self):return self.ready.is_set() and (self.error is not None or self.native.isFinished())
    def value(self,timeout=0):
        if not self.ready.wait(max(0.,timeout)/1000.):raise RuntimeError('SDK submission pending')
        if self.error is not None:raise self.error
        return self.native.value(timeout)
    def cancel(self):
        if self.ready.is_set() and self.native is not None:self.native.cancel()

class MotionDispatch(object):
    def __init__(self):
        self.gate=threading.Lock();self.epoch=0;self.jobs=queue.Queue(8)
        self.worker=threading.Thread(target=self.run);self.worker.daemon=True;self.worker.start()
    def submit(self,operation):
        future=DispatchFuture();self.jobs.put_nowait((self.epoch,operation,future));return future
    def invalidate(self):
        # Wait only for an in-flight submission, never for physical completion.
        with self.gate:self.epoch+=1
    def close(self):
        self.invalidate();self.jobs.put(None);self.worker.join(.5)
    def run(self):
        while True:
            job=self.jobs.get()
            if job is None:return
            epoch,operation,future=job
            try:
                with self.gate:
                    if epoch!=self.epoch:raise RuntimeError('SDK request cancelled by STOP')
                    future.native=operation()
            except Exception as exc:future.error=exc
            finally:future.ready.set();self.jobs.task_done()

class DrainFuture(object):
    def __init__(self,futures):self.futures=list(futures)
    def isFinished(self):return all(f.isFinished() for f in self.futures)
    def value(self,timeout=0):
        for future in self.futures:
            try:future.value(0)
            except RuntimeError as exc:
                if str(exc)!='SDK request cancelled by STOP':raise
    def cancel(self):pass
