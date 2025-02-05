"""
The ability to query windows context menu
and run items from the command line
"""
import typing
import ctypes
from pathlib import Path
from ctypes import wintypes
from win32com.shell import shell
import win32gui
import win32con
import win32gui_struct


# Constants for invoking commands
CMIC_MASK_UNICODE=0x00004000
SEE_MASK_NOCLOSEPROCESS=0x00000040
SEE_MASK_FLAG_NO_UI=0x00000400
SEE_MASK_INVOKEIDLIST=0x0000000C
CMF_NORMAL=0


class SHELLEXECUTEINFO(ctypes.Structure):
    """
    A ctypes version of the windows struct
    """
    _fields_=[
        ("cbSize",wintypes.DWORD),
        ("fMask",wintypes.ULONG),
        ("hwnd",wintypes.HWND),
        ("lpVerb",wintypes.LPCWSTR),
        ("lpFile",wintypes.LPCWSTR),
        ("lpParameters",wintypes.LPCWSTR),
        ("lpDirectory",wintypes.LPCWSTR),
        ("nShow",ctypes.c_int),
        ("hInstApp",wintypes.HINSTANCE),
        ("lpIDList",wintypes.LPVOID),
        ("lpClass",wintypes.LPCWSTR),
        ("hkeyClass",wintypes.HKEY),
        ("dwHotKey",wintypes.DWORD),
        ("hIcon",wintypes.HANDLE),
        ("hProcess",wintypes.HANDLE),
    ]


class ContextMenuItem:
    """
    a single menu item in the context menu
    """
    def __init__(self,
        contextMenuForFilename:"ContextMenuForFilename",
        hMenu:int,
        menuIdx:int,
        parent:typing.Optional["ContextMenuItem"]=None):
        """ """
        self.parent=parent
        self.contextMenuForFilename=contextMenuForFilename
        self.children:typing.List["ContextMenuItem"]=[]
        menuItemInfoBuf,_=win32gui_struct.EmptyMENUITEMINFO()
        win32gui.GetMenuItemInfo(hMenu,menuIdx,True,menuItemInfoBuf)
        menuItemInfo=win32gui_struct.UnpackMENUITEMINFO(menuItemInfoBuf)
        self.fType=menuItemInfo.fType
        self.fState=menuItemInfo.fState
        self.wID=menuItemInfo.wID
        self.hSubMenu=menuItemInfo.hSubMenu
        self.hbmpChecked=menuItemInfo.hbmpChecked
        self.hbmpUnchecked=menuItemInfo.hbmpUnchecked
        self.dwItemData=menuItemInfo.dwItemData
        self.text=menuItemInfo.text
        self.hbmpItem=menuItemInfo.hbmpItem
        #self.menu_id=win32gui.GetMenuItemID(hMenu,menuIdx)
        if self.hSubMenu is not None:
            for i in range(win32gui.GetMenuItemCount(self.hSubMenu)):
                self.children.append(ContextMenuItem(
                    self.contextMenuForFilename,self.hSubMenu,i,self))

    @property
    def name(self)->str:
        """
        Name of the menu item (without hotkey hint)
        """
        return self.text.replace('&','')

    @property
    def hotkey(self)->typing.Optional[str]:
        """
        keyboard hotkey
        """
        s=self.text.split('&',1)
        if len(s)<2:
            return None
        c=s[-1][0]
        return 'ALT+'+c.upper()

    def execute(self):
        """
        Execute the item
        """
        sei=SHELLEXECUTEINFO()
        sei.cbSize=ctypes.sizeof(SHELLEXECUTEINFO) # noqa:E501 # pylint: disable=line-too-long,attribute-defined-outside-init
        sei.fMask=SEE_MASK_INVOKEIDLIST|SEE_MASK_NOCLOSEPROCESS|SEE_MASK_FLAG_NO_UI # noqa:E501 # pylint: disable=line-too-long,attribute-defined-outside-init
        sei.hwnd=None # noqa:E501 # pylint: disable=line-too-long,attribute-defined-outside-init
        sei.lpVerb=self.name # noqa:E501 # pylint: disable=line-too-long,attribute-defined-outside-init
        sei.lpFile=str(self.contextMenuForFilename.filename) # noqa:E501 # pylint: disable=line-too-long,attribute-defined-outside-init
        sei.lpParameters=None # noqa:E501 # pylint: disable=line-too-long,attribute-defined-outside-init
        sei.lpDirectory=None # noqa:E501 # pylint: disable=line-too-long,attribute-defined-outside-init
        sei.nShow=win32con.SW_SHOWNORMAL # noqa:E501 # pylint: disable=line-too-long,attribute-defined-outside-init
        sei.hInstApp=None # noqa:E501 # pylint: disable=line-too-long,attribute-defined-outside-init
        sei.lpIDList=None # noqa:E501 # pylint: disable=line-too-long,attribute-defined-outside-init
        shell32=ctypes.windll.shell32
        shell32.ShellExecuteExW(ctypes.byref(sei))
    def __call__(self):
        self.execute()

    def __repr__(self):
        if self.fType==2048: # separator
            return '--------'
        ret=[self.text]
        for c in self.children:
            ret.append(repr(c))
        return '\n\t\t'.join(ret)


class ContextMenuForFilename:
    """
    represents the context menu for a given filename
    """
    def __init__(self,filename:typing.Union[str,Path]):
        """
        Retrieves Windows Explorer context menu entries for a given file.
        Returns a list of (menu_text,command) tuples.
        """
        self._filename:Path
        self.entries:typing.List[ContextMenuItem]=[]
        self.assign(filename)

    @property
    def filename(self)->Path:
        """
        get the target filename
        """
        return self._filename
    @filename.setter
    def filename(self,filename:typing.Union[str,Path]):
        self.assign(filename)

    def assign(self,filename:typing.Union[str,Path]):
        """
        Retrieves Windows Explorer context menu entries for a given file.
        Returns a list of (menu_text,command) tuples.
        """
        self.entries=[]
        if not isinstance(filename,Path):
            filename=Path(filename)
        filename=filename.absolute()
        self._filename=filename
        parent_folder=filename.parent
        item=filename.name
        desktop = shell.SHGetDesktopFolder()
        pidl_parent = shell.SHILCreateFromPath(str(parent_folder), 0)[0]
        parent_shell_folder = desktop.BindToObject(pidl_parent, None, shell.IID_IShellFolder)
        pidl_item = parent_shell_folder.ParseDisplayName(0, None, item)[1]
        context_menu = parent_shell_folder.GetUIObjectOf(0, [pidl_item], shell.IID_IContextMenu)[1]
        hMenu=win32gui.CreatePopupMenu()
        if context_menu is None:
            print('Failed to retrieve context menu')
            return []
        context_menu.QueryContextMenu(hMenu,0,1,0x7FFF,CMF_NORMAL)
        for i in range(win32gui.GetMenuItemCount(hMenu)):
            self.entries.append(ContextMenuItem(self,hMenu,i))
        win32gui.DestroyMenu(hMenu)

    def __repr__(self):
        ret=[str(self.filename)]
        for e in self.entries:
            ret.append(repr(e))
        return '\n\t'.join(ret)


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    didSomething=False
    printhelp=False
    currentFilename=''
    executeVerb=''
    if not isinstance(args,list):
        args=list(args)
    def runOnFilename(filename:str):
        if not executeVerb:
            menuEntries=ContextMenuForFilename(filename)
            print(menuEntries)
    for arg in args:
        if arg.startswith('-'):
            av=arg.split('=',1)
            av[0]=av[0].lower()
            if av[0] in ('-h','--help'):
                printhelp=True
            else:
                printhelp=True
        else:
            if currentFilename:
                runOnFilename(currentFilename)
                didSomething=True
            currentFilename=arg
    if currentFilename:
        runOnFilename(currentFilename)
        didSomething=True
    if printhelp or not didSomething:
        print('USEAGE:')
        print('  displays [options] [filenames] ...')
        print('OPTIONS:')
        print('  -h ................................. this help')
        return 1
    return 0


if __name__=='__main__':
    import sys
    cmdline(sys.argv[0:])
