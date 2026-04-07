"""
Though based upon nautilus, the actions are somewhat different.

See official documentation:
    https://github-wiki-see.page/m/linuxmint/nemo/wiki/Documentation

And some examples:
    https://github.com/RayCulp/actions-for-nemo-file-manager
"""
import typing
import re
import subprocess
import PIL.Image
from paths import FileUrl,Url,UrlCompatible,asUrl,MimeType,asFileUrl


PercentCodeSplitter=re.compile(r'%[UFPfpDe%xN]')
def decodeNemoSelectionTokens(
    selectionFormat:str,
    selectedFiles:typing.Iterable[UrlCompatible],
    separator:str=' '
    )->str:
    """
    Decode parameters that have selection tokens in them
    """
    selectedFiles=[asUrl(u) for u in selectedFiles]
    def decode(s:str)->str:
        if s==r'%%':
            return r'%'
        elif s==r'%U':
            return separator.join([u.urlString for u in selectedFiles])
        elif s==r'%F':
            return separator.join([str(asFileUrl(u).absolute()) for u in selectedFiles])
        elif s==r'%f' or s==r'%N':
            return separator.join([asFileUrl(u).nameWithExtension for u in selectedFiles])
        elif s==r'%e':
            return separator.join([asFileUrl(u).shortName for u in selectedFiles])
        elif s==r'%P':
            return str(asFileUrl(selectedFiles[0]).absolute().parent)
        elif s==r'%p':
            return asFileUrl(selectedFiles[0]).absolute().parent.shortName
        return ''
    parts:typing.List[str]=[]
    previousIndex=0
    for m in PercentCodeSplitter.finditer(selectionFormat):
        parts.append(selectionFormat[previousIndex:m.start(0)])
        parts.append(decode(str(m.group(0))))
        previousIndex=m.end(0)
    parts.append(selectionFormat[previousIndex:])
    return ''.join(parts)


NemoIconCache:typing.Dict[Url,PIL.Image.Image]={}


class NemoAction:
    """
    A single action for the Nemo file manager

    About 75% of the format is implemented.

    See official documentation:
        https://github-wiki-see.page/m/linuxmint/nemo/wiki/Documentation
    """
    def __init__(self,filename:UrlCompatible):
        self.active:bool=True
        self.name:str=''
        self.comment:str=''
        self.exec:str=''
        self.selection:str=''
        self.extensions:typing.List[str]=[]
        self.dependencies:typing.List[str]=[]
        self.mimeTypes:typing.List[MimeType]=[]
        self.quote:str=''
        self.escapeSpaces:bool=True
        self.terminal:bool=False
        self.iconName:str=''
        self.uriScheme:str=''
        self._dependenciesInstalled:typing.Optional[bool]=None
        self.load(filename)

    @property
    def dependenciesInstalled(self)->bool:
        """
        Are the required dependencies installed?
        """
        if self._dependenciesInstalled is None:
            self._dependenciesInstalled=True
            from packageManagers.linuxPackageInfo import isPackageInstalled
            for dependency in self.dependencies:
                if not isPackageInstalled(dependency):
                    self._dependenciesInstalled=False
                    break
        return self._dependenciesInstalled

    def getName(self,selectedFiles:typing.Iterable[UrlCompatible])->str:
        """
        The name can have selection replacements, so this
        will decode them based upon the files given.
        """
        return decodeNemoSelectionTokens(self.name,selectedFiles,self.separator)

    @property
    def description(self)->str:
        """
        Same thing as comment
        """
        return self.comment

    def getComment(self,selectedFiles:typing.Iterable[UrlCompatible])->str:
        """
        The comment can have selection replacements, so this
        will decode them based upon the files given.
        """
        return decodeNemoSelectionTokens(self.comment,selectedFiles,self.separator)
    getDescription=getComment

    @property
    def icon(self)->typing.Optional[PIL.Image.Image]:
        """
        Get the actual icon image
        """
        iconFilename=self.iconFilename
        if iconFilename is None:
            return None
        ico=NemoIconCache.get(iconFilename,None)
        if ico is None:
            ico=PIL.Image.open(str(iconFilename))
            NemoIconCache[iconFilename]=ico
        return ico

    @property
    def iconFilename(self)->typing.Optional[Url]:
        """
        The icon reference decoded as an actual filename
        """
        if not self.icon:
            return None
        iconFilename=Url(self.iconName,relativeTo=NemoActions.NemoActionsDirectory)
        if not iconFilename.isFile:
            found=False
            for f in iconFilename.parent.iterdir():
                if f.name.startswith(iconFilename.name):
                    iconFilename=f
                    found=True
                    break
            if not found:
                return None
        return iconFilename

    def load(self,filename:UrlCompatible)->None:
        """
        Load the action from the config file
        """
        data=asUrl(filename).read()
        ready=False
        for line in data.split('\n'):
            line=line.strip()
            if not line:
                continue
            if line[0]=='[':
                ready=(line=='[Nemo Action]')
                continue
            if not ready:
                continue
            kv=line.split('=',1)
            if len(kv)!=2:
                continue
            k=kv[0].rstrip()
            v=kv[1].lstrip()
            if k=='Active':
                self.active=v[0].lower()=='t'
            elif k=='Name':
                self.name=v
            elif k=='Comment':
                self.comment=v
            elif k=='Exec':
                self.exec=v
            elif k=='Icon-Name':
                self.iconName=v
            elif k=='Selection':
                self.selection=v
            elif k=='Separator':
                self.separator=v
            elif k=='Extensions':
                if v.endswith(';'):
                    v=v[0:-1]
                self.extensions=[vv.strip() for vv in v.split(';')]
            elif k=='MimeTypes':
                if v.endswith(';'):
                    v=v[0:-1]
                self.mimeTypes=[MimeType(vv.strip()) for vv in v.split(';')]
            elif k=='Terminal':
                self.terminal=v[0].lower()=='t'
            elif k=='EscapeSpaces':
                self.escapeSpaces=v[0].lower()=='t'
            elif k=='Quote':
                self.quote=v
            elif k=='Dependencies':
                if v.endswith(';'):
                    v=v[0:-1]
                self.dependencies=[vv.strip() for vv in v.split(';')]
            elif k=='UriScheme':
                self.uriScheme=v
            elif k=='Conditions':
                if v.endswith(';'):
                    v=v[0:-1]
                self.conditions=[vv.strip() for vv in v.split(';')]
            elif k=='Files':
                if v.endswith(';'):
                    v=v[0:-1]
                self.files=[vv.strip() for vv in v.split(';')]
            elif k=='Locations':
                if v.endswith(';'):
                    v=v[0:-1]
                self.locations=[vv.strip() for vv in v.split(';')]

    def save(self,filename:UrlCompatible)->None:
        """
        Save the action to a config file
        """
        filename=asUrl(filename,relativeTo=NemoActions.NemoActionsDirectory)
        data=['[Nemo Action]']
        data.append(f'Name={self.name}')
        data.append(f'Comment={self.comment}')
        data.append(f'Exec={self.exec}')
        data.append(f'Icon-Name={self.iconName}')
        data.append(f'Selection={self.selection}')
        data.append(f'Quote={self.quote}')
        data.append(f'EscapeSpaces={str(self.escapeSpaces).lower()}')
        data.append(f'Terminal={str(self.terminal).lower()}')
        if self.extensions:
            if len(self.extensions)==1 and self.extensions[0] in ('dir','nodirs','none','any'):
                ext=self.extensions[0]
            else:
                ext=';'.join(self.extensions)+';'
            data.append(f'Extensions={ext}')
        if self.mimeTypes:
            ext=';'.join([str(s) for s in self.mimeTypes])+';'
            data.append(f'Extensions={ext}')
        if self.dependencies:
            d=';'.join(self.dependencies)+';'
            data.append(f'Dependencies={d}')
        if self.conditions:
            d=';'.join(self.conditions)+';'
            data.append(f'Conditions={d}')
        if self.uriScheme:
            data.append(f'UriScheme={self.uriScheme}')

    def appliesToFile(self,filename:UrlCompatible)->bool:
        """
        Check if this action applies to a given file
        """
        if not self.dependenciesInstalled:
            return False
        filename=asUrl(filename)
        if self.uriScheme:
            if filename.protocol!=self.uriScheme:
                return False
        if filename.isDirectory:
            if not self.extensions \
                or (len(self.extensions)==1 and self.extensions[0] in ('dir','any')):
                return True
        elif len(self.extensions)==1 and self.extensions[1] in ('none','nodirs','any'):
            if self.extensions[0]=='none':
                if not filename.ext:
                    return True
            else:
                return True
        else:
            if filename.ext[1:] in self.extensions:
                return True
        return False

    def getExec(self,selectedFiles:typing.Iterable[UrlCompatible])->str:
        """
        Get the final exec string given the set of files
        """
        return decodeNemoSelectionTokens(self.exec,selectedFiles,self.separator)

    def run(self,selectedFiles:typing.Iterable[UrlCompatible])->subprocess.Popen:
        """
        Run the action on a set of files
        """
        return subprocess.Popen(self.getExec(selectedFiles),shell=True,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    __call__=run


class NemoActions:
    """
    All known nemo actions
    """
    NemoActionsDirectory=FileUrl('~/.local/share/nemo/actions',shellReplace=True)

    def __init__(self):
        self._actions:typing.Optional[typing.List[NemoAction]]=None

    @property
    def actionFiles(self)->typing.Iterable[Url]:
        """
        All installed action files
        """
        return self.NemoActionsDirectory.iterdir()

    @property
    def actions(self)->typing.Iterable[NemoAction]:
        """
        All installed actions
        """
        if self._actions is None:
            self._actions=[]
            for f in self.actionFiles:
                action=NemoAction(f)
                self._actions.append(action)
        return self._actions

    def actionsForFile(self,filename:UrlCompatible)->typing.Iterable[NemoAction]:
        """
        Get all actions that applies to a certain file
        """
        for action in self.actions:
            if action.appliesToFile(filename):
                yield action