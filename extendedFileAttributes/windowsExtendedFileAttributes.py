"""
Manage extended file attribute metadata on windows
"""
import typing
from paths import UrlCompatible,asFilePath
from .extendedAttributesBase import (
    ExtendedFileAttributesBase,MetadataType,FileAttributeAssignableValue)


class WindowsExtendedFileAttributes(ExtendedFileAttributesBase):
    """
    Manage extended file attribute metadata on Windows
    """
    def __init__(self,attachedFile:UrlCompatible):
        ExtendedFileAttributesBase.__init__(self,attachedFile)

    def _getAttributeBytes(self,
        name:str
        )->bytes:
        """
        Get the attribute as raw bytes
        """
        adsPath=f"{asFilePath(self.attachedFile)}:{name}"
        try:
            with open(adsPath,'rb') as f:
                return f.read()
        except FileNotFoundError:
            raise IndexError(f'No attribute {name}')

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
        adsPath=f"{asFilePath(self.attachedFile)}:{name}"
        with open(adsPath,'wb') as f:
            f.write(value)

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
        return listWindowsEmbeddedFileAttributes(self.attachedFile)
WindowsFileMetadata=WindowsExtendedFileAttributes


def listWindowsEmbeddedFileAttributes(attachedFile:UrlCompatible)->typing.Iterable[str]:
    """
    Get a list of all attached attributes
    """
    import subprocess
    attachedFile=asFilePath(attachedFile)
    try:
        # Using 'dir /R' to list ADS
        cmd=['cmd','/c',f'dir "{attachedFile}" /R']
        result=subprocess.run(cmd,capture_output=True,text=True)
        print(result.stdout)
        # TODO: not sure if decoding is correct.  It's probably not.
        for line in result.stdout.strip().split('\n'):
            yield line.strip()
    except Exception as e:
        print(f"Error curred: {e}")
listWindowsMetadata=listWindowsEmbeddedFileAttributes


def getWindowsEmbeddedFileAttributes(attachedFile:UrlCompatible)->WindowsExtendedFileAttributes:
    """
    Manage extended file attribute metadata on windows
    """
    return WindowsExtendedFileAttributes(attachedFile)


def getWindowsEmbeddedFileAttribute(
    attachedFile:UrlCompatible,
    name:str,
    metadataType:MetadataType='bytes'
    )->typing.Any:
    """
    Manage extended file attribute metadata on windows
    """
    return WindowsExtendedFileAttributes(attachedFile).readMetadata(name,metadataType)
getWindowsMetadata=getWindowsEmbeddedFileAttribute


def setWindowsEmbeddedFileAttribute(
    attachedFile:UrlCompatible,
    name:str,
    value:FileAttributeAssignableValue,
    metadataType:typing.Optional[MetadataType]=None
    ):
    """
    Attach data to a file
    """
    WindowsExtendedFileAttributes(attachedFile).setAttribute(name,value,metadataType)
setWindowsMetadata=setWindowsEmbeddedFileAttribute
