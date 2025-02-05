"""
Manage graphical window
"""
import typing
import ctypes
from ctypes import wintypes
import win32gui
from bounds2D import Bounds2D,Bounds2DPassthrough
if typing.TYPE_CHECKING:
    from osTools.windowLayoutTools.desktops import Desktop
    from osTools.windowLayoutTools.displays import Display


class WindowNotFoundError(FileNotFoundError):
    """
    Error for when a window is not found
    """


def getHwndsByPid(
    pid:int,
    tid:typing.Optional[int]=None
    )->typing.Iterable[int]:
    """
    Lookup a process id and get all hWnd handles
    (if this is a windowed application)
    """
    import win32process
    results=[]
    def callback(hwnd,results):
        ctid,cpid=win32process.GetWindowThreadProcessId(hwnd) # noqa:E501 # pylint: disable=line-too-long,c-extension-no-member
        if cpid==pid:
            if tid is None or ctid==tid:
                results.append(hwnd)
    win32gui.EnumWindows(callback,results) # noqa:E501 # pylint: disable=line-too-long,c-extension-no-member
    print(f'hwnds for pid {pid}:')
    for result in results:
        print("\t0x%08X - %s"%(result,win32gui.GetWindowText(result))) # noqa:E501 # pylint: disable=line-too-long,c-extension-no-member
    return results


def getWindowsByPid(
    pid:int,
    tid:typing.Optional[int]=None
    )->typing.Iterable["Window"]:
    """
    Lookup a process id and get all Window objects
    (if this is a windowed application)
    """
    return [Window(hwnd) for hwnd in getHwndsByPid(pid,tid)]

def getPidByHwnd(
    hWnd:int
    )->typing.Tuple[int,int]:
    """
    Lookup a process id and get all hWnd handles
    (if this is a windowed application)
    return pid,tid
    """
    import win32process
    tid,pid=win32process.GetWindowThreadProcessId(hWnd) # noqa:E501 # pylint: disable=line-too-long,c-extension-no-member
    return pid,tid


def runAndGetWindow(
    command:str,
    title:typing.Union[None,str,typing.Pattern]=None,
    visible:typing.Optional[bool]=None,
    className:typing.Union[None,str,typing.Pattern]=None,
    checkExisting:bool=False,
    starupTime:float=5.0
    )->typing.Tuple[int,typing.Optional["Window"]]:
    """
    Start a program and wait for a particular window

    :command: command to run to start the window
    :title: title of the window to search for
    :visible: whether the window we want is visible
    :className: windows class name of the window to search for
    :checkExisting: if the specified window already exists,
        return it instead of running a new instance
    :starupTime: how long to wait for window to appear
        (After that, returns None)

    Returns pid,window
    """
    import subprocess
    import time
    allWindows=Windows()
    if checkExisting:
        windows=allWindows.find(
            title=title,visible=visible,className=className)
        if windows:
            window=windows[0]
            return window.pid,window
    po=subprocess.Popen(command)
    time.sleep(0.1)
    windows=allWindows.waitFor(
        title=title,visible=visible,className=className,
        pid=po.pid,timeout=starupTime)
    if windows:
        return po.pid,windows[0]
    return po.pid,None


class Window(Bounds2DPassthrough):
    """
    A single graphical window

    TODO: this should be combined with existing Window object
    from my process management stuff
    """

    def __init__(self,
        hWnd:typing.Union[int,str,wintypes.HWND],
        pid:typing.Optional[int]=None,
        tid:typing.Optional[int]=None):
        """ """
        Bounds2DPassthrough.__init__(self,0,0,0,0)
        if hWnd is None:
            if pid is not None:
                hWnds=getHwndsByPid(pid,tid)
                if hWnds:
                    # assume the fist one
                    # TODO: is there a smarter way?
                    hWnd=hWnds[0]
            if hWnd is None:
                raise WindowNotFoundError("No window to attach to")
        self.hWnd:int=int(hWnd)
        self.desktop:"Desktop"
        self._state:typing.List[str]=[]
        self._pid:typing.Optional[int]=pid
        self._tid:typing.Optional[int]=tid

    @property
    def bounds(self):
        """
        bounds value
        """
        return self
    @bounds.setter
    def bounds(self,bounds:Bounds2D):
        if self._bounds!=bounds:
            self._bounds=bounds
            win32gui.MoveWindow(self.hWnd,self.x,self.y,self.w,self.h,True) # noqa:E501 # pylint: disable=line-too-long,c-extension-no-member

    @property
    def hProcess(self)->int:
        """
        Windows handle to the process
        (this is different than pid)
        """
        import win32api
        return win32api.OpenProcess(1,False,self.pid) # noqa:E501 # pylint: disable=line-too-long,c-extension-no-member

    @property
    def pid(self)->int:
        """
        Process id
        """
        if self._pid is None:
            self._pid,self._tid=getPidByHwnd(self.hWnd)
        return self._pid

    @property
    def tid(self)->int:
        """
        Thread id
        """
        if self._tid is None:
            self._pid,self._tid=getPidByHwnd(self.hWnd)
        return self._tid

    @property
    def hMonitor(self)->wintypes.HMONITOR:
        """
        Handle to the monitor this window is on
        """
        return ctypes.windll.user32.MonitorFromWindow(
            self.hWnd,2) # MONITOR_DEFAULTTONEAREST

    @property
    def display(self)->"Display":
        """
        The display/monitor this window lives on
        """
        from osTools.windowLayoutTools.displays import Display
        return Display(self.hMonitor)
    @display.setter
    def display(self,display:typing.Union[str,"Display"]):
        from osTools.windowLayoutTools.displays import (
            Display,Displays)
        if not isinstance(display,Display):
            display=Displays().find(display)
        if display is not None and display!=self.display:
            dx=self.x-self.display.x
            dy=self.y-self.display.y
            self.move(display.x+dx,display.y+dy)

    @property
    def monitor(self)->"Display":
        """
        The display/monitor this window lives on
        """
        return self.display

    @property
    def title(self)->str:
        """
        The title of this window
        """
        return win32gui.GetWindowText(self.hWnd) # noqa: E501 # pylint: disable=c-extension-no-member, line-too-long

    @property
    def className(self)->str:
        """
        Window class name
        """
        return win32gui.GetClassName(self.hWnd) # noqa:E501 # pylint: disable=line-too-long,c-extension-no-member

    @property
    def name(self)->str:
        """
        The name of this window (same as title)
        """
        return self.title

    def move(self,x:int,y:int):
        """
        Move this window to a new position
        """
        self.bounds=Bounds2D(x,y,self.w,self.h)

    def resize(self,w:int,h:int):
        """
        Resize this window
        """
        self.bounds=Bounds2D(self.x,self.y,w,h)

    @property
    def state(self):
        """
        state of the window, valid values include:
            "normal",
            "maximized",
            "minimized",
            "fullscreen",
            "statusbar",
            "modal",
            "hidden"
        """
        return ','.join(self._state)
    @state.setter
    def state(self,state:typing.Union[str,typing.Iterable[str]]):
        if isinstance(state,str):
            state=state.replace(',',' ').split()
        raise NotImplementedError()
        win32gui.ShowWindow(self.hWnd,5) # TODO: # noqa:E501 # pylint: disable=line-too-long,c-extension-no-member
        win32gui.SetForegroundWindow(self.hWnd) # noqa:E501 # pylint: disable=line-too-long,c-extension-no-member

    @property
    def visible(self)->bool:
        """
        Is the window visible?
        """
        return win32gui.IsWindowVisible(self.hWnd) # noqa:E501 # pylint: disable=line-too-long,c-extension-no-member
    @property
    def hidden(self)->bool:
        """
        Is the window hidden?
        """
        return not self.visible

    def __eq__(self,other):
        if isinstance(other,Window):
            return self.hWnd==other.hWnd
        if isinstance(other,int):
            return self.hWnd==other
        return False

    def __hash__(self):
        return self.hWnd

    def __repr__(self):
        return f'"{self.name}"'


class Windows:
    """
    all windows on the system
    """
    _topLevelWindows:typing.Optional[typing.List[Window]]=None

    def __init__(self,windows:typing.Optional[typing.List[Window]]=None):
        self._windows=windows

    def waitFor(self,
        title:typing.Union[None,str,typing.Pattern]=None,
        visible:typing.Optional[bool]=None,
        className:typing.Union[None,str,typing.Pattern]=None,
        pid:typing.Optional[int]=None,
        timeout:typing.Optional[float]=None,
        pollInterval:float=0.1
        )->"Windows":
        """
        Wait for a window to exist

        :title: title of the window to search for
        :visible: whether the window we want is visible
        :className: windows class name of the window to search for
        :pid: process id of the window to search for
        :timeout: how long to wait before returning empty list
        """
        import time
        targetTime=time.time()+timeout
        while time.time()<targetTime:
            windows=self.find(
                title=title,visible=visible,className=className,pid=pid)
            if windows:
                break
            time.sleep(pollInterval)
        return windows

    def find(self,
        title:typing.Union[None,str,typing.Pattern]=None,
        visible:typing.Optional[bool]=None,
        className:typing.Union[None,str,typing.Pattern]=None,
        pid:typing.Optional[int]=None,
        refresh:bool=True
        )->"Windows":
        """
        Find windows in this set which match a given set of criteria

        :title: title of the window to search for
        :visible: whether the window we want is visible
        :className: windows class name of the window to search for
        :pid: process id of the window to search for
        :refresh: whether to refresh the list before searching
            default is True, but False can save some time
        """
        if refresh:
            self.refresh()
        found=[]
        for w in self.windows:
            # it it the correct process
            if pid is not None and w.pid!=pid:
                continue
            # is it even visible
            if visible is not None and w.visible!=visible:
                continue
            # is it the correct windows class name
            if className is not None:
                if isinstance(className,str):
                    if w.className.find(className)<0:
                        continue
                elif className.match(w.className) is None:
                    continue
            # match the title
            if title is not None:
                if isinstance(title,str):
                    if w.title.find(title)<0:
                        continue
                elif title.match(w.title) is None:
                    continue
            # if it made it this far, add it
            found.append(w)
        return Windows(found)

    @property
    def windows(self)->typing.Iterable:
        """
        All the windows in this set
        """
        if self._windows is None:
            return self.allWindows
        return self._windows

    @property
    def allWindows(self)->typing.Iterable:
        """
        All the windows on the computer
        """
        if self._topLevelWindows is None:
            self.refresh()
        return self._topLevelWindows

    def __len__(self)->int:
        return len(self.windows)

    def __iter__(self):
        return iter(self.windows)

    def __getitem__(self,idx):
        return tuple(self.windows)[idx]

    def refresh(self)->None:
        """
        Refresh the top level window list
        """
        self._topLevelWindows=[]
        def winEnumHandler(hwnd,_):
            self._topLevelWindows.append(Window(hwnd))
        win32gui.EnumWindows(winEnumHandler,None) # noqa: E501 # pylint: disable=c-extension-no-member, line-too-long
