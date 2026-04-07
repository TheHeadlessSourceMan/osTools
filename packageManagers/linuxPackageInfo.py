"""
Juggle installed packages in a universal sort of way
"""
import typing
import subprocess


def getPackageManagers()->typing.Iterable[str]:
    """
    Get all available package managers
    """
    for pm in ('rpm','dpkg'):
        po=subprocess.Popen(['which',pm],
            shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        out,err=po.communicate()
        out=out.strip()
        err=err.strip()
        if not err and po.returncode==0 and out:
            yield pm


def isPackageInstalled(name:str)->bool:
    """
    determine if a package is installed

    Will check all available package managers
    """
    for pm in getPackageManagers():
        cmd=[pm]
        if pm=='rpm':
            cmd.append('-q')
        else:
            cmd.append('-s')
        cmd.append(name)
        po=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        out,err=po.communicate()
        out=out.strip()
        err=err.strip()
        if not err and po.returncode==0:
            return True
    return False
