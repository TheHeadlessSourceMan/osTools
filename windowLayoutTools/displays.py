"""
Manage monitors (aka, displays)
"""
import typing
import ctypes
from ctypes import wintypes
from osTools.windowLayoutTools.windows import Window
from osTools.windowLayoutTools.bounds2D import Bounds2DPassthrough


class Display(Bounds2DPassthrough):
    """
    A single monitor (aka, display)
    """
    def __init__(self,
        hMonitor:wintypes.HMONITOR,
        hDC:wintypes.HDC=None,
        x:int=0,
        y:int=0,
        w:int=0,
        h:int=0):
        """ """
        Bounds2DPassthrough.__init__(self,x,y,w,h)
        self.hMonitor=hMonitor
        self.hDC=hDC
        self._extInfo:typing.Optional[typing.Dict[str,typing.Any]]=None

    @property
    def isVirtual(self)->bool:
        """
        Is this a virtual display vs a physical display
        """
        for keyword in ("RDP","Remote","Virtual","Mirroring","ScreenCapture"):
            if self.deviceString.find(keyword)>=0 \
                or self.deviceID.find(keyword)>=0:
                return True
        return False

    @property
    def name(self)->str:
        """
        Friendly name of the device
        """
        return self.deviceID

    @property
    def deviceID(self)->str:
        """
        Specific id of the device
        """
        return self.extInfo["DeviceID"]

    @property
    def deviceString(self)->str:
        """
        Get the device string for this display
        """
        return self.extInfo["DeviceString"]

    def refresh(self)->None:
        """
        Refresh information about the screen
        """
        user32=ctypes.WinDLL('user32',use_last_error=True)
        #gdi32=ctypes.WinDLL('gdi32',use_last_error=True)
        # Define necessary structures and constants
        class MONITORINFOEXW(ctypes.Structure):
            """
            Ctypes struct for windows MONITOR_INFO_EX
            """
            _fields_=[
                ("cbSize",wintypes.DWORD),
                ("rcMonitor",wintypes.RECT),
                ("rcWork",wintypes.RECT),
                ("dwFlags",wintypes.DWORD),
                ("szDevice",wintypes.WCHAR*32),
            ]
        class DISPLAY_DEVICEW(ctypes.Structure):
            """
            Ctypes struct for windows DISPLAY_DEVICE
            """
            _fields_=[
                ("cb",wintypes.DWORD),
                ("DeviceName",wintypes.WCHAR*32),
                ("DeviceString",wintypes.WCHAR*128),
                ("StateFlags",wintypes.DWORD),
                ("DeviceID",wintypes.WCHAR*128),
                ("DeviceKey",wintypes.WCHAR*128),
            ]
        # Initialize structures
        monitor_info=MONITORINFOEXW()
        monitor_info.cbSize=ctypes.sizeof(MONITORINFOEXW) # noqa: E501 # pylint: disable=attribute-defined-outside-init,line-too-long
        display_device=DISPLAY_DEVICEW()
        display_device.cb=ctypes.sizeof(DISPLAY_DEVICEW) # noqa: E501 # pylint: disable=attribute-defined-outside-init,line-too-long
        # Get monitor info
        if not user32.GetMonitorInfoW(
            self.hMonitor,ctypes.byref(monitor_info)):
            raise ctypes.WinError(ctypes.get_last_error())
        # Enumerate display devices
        if not user32.EnumDisplayDevicesW(
            monitor_info.szDevice,0,ctypes.byref(display_device),0):
            raise ctypes.WinError(ctypes.get_last_error())
        self._extInfo={}
        for f,_ in monitor_info._fields_: # pylint: disable=protected-access
            self._extInfo[f]=getattr(monitor_info,f)
        for f,_ in display_device._fields_: # pylint: disable=protected-access
            self._extInfo[f]=getattr(display_device,f)
        # TODO: reset x,y,w,h using rcMonitor or rcWork members

    @property
    def extInfo(self):
        """
        Get extended info as a dict
        """
        if self._extInfo is None:
            self.refresh()
        return self._extInfo

    @property
    def windows(self)->typing.Generator[Window,None,None]:
        """
        All the windows on this display
        """
        from windows import Windows
        for w in Windows():
            if w.bounds.overlaps(self):
                yield w

    def __repr__(self):
        return f"{self.name} ({self.x},{self.y},{self.w},{self.h})"
Monitor=Display


class Displays:
    """
    All the displays(aka, monitors) on the computer
    """

    _displays:typing.Optional[typing.List[Display]]=None

    @property
    def displays(self)->typing.Generator[Display,None,None]:
        """
        All available displays
        """
        if self._displays is None:
            self.refresh()
        return self._displays

    def find(self,name:str)->typing.Optional[Display]:
        """
        Find a display with the given name
        """
        for d in self.displays:
            if d.deviceID.find(name)>=0 or d.deviceString.find(name)>=0:
                #
                return d
        return None

    def refresh(self):
        """
        refresh the list of monitors
        """
        self._displays=[]
        def monitor_enum_proc(hMonitor,hdcMonitor,lprcMonitor,_):
            rect=lprcMonitor.contents
            self._displays.append(
                Display(hMonitor,hdcMonitor,
                    rect.left,rect.top,
                    rect.right-rect.left,rect.bottom-rect.top)
            )
            return True
        # Define the MONITORINFO structure
        MonitorEnumProc=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HMONITOR,
            wintypes.HDC,ctypes.POINTER(wintypes.RECT),wintypes.LPARAM)
        user32=ctypes.windll.user32
        user32.EnumDisplayMonitors.argtypes=[wintypes.HDC,
            ctypes.POINTER(wintypes.RECT),MonitorEnumProc,wintypes.LPARAM]
        # Call EnumDisplayMonitors
        user32.EnumDisplayMonitors(
            None,None,MonitorEnumProc(monitor_enum_proc),0)

    def __len__(self)->int:
        return len(self.displays)

    def __iter__(self)->typing.Iterator[Display]:
        return iter(self.displays)

    def __repr__(self):
        return '\n'.join([repr(d) for d in self.displays])
Monitors=Displays
