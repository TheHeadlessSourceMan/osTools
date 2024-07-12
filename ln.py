"""
windows link handling tools

among other things implements the linux "ln" functionality

Works great from the command line too!
"""
import typing
import os
import sys
import subprocess
    
def unlink(path:str)->None:
    cmd='rmdir "%s"'%path
    po=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    _,errb=po.communicate()
    err=errb.decode('utf-8',errors='ignore').strip()
    if err:
        if err.startswith('The system cannot find the file specified'):
            # if it doesn't exist, then it's already "unlinked"!
            return
        raise Exception(err)

def linkTarget(path:str)->str:
    """
    get the end target of a symbolic link or shorcut

    NOTE: can follow a series of links/shortcuts and has
        loop detection for safety

    NOTE: helpfully, if you pass an actual file's path in, 
        will still return the same path back out.
        Eg:
            given: "linkname" links to "filename"
            linkTarget(linkname)=>filename
            linkTarget(filename)=>filename
    """
    visited=set()
    ret=path
    while True: # keep following links as long as they keep changing
        if ret in visited:
            raise Exception(f'Circular link "{ret}"')
        visited.add(ret)
        cmd=['powershell','-command','(Get-Item',ret,').Target']
        po=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        #print('$>',' '.join(cmd))
        out,err=po.communicate()
        err=err.strip()
        if err:
            raise Exception(err)
        changed=out.strip().decode('utf-8',errors='ignore')
        #print(changed)
        if not changed or changed==ret: # no change
            if ret.endswith('.lnk'):
                # check .lnk shortcut
                cmd2=['powershell','-command','(New-Object','-ComObject',f"WScript.Shell).CreateShortcut('{ret}').TargetPath"]
                po=subprocess.Popen(cmd2,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                #print('$>',' '.join(cmd2))
                out,err=po.communicate()
                err=err.strip()
                if err:
                    raise Exception(err)
                changed=out.strip().decode('utf-8',errors='ignore')
            #print(changed)
            if not changed or changed==ret: # still no change
                break
        ret=changed
    return ret

def ln(fromPath:str,toPath:str)->None:
    if os.sep!='/':
        fromPath=fromPath.replace('/',os.sep)
        toPath=toPath.replace('/',os.sep)
    cmd=['mklink']
    if os.path.isdir(fromPath):
        cmd.append('/D')
    cmd.append(toPath)
    cmd.append(fromPath)
    po=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    out,_=po.communicate()
    print(out.decode('utf-8'))
   
def cmdline(args:typing.Iterable[str])->int:
    printhelp=False
    fromTo=[]
    behaviour='link'
    for arg in args:
        if arg.startswith('-'):
            av=arg.split('=',1)
            av[0]=av[0].lower()
            if av[0]=='--help':
                printhelp=True
            elif av[0]=='-s':
                if len(av)>1:
                    fromTo.append(av[1])
                behaviour='link'
            elif av[0] in ('-u','--unlink'):
                if len(av)>1:
                    fromTo.append(av[1])
                behaviour='unlink'
            elif av[0] in ('-t','--target'):
                if len(av)>1:
                    fromTo.append(av[1])
                behaviour='target'
            else:
                print('ERR: Unknown Argument "%s"'%arg)
                printhelp=True
        else:
            fromTo.append(arg)
    if behaviour=='link':
        if len(fromTo)!=2:
            print('Unknown useage')
            printhelp=True
        else:
            ln(*fromTo)
    elif behaviour=='unlink':
        if len(fromTo)!=1:
            print('Unknown useage')
            printhelp=True
        else:
            unlink(fromTo[0])
    elif behaviour=='target':
        if len(fromTo)!=1:
            print('Unknown useage')
            printhelp=True
        else:
            print(linkTarget(fromTo[0]))
    if printhelp:
        print('Implementation of linux symbolic link command "ln" on windows')
        print('Useage:')
        print('   ln.py [options] [fromFile] [toLinkName]')
        print('Options:')
        print('   --help ......... show this help')
        print('   -s ............. symbolic flag (ignored)')
        print('   -u,--unlink .... unlink')
        print('   -t,--target .... get the target instead')
        return -1
    return 0
        
        
if __name__=='__main__':
    import sys
    sys.exit(cmdline(sys.argv[1:]))