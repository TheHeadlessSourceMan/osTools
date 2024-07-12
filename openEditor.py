import typing
import os
import re
import json
from paths import FileLocation
from k_runner.osrun import OsRun


DEFAULT_EDITOR='notepad++'

def globsToRe(globs:typing.Iterable[str])->typing.Pattern:
    return re.compile('|'.join(['(%s)'%re.escape(glob).replace('\\*','.*') for glob in globs]),re.IGNORECASE)

class FileType:
    def __init__(self,json):
        self.json=json
        self.re:typing.Pattern=globsToRe(json['extensions'])

    @property
    def editors(self)->typing.List[str]:
        return self.json['editors']

    def matches(self,filename:str)->bool:
        if self.json['name']=="directory":
            return os.path.isdir(filename)
        return self.re.match(filename) is not None


class _Editors:
    def __init__(self):
        self.json:typing.Dict[str,typing.Any]={}
        self.aliases:typing.Dict[str,str]={}
        self.load()

    def __len__(self):
        """
        how many top-level editors there are
        """
        return len(self.json["editors"])

    def __iter__(self)->typing.Iterator[str]:
        """
        iterate editor names
        """
        return self.json["editors"].keys()

    def keys(self)->typing.Iterator[str]:
        """
        iterate editor names
        """
        return self.json["editors"].keys()

    def load(self,filename=None):
        if filename is None:
            filename=__file__.rsplit('.',1)[0]+'.json'
        with open(filename,'rb') as f:
            self.json=json.loads(f.read().decode('utf-8'))
        self.aliases={}
        for editorName,editor in self.json['editors'].items():
            self.aliases[editorName]=editorName
            for alias in editor['aliases']:
                self.aliases[alias]=editorName
        self.filetypes=[FileType(ft) for ft in self.json['filetypes']]
    
    def get(self,filename:str,editor:typing.Optional[str]=None)->typing.Dict[str,typing.Any]:
        """
        Get the editor for a filename
        """
        if editor is None:
            editor=DEFAULT_EDITOR
            for ft in self.filetypes:
                if ft.matches(filename):
                    editor=ft.editors[0] # TODO: check if editor is actually installed?
        if editor is None:
            ed=None
        else:
            ed=self.aliases.get(editor,None)
        if ed is None:
            print(self.aliases)
            raise IndexError('Unimplemented editor "%s"'%editor)
        return self.json["editors"].get(ed)

    def getEditorCommand(self,filename:str,editor:typing.Optional[str]=None)->str:
        ed=self.get(filename,editor)
        return ed['command']

    def openEditor(
        self,
        fileLocation:typing.Union[str,FileLocation],
        row:int=0,
        col:int=0,
        editor:typing.Optional[str]=None):
        """
        Editors supported:
            notepad++
            vscode
            visualc++
        or some reasonable string along those lines
        """
        if not isinstance(fileLocation,FileLocation):
            fileLocation=FileLocation(fileLocation,row,col)
        template=Editors.getEditorCommand(fileLocation.filename,editor)
        cmd=template.replace('{filename}',os.path.abspath(fileLocation.filename)).replace('{row}',str(fileLocation.row)).replace('{col}',str(fileLocation.col))
        print(cmd)
        OsRun(cmd,shell=True,detatch=True).runAsync()
    open=openEditor
    edit=openEditor

    def __call__(self):
        return self
Editors=_Editors()
EDITORS=Editors

def openEditor(
    fileLocation:typing.Union[str,FileLocation],
    row:int=0,
    col:int=0,
    editor:typing.Optional[str]=None):
    Editors.open(fileLocation,row,col,editor)

def cmdline(args:typing.Iterable[str])->int:
    printhelp=False
    filename:typing.List[str]=[]
    for arg in args:
        if not filename and arg.startswith('-'):
            av=arg.split('=',1)
            av[0]=av[0].lower()
            if av[0]=='--help':
                printhelp=True
            elif av[0]=='--editor':
                editor=av[1]
            else:
                print('ERR: Unknown Argument "%s"'%arg)
                printhelp=True
        else:
            filename.append(arg)
    if not filename:
        printhelp=True
    else:
        openEditor(' '.join(filename),editor=editor)
    if printhelp:
        print('Open an editor for the given vile')
        print('Useage:')
        print('   openEditor.py [options] [filename]')
        print('Options:')
        print('   --help .......... show this help')
        print('   --editor=name ... specify an editor')
        return -1
    return 0
        
        
if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))
    

