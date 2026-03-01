"""
List named pipes in windows
"""
import typing
import typing
import time
import subprocess
import win32pipe # type: ignore
import win32file # type: ignore
#import pywintypes # type: ignore


def listPipes()->typing.Iterable[str]:
    """
    Generate a list of all windows named pipes
    """
    cmd=['powershell','-c','get-childitem',r'\\.\pipe\\']
    po=subprocess.Popen(cmd,stdout=subprocess.PIPE)
    out:typing.Union[bytes,str]
    out,_=po.communicate()
    if not isinstance(out,str):
        out=out.decode('utf-8',errors='ignore')
    return [x.rstrip() for x in out.split('\n')]


def pipe_server():
    """
    Start a pipe server
    """
    print("pipe server")
    count=0
    pipe=win32pipe.CreateNamedPipe(
        r'\\.\pipe\Foo',
        win32pipe.PIPE_ACCESS_DUPLEX,
        win32pipe.PIPE_TYPE_MESSAGE|
        win32pipe.PIPE_READMODE_MESSAGE|
        win32pipe.PIPE_WAIT,
        1,65536,65536,
        0,
        None)
    try:
        print("waiting for client")
        win32pipe.ConnectNamedPipe(pipe,None)
        print("got client")
        while count<10:
            print(f"writing message {count}")
            # convert to bytes
            some_data=str.encode(f"{count}")
            win32file.WriteFile(pipe,some_data)
            time.sleep(1)
            count+=1
        print("finished now")
    finally:
        win32file.CloseHandle(pipe)


def pipe_client(name:str):
    """
    Start a pipe client
    """
    print("pipe client")
    quitLoop=False
    while not quitLoop:
        try:
            handle=win32file.CreateFile(
                f'\\\\.\\pipe\\{name}',
                win32file.GENERIC_READ|win32file.GENERIC_WRITE,
                0,
                None,
                win32file.OPEN_EXISTING,
                0,
                None
            )
            res=win32pipe.SetNamedPipeHandleState(
                handle,win32pipe.PIPE_READMODE_MESSAGE,None,None)
            if res==0:
                print(f"SetNamedPipeHandleState return code: {res}")
            while True:
                resp = win32file.ReadFile(handle,64*1024)
                print(f"message: {resp}")
        except Exception as e:
            if e.args[0]==2:
                print("no pipe, trying again in a sec")
                time.sleep(1)
            elif e.args[0]==109:
                print("broken pipe, bye bye")
                quitLoop=True


if __name__=='__main__':
    #import sys
    for line in listPipes():
        print(line)
