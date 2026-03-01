"""
Save/load/apply window layouts
including auto-run of applications that are not present
"""
import typing
import json
from pathlib import Path
from osTools.windowLayoutTools.windows import (
    Windows,Window,runAndGetWindow)
from osTools.windowLayoutTools.bounds2D import Bounds2D


Json=typing.Dict[str,typing.Any]

class windowLayout:
    """
    Layout for a single window
    """
    def __init__(self,
        jsonObj:typing.Optional[Json]=None,
        window:typing.Union[None,int,Window]=None):
        """
        :window: if json is also specified, will
            auto-apply it to window.
            If json is not specified, will
            take existing dimensions from window
        """
        self._window:typing.Optional[Window]=None
        self._json:Json={}
        if jsonObj is not None:
            self.assign(jsonObj)
            if window is not None:
                if not isinstance(window,Window):
                    window=Window(window)
                self.window=window
                self.apply()
        if window is not None:
            self.assign(window)

    @property
    def window(self)->Window:
        """
        If there is not a linked window, will
        attempt to find window by "title"
        and/or autostart program as specified by
            "autoStart" and "command"
        """
        if self._window is None:
            window=None
            title=self._json.get("title","")
            autoStart=self._json.get("autoStart","never")
            if autoStart!="always":
                # find any existing
                windows=Windows().find(title=title)
                if windows:
                    window=windows[0]
            if window is None and autoStart!="never":
                # attempt to auto-start
                command=self._json.get('command')
                if command is None:
                    raise Exception("Unable to autoStart window with no command specified") # noqa: E501 # pylint: disable=line-too-long
                _,window=runAndGetWindow(command,title=title)
            if window is None:
                raise FileNotFoundError(f'Unable to find window called "{title}"') # noqa: E501 # pylint: disable=line-too-long
            self._window=window
        return self._window
    @window.setter
    def window(self,window:typing.Union[int,str,Window]):
        if not isinstance(window,Window):
            window=Window(window)
        self._window=window

    def _assignFromWindow(self,window:Window)->None:
        """
        Assign the value of this layout from an existing window.

        To use this, just call assign().
        """
        self._json["title"]=window.title
        self._json["command"]=window.commandLine
        self._json["display"]=window.display.name
        self._json["desktop"]=window.desktop.name
        self._json["x"]=window.x
        self._json["y"]=window.y
        self._json["w"]=window.w
        self._json["h"]=window.h
        self._json["windowStyle"]=window.state

    def updateFromWindow(self):
        """
        Update this layout info to reflect how the window
        actually looks.

        (Useful for saving current layout)
        """
        self._assignFromWindow(self.window)

    def assign(self,
        assignFrom:typing.Union[int,str,Window,Json,Bounds2D],
        apply:bool=False
        )->None:
        """
        Can assign the value of this layout from:
            an hWnd
            a Window object
            Json data (dict)
            or assign just the bounds with a Bounds2D
        """
        if isinstance(assignFrom,Bounds2D):
            self._json["x"]=assignFrom.x
            self._json["y"]=assignFrom.y
            self._json["w"]=assignFrom.w
            self._json["h"]=assignFrom.h
        elif isinstance(assignFrom,(int,str,Window)):
            if not isinstance(assignFrom,Window):
                assignFrom=Window(assignFrom)
            self._assignFromWindow(assignFrom)
        else:
            self._json.update(assignFrom)
        if apply:
            self.apply()

    @property
    def bounds(self)->Bounds2D:
        """
        Get the location as a bounds structure
        """
        return Bounds2D(
            int(self.jsonObj.get("x",0)),
            int(self.jsonObj.get("y",0)),
            int(self.jsonObj.get("w",0)),
            int(self.jsonObj.get("h",0)))

    @property
    def jsonObj(self)->Json:
        """
        Get as json object of the form:
        {
            "title":"paintbrush",
            "autoStart":"ifNotRunning",
            "command":"mspaint",
            "display":"1",
            "desktop":"test desktop",
            "x":"0",
            "y":"0",
            "w":"100",
            "h":"100",
            "windowStyle":"normal"
        },
        """
        return self._json
    @jsonObj.setter
    def jsonObj(self,jsonObj:Json):
        self._json=jsonObj

    def apply(self):
        """
        Apply this layout to the specified window
        """
        window=self.window
        window.bounds=self.bounds
        display=self._json.get("display")
        if display is not None:
            window.display=display
        desktop=self._json.get("desktop")
        if desktop is not None:
            window.desktop=desktop
        windowStyle=self._json.get("windowStyle")
        if windowStyle is not None:
            window.windowStyle=windowStyle


class WindowLayouts:
    """
    Save/load/apply window layouts
    including auto-run of applications that are not present
    """

    def __init__(self,filename:str='',apply:bool=False):
        self._windowLayouts:typing.List[windowLayout]=[]
        if filename:
            self.load(filename,apply)

    def clear(self)->None:
        """
        Clear the list of layouts
        """
        self._windowLayouts=[]

    def apply(self)->None:
        """
        apply the layout
        """
        for layout in self._windowLayouts:
            layout.apply()

    def getLayout(self,forWindow:Window
        )->typing.Optional[windowLayout]:
        """
        If there's a layout for a given window, return it.
        """
        for layout in self._windowLayouts:
            if layout.window==forWindow:
                return layout
        return None

    def updateFromWindows(self):
        """
        Update the json data to reflect the current window locations
        """
        for layout in self._windowLayouts:
            layout.updateFromWindow()

    def addWindows(self,windows:typing.Iterator[Window]):
        """
        Add windows to the JSON if they're not already there

        :windows: windows to add.
        """
        for window in windows:
            layout=self.getLayout(window)
            if layout is not None:
                layout.updateFromWindow()
            else:
                layout=windowLayout(window=window)
                self._windowLayouts.append(layout)
        raise NotImplementedError()

    def addAllWindows(self):
        """
        Add all windows that are open to the JSON
        if they're not already there
        """
        self.addWindows(Windows())

    @property
    def jsonStr(self)->str:
        """
        Get the json data as a string

        NOTE: setting does not clear.  You may want to call clear() first
        """
        return self.jsonObj.dumps()
    @jsonStr.setter
    def jsonStr(self,jsonStr:str):
        """
        NOTE: setting does not clear.  You may want to call clear() first
        """
        self.jsonObj=json.loads(jsonStr)

    @property
    def jsonObj(self
        )->typing.List[typing.Dict[str,typing.Any]]:
        """
        Get the json data as a json object

        NOTE: setting does not clear.  You may want to call clear() first
        """
        return [layout.jsonObj for layout in self._windowLayouts]
    @jsonObj.setter
    def jsonObj(self,jsonObj:typing.Iterable[typing.Dict[str,typing.Any]]):
        """
        NOTE: setting does not clear.  You may want to call clear() first
        """
        for j in jsonObj["windows"]:
            self._windowLayouts.append(windowLayout(j))

    def load(self,
        filename:typing.Union[str,Path],
        apply:bool=False,
        clear:bool=True):
        """
        Load the layout from file
        """
        if clear:
            self.clear()
        if not isinstance(filename,Path):
            filename=Path(filename)
        self.jsonStr=filename.read_text(encoding="utf-8",errors="ignore")
        if apply:
            self.apply()

    def save(self,
        filename:typing.Union[str,Path],
        update:bool=True):
        """
        Save the current layout to file
        """
        if not self._windowLayouts:
            raise Exception("Nothing to save")
        if update:
            self.updateFromWindows()
        if not isinstance(filename,Path):
            filename=Path(filename)
        filename.write_text(self.jsonStr,'utf-8')

def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    didSomething=False
    printhelp=False
    if not isinstance(args,list):
        args=list(args)
    for arg in args:
        if arg.startswith('-'):
            av=arg.split('=',1)
            av[0]=av[0].lower()
            if av[0] in ('-h','--help'):
                printhelp=True
            else:
                printhelp=True
        else:
            printhelp=True
    if printhelp or not didSomething:
        print('USEAGE:')
        print('  windowLayout [options] [filenames]')
        print('OPTIONS:')
        print('  -h ................................. this help')
        return 1
    return 0


if __name__=='__main__':
    #import sys
    #cmdline(sys.argv[1:])
    # test code
    layout=WindowLayouts('sampleLayout.json')
    layout.apply()
