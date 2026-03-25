"""
Tools to get get cpu usage and detect idle for a process
or for the whole system
"""
import typing
import os
import time
import threading


class HasPid(typing.Protocol):
    """
    Any class with a pid member
    """
    pid:int
PidCompatible=typing.Union[int,HasPid]


def asPid(pid:typing.Optional[PidCompatible])->int:
    """
    Always return an integer pid
    """
    if pid is None:
        return os.getpid()
    if isinstance(pid,int):
        return pid
    return pid.pid


if os.name=='nt':
    import win32process
    import win32api

    def systemIdleTime()->float:
        """
        Get the idle time (in seconds) for the system
        """
        idleTime=0
        lastInputInfo=win32api.GetLastInputInfo()
        tickCount=win32api.GetTickCount()
        idleTime=(tickCount-lastInputInfo[1])/1000.0
        return idleTime

    def getProcessCpuUsage(
        pid:typing.Optional[PidCompatible]=None
        )->float:
        """
        Get the cpu usage for a process.

        :pid: if not specified, get usage for the current process
        """
        pid=asPid(pid)
        handle=None
        totalTime=0
        try:
            # Open the process with the specified PID
            handle=win32api.OpenProcess(win32process.PROCESS_ALL_ACCESS,False,pid)
            # Get the process's CPU times
            cpuTimes=win32process.GetProcessTimes(handle)
            userTime=cpuTimes[0]
            kernelTime=cpuTimes[1]
            # Calculate total time
            totalTime=userTime+kernelTime
        finally:
            if handle is not None:
                win32api.CloseHandle(handle)
        return totalTime
else:
    def systemIdleTime()->float:
        """
        Get the idle time (in seconds) for the system
        """
        with open('/proc/uptime','r') as f:
            upTimeCols=f.read().split()
        return float(upTimeCols[1])

    def getProcessCpuUsage(
        pid:typing.Optional[PidCompatible]=None
        )->float:
        """
        Get the cpu usage for a process.

        :pid: if not specified, get usage for the current process
        """
        pid=asPid(pid)
        totalTime=0
        try:
            with open(f'/proc/{pid}/stat','r') as f:
                data=f.read().split()
            # Extract user and system time from the stat file
            userTime=int(data[13])  # User CPU time (jiffies)
            systemTime=int(data[14])  # System CPU time (jiffies)
            # Total CPU time
            totalTime=(userTime+systemTime)/60.0
        except FileNotFoundError:
            raise ValueError(f"Process with PID {pid} does not exist.")
        return totalTime


def onProcessIdle(
    pid:PidCompatible,
    fn:typing.Optional[typing.Callable[[int],typing.Optional[bool]]]=None,
    cpuThreshold:float=0.001,
    idleDuration:float=0.0
    )->threading.Thread:
    """
    Watch a process and return when it is idle.

    :fn: the function to call when the process goes idle
        this is of the form fn(pid) where it returns True
        if the thread should exit.
    :cpuThreshold: cpu below this amount is considered idle
    :idleDuration: must be below cpuThreshold for this long

    NOTE: this starts a thread.  If you want do block do
    onProcessIdle(pid).join()
    """
    pid=asPid(pid)
    def threadFn():
        while True:
            usage=getProcessCpuUsage(pid)
            if usage<cpuThreshold:
                result=None
                if idleDuration<=0:
                    if fn is None:
                        break
                    result=fn(pid)
                else:
                    # need to check periodically
                    timeslice=max(0.001,idleDuration)
                    target=time.time()+idleDuration
                    isOk=True
                    for _ in range(time.time(),target,timeslice):
                        if usage>=idleDuration:
                            isOk=False
                            break
                    if isOk:
                        if fn is None:
                            break
                        result=fn(pid)
                if result is not None and result:
                    break
            else:
                time.sleep(0.1)
    t=threading.Thread(target=threadFn)
    t.start()
    return t


def onSystemIdle(
    fn:typing.Optional[typing.Callable[[],typing.Optional[bool]]],
    idleDuration:float=0.0
    )->threading.Thread:
    """
    Watch for the system to become idle and call
    function when it happens.
    Useful for things like AFK detection and starting
    maintinence tasks.

    :fn: the function to call when the system goes idle
        this is of the form fn() where it returns True
        if the thread should exit.
    :idleDuration: must be below idle for this long

    NOTE: this starts a thread.  If you want do block instead do:
    onSystemIdle().join()
    """
    def threadFn():
        while True:
            t=systemIdleTime()
            if t>idleDuration:
                if fn is None:
                    break
                result=fn()
                if result is not None and result:
                    break
            else:
                time.sleep(idleDuration-t)
    t=threading.Thread(target=threadFn)
    t.start()
    return t
