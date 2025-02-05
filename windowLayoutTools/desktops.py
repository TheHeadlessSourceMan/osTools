"""
Manage windows desktops

NOTE: This is similar to pyvda, so
may just want to use that sometime
https://github.com/mrob95/pyvda
"""
import typing
import ctypes
from comtypes import (GUID)
if typing.TYPE_CHECKING:
    from osTools.windowLayoutTools.windows import Window
    from osTools.windowLayoutTools.displays import Display
from com_defns import _get_object,IVirtualDesktopManagerInternal,CLSID_VirtualDesktopManagerInternal


class Desktop:
    """
    A single desktop
    """
    def __init__(self,desktopID:str):
        self.desktopID=desktopID

    @property
    def name(self):
        """
        The name of this desktop
        """
        return self.desktopID

    @property
    def windows(self)->typing.Iterable["Window"]:
        """
        All of the windows on all of the displays on this desktop
        """

    @property
    def displays(self)->typing.Iterable["Display"]:
        """
        All of the displays on this desktop
        """




class Desktops:
    """
    All of the desktops on the machine
    """

    _virtualDesktopManager=None # use single, global instance

    @property
    def virtualDesktopManager(self):
        """
        Get the windows desktop manager COM object
        """
        if self._virtualDesktopManager is None:
            self._virtualDesktopManager=_get_object(IVirtualDesktopManagerInternal, CLSID_VirtualDesktopManagerInternal)
        return self._virtualDesktopManager

    def __len__(self)->int: # pylint: disable=invalid-length-returned
        return self.count

    def __iter__(self)->typing.Iterable[Desktop]:
        yield from self.desktops

    @property
    def count(self)->int:
        """
        Get the count of virtual desktops
        """
        getCountMethod=self.virtualDesktopManager[0].lpVtbl[3] # Index of `GetCount` method # noqa: E501 # pylint: disable=line-too-long
        count=ctypes.c_uint()
        getCountMethod(self.virtualDesktopManager,ctypes.byref(count))
        return count

    def findWindow(self,
        continingWindow:"Window"
        )->typing.Tuple[Desktop,"Display"]:
        """
        Find the desktop and display containing a given window
        """
        raise NotImplementedError()

    @property
    def desktops(self)->typing.Generator[Desktop,None,None]:
        """
        All of the desktops on the machine
        """
        virtualDesktopManager=self.virtualDesktopManager
        getDesktopMethod=virtualDesktopManager[0].lpVtbl[4] # Index of `GetDesktop` method # noqa: E501 # pylint: disable=line-too-long
        for i in range(self.count):
            desktop=ctypes.POINTER(ctypes.c_void_p)()
            getDesktopMethod(
                virtualDesktopManager,
                ctypes.c_int(i),
                ctypes.byref(desktop))
            # Get the desktop GUID
            get_desktop_id=desktop[0].lpVtbl[3] # Index of `GetID` method
            desktop_id=GUID()
            get_desktop_id(desktop,ctypes.byref(desktop_id))
            yield Desktop(str(desktop_id))

    @property
    def currentDesktop(self)->Desktop:
        """
        The currently selected desktop
        """

    def __del__(self):
        if self._virtualDesktopManager:
            self._virtualDesktopManager=None

    def __repr__(self):
        return '\n'.join([repr(dt) for dt in self.desktops])


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
        print('  displays [options] [commands]')
        print('OPTIONS:')
        print('  -h ................................. this help')
        return 1
    return 0


if __name__=='__main__':
    #import sys
    #cmdline(sys.argv[1:])
    # test code
    desktops=Desktops()
    print(desktops)
