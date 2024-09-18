"""
Handy progress bar library
"""
import typing
import time
import threading


ProgressCb=typing.Callable[[float,float,str],None]

def cmdLineProgress(amt:float,total:float=1.0,msg:str=''):
    """
    Display a progress bar on the command line
    """
    w=50
    full='#'
    empty='_'
    if amt==0:
        n=0
    else:
        n=int(w*amt/total)
    print(f'\r[{n*full}{(w-n)*empty}] {msg}',end='')


class TimedCall:
    """
    EXPERIMENTAL!

    Calls a function at most every n seconds
    (Useful for like ui stuff)

    Useage:
    _myFn=TimedCall(myFn)
    _myFn(normal,params)

    It can be used with Threading() or it can be run
    manually by calling like a function.

    The difference being if you do not use threading, missed
    values might be cut off -- especially the last one, so
    you may want to call self.fn() directly for the last value.

    But with threading you then have to worry about
    thread safety instead, so pick your poison.

    TODO: make this an annotation?
    """
    def __init__(self,fn:typing.Callable,timing:float=0.24):
        self.timing=timing
        self.fn=fn
        self._argset:typing.Optional[
            typing.Tuple[typing.List,typing.Dict]]=None
        self._inThread=False
        self._lasttimestamp=None
        self._lastargs=[]
        self._lastkwargs={}

    def __call__(self,*args,**kwargs):
        self._lastargs=args
        self._lastkwargs=kwargs
        if self._inThread:
            self._argset=(args,kwargs)
        else:
            import datetime
            now=datetime.datetime.now()
            if self._lasttimestamp is None \
                or (now-self._lasttimestamp).microseconds/1000000.0>=self.timing: # noqa: E501 # pylint: disable=line-too-long
                self._lasttimestamp=now
                self.fn(*self._lastargs,**self._lastkwargs)

    def run(self):
        """
        in case you want to run this like a thread
        """
        self._inThread=True
        while True:
            if self._argset is not None:
                argset=self._argset
                self._argset=None
                self.fn(*argset[0],**argset[1])


class TimerProgress(threading.Thread):
    """
    For a lot of jobs it runs in the background and then blats everything
    out at the end.  This is a bad design, yet we want to have a way
    to work around.

    The "solution" is this class, which takes a timeout estimate
    and uses a clock to update the progress bar.

    Not accurate, but at least it gives the user reasonable feedback.

    NOTE: this will run up to 99%, assuming that the initiator will call stop()
        and thus make it 100%
    """

    def __init__(self,
        progressBarCb:ProgressCb,
        timeout:float,
        interval:float=0.24):
        """ """
        threading.Thread.__init__(self)
        self.progressBarCb=progressBarCb
        self.timeout=timeout
        self.interval=interval
        self.keepGoing=True
        self.running=False

    def stop(self):
        """
        Stopping always puts the progress bar to 100%
        """
        if self.running:
            self.keepGoing=False
            self.join()
        self.progressBarCb(1.0,msg='100%')

    def run(self):
        accumulator=0
        self.running=True
        while self.keepGoing:
            time.sleep(self.interval)
            accumulator+=self.interval
            if accumulator>=self.timeout:
                self.progressBarCb(0.99,msg='99%')
                break
            percent=accumulator/float(self.timeout)
            self.progressBarCb(percent,msg=f'{int(percent*100)}%')
        self.running=False


def sample():
    """
    Sample demo
    """
    progress=TimedCall(cmdLineProgress)
    for i in range(95):
        progress(i+1,95,f'Stage {i}')
        time.sleep(0.1)
    progress.fn(i+1,95,f'Stage {i}')


def sample2():
    """
    Sample demo
    """
    tp=TimerProgress(cmdLineProgress,10)
    tp.start()
    time.sleep(15)
    tp.stop()
