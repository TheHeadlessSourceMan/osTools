"""
This is experimental to see if somebody has a directory locked
and what process is the culprit

see also:
    instructions - https://devblogs.microsoft.com/oldnewthing/20120217-00/?p=8283
    dll reference - https://docs.microsoft.com/en-us/windows/win32/api/restartmanager/nf-restartmanager-rmgetlist
""" # noqa: E501 # pylint: disable=line-too-long
import typing
import os
from dataclasses import dataclass

try:
    import win32api # type: ignore
    import win32con # type: ignore
    import pywintypes # type: ignore
    hasWindowsTools=True
except ImportError:
    hasWindowsTools=False
import ctypes

rstrtmgr=ctypes.windll.Rstrtmgr # restart manager dll

CCH_RM_MAX_APP_NAME=255
CCH_RM_SESSION_KEY=512#255
CCH_RM_MAX_SVC_NAME=63
class FILETIME(ctypes.c_ulong):
    """
    Windows FILETIME structure
    """
class RM_UNIQUE_PROCESS(ctypes.Structure):
    """
    https://docs.microsoft.com/en-us/windows/win32/api/restartmanager/ns-restartmanager-rm_unique_process
    """
    _fields_=[
        ("dwProcessId",ctypes.c_uint),
        ("ProcessStartTime",FILETIME)]
class RM_APP_TYPE(ctypes.c_uint):
    """
    https://docs.microsoft.com/en-us/windows/win32/api/restartmanager/ne-restartmanager-rm_app_type
    """
    RmUnknownApp = 0
    RmMainWindow = 1
    RmOtherWindow = 2
    RmService = 3
    RmExplorer = 4
    RmConsole = 5
    RmCritical = 1000

class RM_PROCESS_INFO(ctypes.Structure):
    """
    https://docs.microsoft.com/th-th/windows/win32/api/restartmanager/ns-restartmanager-rm_process_info
    """
    _fields_=[
        ("Process",RM_UNIQUE_PROCESS),
        ("strAppName",ctypes.c_wchar*(CCH_RM_MAX_APP_NAME+1)),
        ("strServiceShortName",ctypes.c_wchar*(CCH_RM_MAX_SVC_NAME+1)),
        ("ApplicationType",RM_APP_TYPE),
        ("AppStatus",ctypes.c_uint),
        ("TSSessionId",ctypes.c_uint),
        ("bRestartable",ctypes.c_bool)]
    raise NotImplementedError()
    # TODO: I don't know what this is, but it looks incomplete
    # c_uint_p=ctypes.POINTER(ctypes.c_uint)
    # RM_PROCESS_INFO_p=ctypes.POINTER(RM_PROCESS_INFO)
    # rstrtmgr.RmStartSession.restype=ctypes.c_uint
    # rstrtmgr.RmStartSession.argtypes=c_uint_p,ctypes.c_uint,ctypes.c_wchar_p
    # rstrtmgr.RmRegisterResources.restype=ctypes.c_uint
    # rstrtmgr.RmRegisterResources.argtypes=ctypes.c_uint,ctypes.c_uint,ctypes.POINTER(ctypes.c_wchar_p),ctypes.c_uint,ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p
    # rstrtmgr.RmGetList.restype=ctypes.c_uint
    # rstrtmgr.RmGetList.argtypes=ctypes.c_uint,c_uint_p,c_uint_p,RM_PROCESS_INFO_p,c_uint_p
    # rstrtmgr.RmEndSession.restype=ctypes.c_uint
    # rstrtmgr.RmEndSession.argtypes=[ctypes.c_uint]

@dataclass
class ProcessInfo:
    """
    Info about a given process
    """
    name:str=''
    pid:int=0
    appType:str=''
    _fullName:typing.Optional[str]=None
    processStartTime:int=0
    _processExitTime:typing.Optional[int]=None
    _processKernelTime:typing.Optional[int]=None
    _processUserTime:typing.Optional[int]=None

    @property
    def processExitTime(self)->int:
        """
        When the process exited
        (if still running, return 0)
        """
        if self._processExitTime is None:
            self._getProcessInfo()
        if self._processExitTime is None:
            return 0
        return self._processExitTime

    @property
    def processKernelTime(self)->int:
        """
        Relative measure of how much time the process is consuming
        in the kernel space
        """
        if self._processKernelTime is None:
            self._getProcessInfo()
        if self._processKernelTime is None:
            return 0
        return self._processKernelTime

    @property
    def processUserTime(self)->int:
        """
        Relative measure of how much time the process is consuming
        in the user space
        """
        if self._processUserTime is None:
            self._getProcessInfo()
        if self._processUserTime is None:
            return 0
        return self._processUserTime

    @property
    def fullName(self)->str:
        """
        Full command line of the process
        """
        if self._fullName is None:
            self._getProcessInfo()
        if self._fullName is None:
            return self.name
        return self._fullName

    def _getProcessInfo(self):
        """
        Fetch the process info from the system
        """
        ftCreate=FILETIME(0)
        ftExit=FILETIME(0)
        ftKernel=FILETIME(0)
        ftUser=FILETIME(0)
        if self.pid!=0:
            hProcess=win32api.OpenProcess(
                win32con.PROCESS_QUERY_LIMITED_INFORMATION,
                pywintypes.FALSE,
                self.pid)
            hProcess=win32api.OpenProcess(
                win32con.PROCESS_QUERY_LIMITED_INFORMATION,
                False,
                self.pid)
            if hProcess:
                processStartTime=ctypes.c_uint(self.processStartTime)
                if win32api.GetProcessTimes(
                    hProcess,
                    ctypes.pointer(ftCreate),
                    ctypes.pointer(ftExit),
                    ctypes.pointer(ftKernel),
                    ctypes.pointer(ftUser)) \
                    and \
                    win32api.CompareFileTime(
                    ctypes.pointer(processStartTime),
                    ctypes.pointer(ftCreate)) == 0:
                    #
                    imageName=ctypes.c_wchar*win32con.MAX_PATH
                    imageNameLen=ctypes.c_uint(win32con.MAX_PATH)
                    if win32api.QueryFullProcessImageNameW(
                        hProcess,0,imageName,
                        ctypes.pointer(imageNameLen)) \
                        and imageNameLen<=win32con.MAX_PATH:
                        #
                        self._fullName=imageName
                win32api.CloseHandle(hProcess)
        return (ftCreate,ftExit,ftKernel,ftUser)

    def __repr__(self)->str:
        ret=[]
        ret.append('0x%08X %s'%(self.pid,self.name))
        ret.append(self.fullName)
        if self.appType:
            ret.append(self.appType)
        if self.processStartTime!=0:
            ret.append(f'start: {self.processStartTime}')
        if self.processExitTime!=0:
            ret.append(f'exit: {self.processExitTime}')
        if self.processKernelTime!=0:
            ret.append(f'kernel: {self.processKernelTime}')
        if self.processUserTime!=0:
            ret.append(f'user: {self.processUserTime}')
        return '\n   '.join(ret)


def processLockingFile(
    filename:str,
    recursive:bool=False,
    ignore:typing.Optional[typing.Iterable[str]]=None,
    noExpand:bool=False
    )->typing.Generator[ProcessInfo,None,None]:
    """
    Determine all processes that have locked a given file.

    :recursive: if filename is a directory, keep going
        with subdirectories and files
    :noExpand: do not try to expand shell variables in the filename
        (main purpose is so this can be called recursively)

    Implementation is to query the "restart manager" to get this information
    (You know, how every time you try to shut down winda's says
    "you can't because these apps are preventing it")

    See also:
        https://docs.microsoft.com/th-th/windows/win32/api/_rstmgr/
    """
    if not noExpand:
        filename=os.path.abspath(os.path.expandvars(filename))
    if filename in ignore:
        return
    if ignore is None:
        ignore=tuple()
    print(f'Checking "{filename}"')
    if not isinstance(ignore,list):
        ignore=list(ignore)
    ignore.append(filename)
    dwSession=ctypes.c_uint()
    szSessionKey=ctypes.create_unicode_buffer(CCH_RM_SESSION_KEY+1)
    dwError=rstrtmgr.RmStartSession(ctypes.pointer(dwSession),0,szSessionKey)
    #print(f'RmStartSession key={szSessionKey.value} session={dwSession.value}') # noqa: E501 # pylint: disable=line-too-long
    if dwError!=0: # success
        raise Exception('[Windows error 0x%02X] %s'%(
            dwError,win32api.FormatMessage(dwError)))
    pszFile=ctypes.c_wchar_p(filename)
    numFiles=1
    dwError=rstrtmgr.RmRegisterResources(
        dwSession,numFiles,ctypes.byref(pszFile),0,None,0,None)
    #print(f'RmRegisterResources({pszFile.value})')
    if dwError!=0: # success
        raise Exception('[Windows error 0x%02X] %s'%(
            dwError,win32api.FormatMessage(dwError)))
    dwReason=ctypes.c_uint()
    nProcInfoNeeded=ctypes.c_uint()
    numProcs=10
    nProcInfo=ctypes.c_uint(numProcs)
    rgpi=(RM_PROCESS_INFO*numProcs)()
    pRgpi=ctypes.cast(rgpi,ctypes.POINTER(RM_PROCESS_INFO))
    dwError=rstrtmgr.RmGetList(
        dwSession,
        ctypes.byref(nProcInfoNeeded),
        ctypes.byref(nProcInfo),
        pRgpi,
        ctypes.byref(dwReason))
    if dwError==5:
        # ACCESS_DENIED - sometimes trying again helps
        dwError=rstrtmgr.RmGetList(
            dwSession,
            ctypes.byref(nProcInfoNeeded),
            ctypes.byref(nProcInfo),
            pRgpi,
            ctypes.byref(dwReason))
    # See also:
    # https://docs.microsoft.com/en-us/windows/win32/debug/system-error-codes--0-499-
    if dwError!=0:
        raise Exception('[Windows error 0x%02X] %s'%(
            dwError,win32api.FormatMessage(dwError)))
    #print(f'RmGetList returned {nProcInfo.value} infos ({nProcInfoNeeded} needed)') # noqa: E501 # pylint: disable=line-too-long
    for i in range(nProcInfo.value):
        pi=ProcessInfo(
            rgpi[i].strAppName,
            rgpi[i].Process.dwProcessId,
            rgpi[i].ApplicationType)
        pi.processStartTime=rgpi[i].Process.ProcessStartTime
        yield pi
    rstrtmgr.RmEndSession(dwSession)
    if recursive and os.path.isdir(filename):
        for f in os.listdir(filename):
            yield from processLockingFile(
                os.sep.join((filename,f)),recursive,ignore,True)
            yield from processLockingFile(
                os.sep.join((filename,f)),
                recursive,
                ignore,
                True)

def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    didSomething=False
    printhelp=False
    recursive=False
    for arg in args:
        if arg.startswith('-'):
            av=arg.split('=',1)
            av[0]=av[0].lower()
            if av[0] in ('-h','--help'):
                printhelp=True
            else:
                printhelp=True
            if av[0] in ('-r',):
                recursive=True
        else:
            procs=list(processLockingFile(arg,recursive))
            print(f'{len(procs)} process(es) locking "{arg}"')
            print('------')
            for p in procs:
                print(p)
            didSomething=True
    if printhelp or not didSomething:
        print('USEAGE:')
        print('  whoLockedFile [options] [filename]')
        print('OPTIONS:')
        print('  -r ............................. recursive (keep going till you find one)') # noqa: E501 # pylint: disable=line-too-long
        print('  -h ............................. this help')
        return 1
    return 0


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
