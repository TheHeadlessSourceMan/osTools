"""
Manage extended file attribute metadata on linux
"""
import typing
from paths import UrlCompatible,asFilePath
from .extendedAttributesBase import (
    ExtendedFileAttributesBase,MetadataType,FileAttributeAssignableValue)
try:
    import xattr
except ImportError as e:
    print('xattr not found. Pleas install with:')
    print('    pip install xattr')
    raise e


class LinuxExtendedFileAttributes(ExtendedFileAttributesBase):
    """
    Manage extended file attribute metadata on linux
    """
    def __init__(self,attachedFile:UrlCompatible):
        ExtendedFileAttributesBase.__init__(self,attachedFile)

    def _getAttributeBytes(self,
        name:str
        )->bytes:
        """
        Get the attribute as raw bytes
        """
        return xattr.getxattr(str(asFilePath(self.attachedFile)),f'user.{name}')

    def _getAttributeText(self,
        name:str
        )->str:
        """
        Get the attribute as raw text
        """
        return self._getAttributeBytes(name).decode('utf-8',errors='ignore')

    def _setAttributeBytes(self,
        name:str,
        value:bytes
        ):
        """
        Set the attribute as raw bytes
        """
        xattr.setxattr(str(asFilePath(self.attachedFile)),f'user.{name}',value)

    def _setAttributeText(self,
        name:str,
        value:str
        ):
        """
        Set the attribute as raw text
        """
        self._setAttributeBytes(name,value.encode('utf-8',errors='ignore'))

    def _listAttributes(self)->typing.Iterable[str]:
        """
        List all available attributes
        """
        return listLinuxEmbeddedFileAttributes(self.attachedFile)
LinuxFileMetadata=LinuxExtendedFileAttributes


def listLinuxEmbeddedFileAttributes(attachedFile:UrlCompatible)->typing.Iterable[str]:
    """
    Get a list of all attached attributes
    """
    for s in xattr.listxattr(str(asFilePath(attachedFile))):
        yield s


def getLinuxEmbeddedFileAttributes(attachedFile:UrlCompatible)->LinuxExtendedFileAttributes:
    """
    Manage extended file attribute metadata on linux
    """
    return LinuxExtendedFileAttributes(attachedFile)


def getLinuxEmbeddedFileAttribute(
    attachedFile:UrlCompatible,
    name:str,
    metadataType:MetadataType='bytes'
    )->typing.Any:
    """
    Manage extended file attribute metadata on linux
    """
    return LinuxExtendedFileAttributes(attachedFile).readMetadata(name,metadataType)
getLinuxMetadata=getLinuxEmbeddedFileAttribute


def setLinuxEmbeddedFileAttribute(
    attachedFile:UrlCompatible,
    name:str,
    value:FileAttributeAssignableValue,
    metadataType:typing.Optional[MetadataType]=None
    ):
    """
    Attach data to a file
    """
    LinuxExtendedFileAttributes(attachedFile).setAttribute(name,value,metadataType)
setLinuxMetadata=setLinuxEmbeddedFileAttribute
