"""
Access context menus for linux Nautilus/Nemo file explorers.
(Nautilus=Gnome desktop, Nemo=Mint,Cinnamon desktop)

This is based on the DES-EMA (Desktop Entry Specification - Extension for Menus and Actions)
Specification:
    https://gitlab.gnome.org/Archive/filemanager-actions/-/tree/NAUTILUS_ACTIONS_3_2_4/docs/des-ema

For a more user-friendly breakdown, see:
    https://hellosystem.github.io/docs/developer/filer-context-menus.html
"""
import typing
import subprocess
import PIL.Image
from paths import UrlCompatible,Url,asUrl,MimeType
from fileExplorerContextMenu.fileExplorerContextMenuBase import FileExplorerContextMenusBase


class ProfileValuesDict:
    """
    Manage a dict of values
    """
    def __init__(self):
        self._values:typing.Dict[str,typing.List[str]]={}

    def addProfileValues(self,name:str,values:str):
        """
        Add one or more values from a values string
        """
        if values.endswith(';'):
            valuesList=values.split(';')[0:-1]
        else:
            valuesList=[values]
        if name not in self._values:
            self._values[name]=valuesList
        else:
            self._values[name].extend(valuesList)

    def addKeyValueString(self,kvStr:str)->bool:
        """
        Add one or more values from a k=v string.

        Returns True if it worked.
        """
        kv=kvStr.split('=',1)
        if len(kv)!=2:
            return False
        k=kv[0].strip()
        v=kv[1].strip()
        self.addProfileValues(k,v)
        return True

    def getValue(self,name:str,default:str='')->str:
        """
        Get a single (or first) value
        """
        value=self._values.get(name,default)
        if isinstance(value,str):
            return value
        return value[0]
    get=getValue

    def getValues(self,name:str)->typing.Iterable[str]:
        """
        Get values array
        """
        return self._values.get(name,[])


class ActionProfile(ProfileValuesDict):
    """
    A single file profile to match for an action
    """
    def __init__(self,parent:"DesktopEntry",profileName:str):
        ProfileValuesDict.__init__(self)
        self.parent=parent
        self.profileName=profileName

    @property
    def name(self)->str:
        """
        Get the name
        """
        return self.get('Name')

    @property
    def selectionCount(self)->str:
        """
        Get the number of files this profile takes
        returns something like "1",">2","<4",etc
        """
        return self.get('SelectionCount','').replace(' ','')

    @property
    def exec(self)->str:
        """
        Get the exec string
        """
        return self.get('Exec')

    @property
    def path(self)->str:
        """
        Get the working directory for exec
        """
        return self.get('Path','./')

    @property
    def mimeTypes(self)->typing.Iterable[MimeType]:
        """
        Get the mime types
        """
        return [MimeType(mt) for mt in self.getValues('MimeTypes')]

    @property
    def schemes(self)->typing.Iterable[str]:
        """
        Get the url protocol schemes
        """
        return self.getValues('Schemes')

    def callOnFile(self,filename:UrlCompatible,verify:bool=True):
        """
        Call this action on a single file
        """
        return self.callOnFiles([filename],verify)

    def callOnFiles(self,
        filenames:typing.Iterable[UrlCompatible],
        verify:bool=True
        )->subprocess.Popen:
        """
        Call this action on a single file
        """
        fnArray=[]
        for filename in filenames:
            filename=asUrl(filename).absolute()
            if verify and not self.appliesToFile(filename):
                raise AttributeError(f'Action "{self.name}" does not apply to "{filename}"')
            s=str(filename)
            if s.find(' '):
                s=f'"{s}"'
            fnArray.append(s)
        sc=self.selectionCount
        if sc:
            if sc[0]==">":
                if len(fnArray)<=int(sc[1:]):
                    raise AttributeError(f'Requires more than {int(sc[1:])} files ({len(fnArray)} given).') # pylint: disable=line-too-long
            elif sc[0]=="<":
                if len(fnArray)>=int(sc[1:]):
                    raise AttributeError(f'Requires less than {int(sc[1:])} files ({len(fnArray)} given).') # pylint: disable=line-too-long
            elif len(fnArray)!=int(sc[1:]):
                raise AttributeError(f'Requires exactly {int(sc[1:])} files ({len(fnArray)} given).') # pylint: disable=line-too-long
        # replace working directory
        p=self.path
        if p.find(' ')>=0:
            p=f'"{p}"'
        cmd=self.exec.replace(r'%d',p)
        return subprocess.Popen(cmd,shell=True,cwd=self.path,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)

    def appliesToFile(self,filename:UrlCompatible)->bool:
        """
        Check if this action applies to a given file
        """
        filename=asUrl(filename)
        if filename.protocol not in self.schemes:
            return False
        if hasattr(filename,'mimeType') \
            and filename.mimeType is not None \
            and filename.mimeType in self.mimeTypes:
            # TODO: what about mime type "all/allfiles"
            return True
        return False


class DesktopEntry:
    """
    A single desktop entry for linux Nautilus/Nemo file explorers.
    (Nautilus=Gnome desktop, Nemo=Mint,Cinnamon desktop)

    This is based on the DES-EMA (Desktop Entry Specification - Extension for Menus and Actions)
    Specification:
        https://gitlab.gnome.org/Archive/filemanager-actions/-/tree/NAUTILUS_ACTIONS_3_2_4/docs/des-ema

    For a more user-friendly breakdown, see:
        https://hellosystem.github.io/docs/developer/filer-context-menus.html
    """
    def __init__(self,actionFilename:UrlCompatible):
        self._profiles:typing.Dict[str,ActionProfile]={}
        self._valuesDict:ProfileValuesDict=ProfileValuesDict()
        self.filename:Url
        self.load(actionFilename)

    def load(self,filename:UrlCompatible)->None:
        """
        Load the file
        """
        self.filename=Url(filename)
        data=self.filename.readString()
        ready=False
        self._profiles={}
        self._valuesDict=ProfileValuesDict()
        currentDict=self._valuesDict
        for line in data.split('\n'):
            line=line.strip()
            if not line:
                continue
            if not ready:
                if line=='[Desktop Entry]':
                    ready=True
                else:
                    raise ValueError('Not a [Desktop Entry] file')
            if line[0]=='[':
                if line.startswith('[X-Action-Profile '):
                    profileName=line.split(' ',1)[-1][0:-1].strip()
                    profile=ActionProfile(self,profileName)
                    currentDict=profile
                    self._profiles[profileName]=profile
                else:
                    print(f'Skipping unknown section {line}')
                    currentDict=ProfileValuesDict()
            else:
                currentDict.addKeyValueString(line)

    @property
    def name(self)->str:
        """
        Get the name
        """
        return self._valuesDict.get('Name')

    @property
    def type(self)->str:
        """
        Get the type ("" for action, "Menu" for context menu)
        """
        return self._valuesDict.get('Type')

    @property
    def iconName(self)->str:
        """
        Get the icon name
        """
        return self._valuesDict.get('Icon')

    @property
    def icon(self)->typing.Optional[PIL.Image.Image]:
        """
        Get the icon
        """
        filename=self.iconName
        return PIL.Image.open(filename)

    def callOnFile(self,filename:UrlCompatible,verify:bool=True):
        """
        Call this action on a single file
        """
        filename=asUrl(filename)
        if verify and not self.appliesToFile(filename):
            raise AttributeError(f'Action "{self.name}" does not apply to "{filename}"')

    def appliesToFile(self,filename:UrlCompatible)->bool:
        """
        Check if this action applies to a given file
        """
        filename=asUrl(filename)
        for profile in self._profiles.values():
            if profile.appliesToFile(filename):
                return True
        return False


class LinuxNautilusContextMenus(FileExplorerContextMenusBase):
    """
    Access context menus for linux Nautilus file explorers.
    (Nautilus is the default fie explorer for Gnome desktop)

    This is based on the DES-EMA (Desktop Entry Specification - Extension for Menus and Actions)
    Specification:
        https://gitlab.gnome.org/Archive/filemanager-actions/-/tree/NAUTILUS_ACTIONS_3_2_4/docs/des-ema

    For a more user-friendly breakdown, see:
        https://hellosystem.github.io/docs/developer/filer-context-menus.html
    """
    def __init__(self,actionsDirectory:typing.Optional[UrlCompatible]=None):
        if actionsDirectory is None:
            actionsDirectory="~/.local/share/file-manager/actions"
        self._actionsDirectory=Url(actionsDirectory)
        self._actions:typing.Optional[typing.List[DesktopEntry]]=None

    @property
    def actions(self)->typing.Iterable[DesktopEntry]:
        """
        Get all of the actions
        """
        if self._actions is None:
            self.reload()
        return iter(self._actions) # type: ignore

    @property
    def actionsDirectory(self)->Url:
        """
        Get the actions directory
        """
        return Url(self._actionsDirectory)

    @property
    def actionFiles(self)->typing.Iterable[Url]:
        """
        Get all of the action files in the actions directory
        """
        yield from self._actionsDirectory.iterdir()

    def reload(self)->None:
        """
        Reload the list of actions from scratch
        """
        self._actions=[]
        for f in self.actionFiles:
            action=DesktopEntry(f)
            self._actions.append(action)

    def getActionsFor(self,filename:UrlCompatible)->typing.Iterable[DesktopEntry]:
        """
        Get all actions that apply to a particular file
        """
        for action in self.actions:
            if action.appliesToFile(filename):
                yield action


def openNautilus(
    location:typing.Optional[UrlCompatible]=None,
    selection:typing.Optional[UrlCompatible]=None
    )->subprocess.Popen:
    """
    Open the nemo file explorer
    """
    cmd=['nautilus','-w']
    if location is not None and location:
        cmd.append(str(asUrl(location)))
        if selection is not None:
            selection=asUrl(selection)
            cmd.append('-s')
            cmd.append(str(selection))
    return subprocess.Popen(cmd,shell=True,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE)


def replaceParameters(formatString:str,files:typing.Iterable[UrlCompatible])->str:
    r"""
    Replace desktop % code parameters with what they should be
    """
    import re
    files=[asUrl(f) for f in files]
    percentCodes:typing.Dict[str,typing.Union[str,int,None]]={r'%%':r'%'}
    def enquot(s:typing.Union[str,Url])->str:
        s=str(s)
        if s.find(' ')>=0:
            return f'"{s}"'
        return s
    def getPercentCode(pc:str)->str:
        ret=percentCodes.get(pc,None)
        if ret is None:
            if pc==r'%b':
                ret=enquot(files[0].name)
            elif pc==r'%B':
                ret=' '.join([enquot(f.name) for f in files])
            elif pc==r'%c':
                ret=str(len(files))
            elif pc==r'%d':
                ret=enquot(files[0].absolute().parent)
            elif pc==r'%D':
                ret=' '.join([enquot(f.absolute().parent) for f in files])
            elif pc==r'%f':
                ret=enquot(files[0].absolute())
            elif pc==r'%F':
                ret=' '.join([enquot(f.absolute()) for f in files])
            elif pc==r'%n':
                u=files[0].username
                if u is None:
                    u=''
                ret=enquot(u)
            elif pc==r'%o':
                ret=""
            elif pc==r'%O':
                ret=""
            elif pc==r'%p':
                ret=files[0].port
            elif pc==r'%s':
                ret=enquot(files[0].protocol)
            elif pc==r'%u':
                ret=enquot(files[0].urlString)
            elif pc==r'%U':
                ret=' '.join([enquot(f.urlString) for f in files])
            elif pc==r'%w':
                ret=enquot(files[0].absolute())
            elif pc==r'%W':
                ret=' '.join([enquot(f.absolute()) for f in files])
            percentCodes[pc]=ret
        return str(ret)
    percentSplitter=re.compile(r'%[bBcdDfFmFnoOpsuUwWxX%]')
    parts=[]
    lastIdx=0
    for match in percentSplitter.finditer(formatString):
        parts.append(formatString[lastIdx:match.start(0)])
        parts.append(getPercentCode(match.group(0)))
        lastIdx=match.end(0)
    parts.append(formatString[lastIdx:])
    return ' '.join(parts)
