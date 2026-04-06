"""
Manage extra file attributes (metadata) attached to a file
"""
import os
from .extendedAttributesBase import ExtendedFileAttributesBase

ExtendedFileAttributes:ExtendedFileAttributesBase

if os.name=='nt':
    from windowsExtendedFileAttributes import *
    ExtendedFileAttributes=WindowsExtendedFileAttributes
    FileMetadata=WindowsFileMetadata
    listEmbeddedFileAttributes=listWindowsEmbeddedFileAttributes
    listMetadata=listWindowsMetadata
    getEmbeddedFileAttributes=getWindowsEmbeddedFileAttributes
    getEmbeddedFileAttribute=getWindowsEmbeddedFileAttribute
    getMetadata=getWindowsMetadata
    setEmbeddedFileAttribute=setWindowsEmbeddedFileAttribute
    setMetadata=setWindowsMetadata
else:
    from linuxExtendedFileAttributes import *
    ExtendedFileAttributes=LinuxExtendedFileAttributes
    FileMetadata=LinuxFileMetadata
    listEmbeddedFileAttributes=listLinuxEmbeddedFileAttributes
    listMetadata=listLinuxMetadata
    getEmbeddedFileAttributes=getLinuxEmbeddedFileAttributes
    getEmbeddedFileAttribute=getLinuxEmbeddedFileAttribute
    getMetadata=getLinuxMetadata
    setEmbeddedFileAttribute=setLinuxEmbeddedFileAttribute
    setMetadata=setLinuxMetadata
