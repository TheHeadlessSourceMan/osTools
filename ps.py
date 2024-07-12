"""
Tools to run powershell commands and interperet the results in a pythonic way
"""
import typing
from collections.abc import Iterable
import re
import k_runner.osrun as osrun

CmdCompatible=typing.Union[str,typing.Iterable[str]]
PsDataResult=typing.Dict[str,str]

psTableHeader = re.compile(r'[^\s]+')
def psTableDissect(lines:typing.Union[typing.List[str],str])->typing.Iterable[PsDataResult]:
    """
    convert a powershell-formatted table into something useable
    
    :lines: either a list of lines or a string to split using '\n'
    
    returns json-compatible [{k:v},...]
    """
    if isinstance(lines,str):
        lines=lines.split('\n')
    ret:typing.List[typing.Dict]=[]
    header:typing.List[str]=[]
    colIndices:typing.List[int]=[]
    separator=None
    for line in lines:
        if not line:
            continue
        if not header:
            for m in psTableHeader.finditer(line):
                header.append(m.group(0))
                colIndices.append(m.start(0))
            if colIndices:
                colIndices.append(-1)
        elif separator is None:
            # Consume separator row
            separator=line
        else:
            row={}
            for i,k in enumerate(header):
                v=line[colIndices[i]:colIndices[i+1]]
                row[k]=v.strip()
            ret.append(row)
    return ret


def psColonListDissect(lines:typing.Union[typing.List[str],str])->PsDataResult:
    """
    convert a powershell-formatted key:value list into something useable
    
    eg
        thisitem    : 1
        anotheritem : 2
        ...
    
    :lines: either a list of lines or a string to split using '\n'
    
    returns json-compatible {k:v}
    """
    ret={}
    if isinstance(lines,str):
        lines='\n'.split(lines)
    for line in lines:
        if not line:
            continue
        kv=line.split(':',1)
        ret[kv[0].strip()]=kv[1].strip()
    return ret


def psCommand(cmd:CmdCompatible)->str:
    """
    Run a powershell command and return the output lines
    """
    if not isinstance(cmd,str):
        cmd=' '.join(cmd)
    result=osrun.osrun(['powershell','-c',cmd])
    if result.err:
        raise Exception(result.err)
    return result.out


def psCommandWithTableOutput(cmd:CmdCompatible)->typing.Iterable[PsDataResult]:
    """
    Run a powershell command that expects a table as output
    result will be converted to [{k:v}] with psTableDissect()
    """
    return psTableDissect(psCommand(cmd))


def psCommandWithColonListOutput(cmd:CmdCompatible)->PsDataResult:
    """
    Run a powershell command that expects a colon as output
    
    eg
        thisitem    : 1
        anotheritem : 2
        ...
    
    result will be converted to {k:v} with psColonListDissect()
    """
    return psColonListDissect(psCommand(cmd))


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    didSomething=False
    printhelp=False
    output=''
    if not isinstance(args,Iterable) or isinstance(args,str):
        args=list(args)
    for i, arg in enumerate(args):
        if arg.startswith('-'):
            av=arg.split('=',1)
            av[0]=av[0].lower()
            if av[0] in ('-h','--help'):
                printhelp=True
            elif av[0]=='--output':
                if len(av)>1:
                    output=av[1]
                else:
                    output=''
            else:
                printhelp=True
        else:
            didSomething=True
            if output=='table':
                print(psCommandWithTableOutput(args[i:]))
            elif output=='list':
                print(psCommandWithColonListOutput(args[i:]))
            else:
                print(psCommand(args[i:]))
            break
            
    if printhelp or not didSomething:
        print('USEAGE:')
        print('  ps [options] [commands]')
        print('OPTIONS:')
        print('  -h ................................. this help')
        print('  --output=list|table ................ specify output type to dissect (default=none)')
        return 1
    return 0


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])