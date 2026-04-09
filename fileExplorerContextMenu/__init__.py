"""
Manage extra file attributes (metadata) attached to a file

For linux, many of the tricks are application-dependent,
or are derived from the XDG Specification
    https://specifications.freedesktop.org/basedir/latest/
And maybe the mime directory
    https://specifications.freedesktop.org/shared-mime-info/latest
"""
import typing
import os
import subprocess
from paths import UrlCompatible,asUrl
from .fileExplorerContextMenuBase import FileExplorerContextMenuBase


# generic
FileExplorerContextMenu:FileExplorerContextMenuBase
def _defaultOpenFileExplorer(
    location:typing.Optional[UrlCompatible]=None
    )->subprocess.Popen:
    """
    Open the default file explorer using shell open
    """
    cmd=['open']
    if location is not None and location:
        cmd.append(str(asUrl(location)))
    return subprocess.Popen(cmd,shell=True,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE)


if os.name=='nt':
    from .windowsExplorerContextMenu import (
        WindowsExplorerContextMenus,openWindowsExplorer)
    ExtendedFileAttributes=WindowsExplorerContextMenus
    openFileExplorer=openWindowsExplorer
else:
    desktopName=os.environ.get('XDG_CURRENT_DESKTOP','').lower()
    if not desktopName:
        raise Exception('No desktop registered')
    if desktopName=='nautilus':
        from .linuxNautilusContextMenu import (
            LinuxNautilusContextMenus,openNautilus)
        ExtendedFileAttributes=LinuxNautilusContextMenus
        openFileExplorer=openNautilus
    elif desktopName=='nemo':
        from .linuxNemoContextMenu import (
            LinuxNemoContextMenus,openNemo)
        ExtendedFileAttributes=LinuxNemoContextMenus
        openFileExplorer=openNemo
    elif desktopName=='cosmic':
        from .linuxCosmicFileExplorer import openCosmic
        openFileExplorer=openCosmic
    else:
        # in case they ignore the exception we will still try to use the default
        openFileExplorer=_defaultOpenFileExplorer
        raise NotImplementedError(f'The desktop "{desktopName}" is not implemented')
