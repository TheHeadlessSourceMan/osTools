"""
Common base class for file explorer context menu
"""
from abc import abstractmethod
import typing
import subprocess
import PIL.Image
from paths import Url,UrlListCompatible,asUrlList


class ContextMenuItemBase:
    """
    A single item in a context menu
    """
    def __init__(self,contextMenu:"FileExplorerContextMenuBase",name:str):
        self.parent=contextMenu
        self.name=name

    @property
    def icon(self)->PIL.Image.Image:
        """
        Get the icon for this menu item
        """
        return self.getIcon()

    @abstractmethod
    def getIcon(self)->PIL.Image.Image:
        """
        Get the icon for this menu item
        """

    @property
    def cmdFormat(self)->str:
        """
        Get the raw command line command
        """
        return self.getCmdFormat()

    @abstractmethod
    def getCmdFormat(self)->str:
        """
        Get the raw command line command
        """

    @abstractmethod
    def applyCmdFormat(self,cmdFormat:str,files:typing.Iterable[Url])->str:
        """
        Apply the given command format to the given files
        """

    @property
    def cmd(self)->str:
        """
        Get the runnable command for this menu item
        """
        return self.applyCmdFormat(self.getCmdFormat(),self.parent.files)

    def run(self)->subprocess.Popen:
        """
        Run this menu item
        """
        return subprocess.Popen(self.cmd,cwd=str(self.parent.cwd),
            shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    __call__=run


class FileExplorerContextMenuBase:
    """
    Common base class for file explorer context menu
    """
    def __init__(self,parent:"FileExplorerContextMenusBase",forFiles:UrlListCompatible):
        self._forFiles=asUrlList(forFiles)
        self._entries:typing.Dict[str,ContextMenuItemBase]={}
        self.parent=parent

    @property
    def cwd(self)->Url:
        """
        Get the current working directory
        """
        if self._forFiles:
            return self._forFiles[0].parent
        return Url('..')

    @property
    def files(self)->typing.Iterable[Url]:
        """
        All of the files we are wanting to apply this to
        """
        return self._forFiles

    @abstractmethod
    def listContextMenuEntries(self)->typing.Iterable[str]:
        """
        Get a list of context menu entry names
        """

    @abstractmethod
    def getContextMenuEntry(self,name:str)->ContextMenuItemBase:
        """
        Get a single context menu entry
        """


class FileExplorerContextMenusBase:
    """
    All registered context menus
    """
    def __init__(self):
        pass

    def getMenuItems(self,
        files:UrlListCompatible
        )->FileExplorerContextMenuBase:
        """
        Get all menu items that apply to one or more files
        """
        ret=FileExplorerContextMenuBase(self,files)
        return ret
