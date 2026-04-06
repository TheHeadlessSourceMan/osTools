"""
Common base for managing metadata
"""
from abc import abstractmethod
import typing
import json
from jsonSerializeable import JsonObj
import PIL.Image
from paths import Url,UrlCompatible


MetadataType=typing.Literal['bytes','jpeg','png','json','text','str']
FileAttributeAssignableValue=typing.Union[str,bytes,bytearray,JsonObj,PIL.Image.Image]


class ExtendedFileAttributesBase:
    """
    Common base for managing metadata

    To manage this from the command line you can do
        sudo apt-get install attr
    Then get data
        getfattr -n user.metadata_name /path/to/your/file
    And set data
        setfattr -n user.metadata_name -v "Your metadata value" /path/to/your/file

    """
    def __init__(self,attachedFile:UrlCompatible):
        self._attachedFile=Url(attachedFile)
        self._attributes:typing.Dict[str,typing.Optional[FileAttributeAssignableValue]]

    @property
    def attributeNames(self)->typing.Iterable[str]:
        """
        Get all attribute names
        """
        if not self._attributes:
            self.refresh()
        yield from self._attributes.keys()
    @property
    def names(self)->typing.Iterable[str]:
        """
        Get all attribute names
        """
        return self.attributeNames
    @property
    def keys(self)->typing.Iterable[str]:
        """
        Get all keys like a dict does
        """
        return self.attributeNames
    def __iter__(self)->typing.Iterable[str]:
        """
        Get all keys like a dict does
        """
        return self.attributeNames

    def values(self)->typing.Iterable[FileAttributeAssignableValue]:
        """
        Get all values like a dict does
        """
        for _,v in self.items():
            yield v

    def items(self
        )->typing.Iterable[typing.Tuple[str,FileAttributeAssignableValue]]:
        """
        Get all items like a dict does
        """
        for k in self.keys:
            v=self.get(k)
            if v is not None:
                yield k,v

    def __len__(self)->int:
        return len(list(self.attributeNames))

    def __getitem__(self,k:str)->FileAttributeAssignableValue:
        if not self._attributes:
            self.refresh()
        v=self._attributes[k]
        if v is None:
            v=self.readMetadata(k)
            self._attributes[k]=v
        return v

    def get(self,
        k:str,
        default:typing.Optional[FileAttributeAssignableValue]=None
        )->typing.Optional[FileAttributeAssignableValue]:
        """
        Get a metadata attribute value
        """
        if not self._attributes:
            self.refresh()
        if k not in self._attributes:
            return default
        return self[k]

    def refresh(self,force:bool=True):
        """
        Refresh the attributes list
        """
        if force:
            self._attributes={}
        if not self._attributes:
            for name in self._listAttributes():
                self._attributes[name]=None

    @property
    def attachedFile(self)->Url:
        """
        The file these attributes are attached to
        """
        return self._attachedFile
    @typing.overload
    def readMetadata(self,
        name:str,
        metadataType:typing.Literal['text','str']
        )->str:
        ...
    @typing.overload
    def readMetadata(self,
        name:str,
        metadataType:typing.Literal['jpeg','png']
        )->PIL.Image.Image:
        ...
    @typing.overload
    def readMetadata(self,
        name:str,
        metadataType:typing.Literal['bytes']
        )->bytes:
        ...
    @typing.overload
    def readMetadata(self,
        name:str,
        metadataType:typing.Literal['json']
        )->JsonObj:
        ...
    def readMetadata(self,
        name:str,
        metadataType:MetadataType='bytes'
        )->FileAttributeAssignableValue:
        """
        Get a particular type of metadata
        """
        if metadataType=='bytes':
            return self._getAttributeBytes(name)
        elif metadataType in ('text','str'):
            return self._getAttributeText(name)
        elif metadataType in ('png','jpeg'):
            data=self._getAttributeBytes(name)
            img=PIL.Image.Image()
            img.frombytes(data,decoder_name=metadataType)
            return img
        elif metadataType=='json':
            return json.loads(self._getAttributeText(name))
        raise AttributeError(f'Unknown format type {metadataType}')

    @abstractmethod
    def _getAttributeBytes(self,
        name:str
        )->bytes:
        """
        Get the attribute as raw bytes
        """

    @abstractmethod
    def _getAttributeText(self,
        name:str
        )->str:
        """
        Get the attribute as raw text
        """

    def setAttribute(
        self,
        name:str,
        value:FileAttributeAssignableValue,
        metadataType:typing.Optional[MetadataType]=None
        ):
        """
        Attach data to a file
        """
        if metadataType is None:
            # best guess based upon data type
            if isinstance(value,str):
                metadataType='str'
            elif isinstance(value,PIL.Image.Image):
                metadataType=value.format # type: ignore
            elif isinstance(value,(dict,list)):
                metadataType='json'
            else:
                metadataType='bytes'
        if metadataType in ('str','text'):
            self._setAttributeText(name,str(value))
        elif metadataType=='json':
            if not isinstance(value,(list,dict)):
                value=json.loads(str(value))
            self._setAttributeText(name,json.dumps(value))
        else:
            if not isinstance(value,bytes):
                if isinstance(value,PIL.Image.Image):
                    if metadataType=='bytes':
                        encoder='raw'
                    else:
                        encoder=metadataType
                    value=value.tobytes(encoder) # type: ignore
                else:
                    value=str(value).encode('utf-8')
            self._setAttributeBytes(name,value)

    @abstractmethod
    def _setAttributeBytes(self,
        name:str,
        value:bytes
        ):
        """
        Set the attribute as raw bytes
        """

    @abstractmethod
    def _setAttributeText(self,
        name:str,
        value:str
        ):
        """
        Set the attribute as raw text
        """

    @abstractmethod
    def _listAttributes(self)->typing.Iterable[str]:
        """
        List all available attributes
        """
