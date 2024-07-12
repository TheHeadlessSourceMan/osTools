"""
expands upon sys.environ to make it an object
"""
import subprocess
import typing
from collections.abc import Iterable
import os

class _EnvironmentVariables:
    """
    expands upon sys.env to make it an object
    """

    def __init__(self):
        if os.name=='nt':
            self.delimiter=';'
        else:
            self.delimiter=':'

    def __call__(self)->"_EnvironmentVariables":
        """
        In case some fool tries to construct EnvironmentVariables variable
        """
        return self

    def __getitem__(self,k:str,default:typing.Any=None
        )->typing.Any:
        """
        Access like a dict
        """
        return self.get(k,default)

    def __setitem__(self,k:str,v:typing.Any)->None:
        """
        Access like a dict
        """
        return self.set(k,v)

    def items(self)->typing.Iterable[typing.Tuple[str,typing.Any]]:
        """
        Access like a dict
        """
        return [(k,self.get(k)) for k in self.keys()]

    def keys(self)->typing.Iterable[str]:
        """
        Access like a dict
        """
        return os.environ.keys()

    def values(self)->typing.Iterable[typing.Any]:
        """
        Access like a dict
        """
        return [self.get(k) for k in self.keys()]

    def getStr(self,k:str,default:typing.Any=None)->str:
        """
        Get the specified item as a string
        """
        if not isinstance(k,str):
            k=str(k)
        if k not in os.environ:
            return default # type: ignore
        return os.environ[k]

    def getStrList(self,k:str,default:typing.Any=None)->typing.List[str]:
        """
        Get the specified item as a list of strings
        """
        s=self.getStr(k,default)
        if isinstance(s,str):
            return s.split(self.delimiter)
        return s

    def _inferredCast(self,v:str)->typing.Any:
        """
        Utility to perform the best cast that a string allows
        """
        ret:typing.Any=v
        if v is None:
            return v
        try:
            ret=int(v)
            return ret
        except ValueError:
            pass
        try:
            ret=float(v)
            return ret
        except ValueError:
            pass
        lv=v.lower()
        if lv in ('y','yes','t','true'):
            return True
        if lv in ('n','no','f','false'):
            return False
        return v

    def getList(self,k:str,default:typing.Any=None)->typing.List[typing.Any]:
        """
        Get the specified item as a list of mixed-type items
        """
        return [self._inferredCast(v) for v in self.getStrList(k,default)]

    def get(self,k:str,default:typing.Any=None)->typing.Any:
        """
        Get the specified item as a mixed-type item
        or a list of mixed-type items
        """
        v=self.getList(k,default)
        if v is not None and len(v)==1:
            return v[0]
        return None

    def set(self,k:str,v:typing.Any,
        append:typing.Optional[bool]=None,
        permanent:bool=False,
        allusers:bool=False):
        """
        set an item

        :append: if value already exists, then append to it with the
            os separator, otherwise will overwrite the old value
            (if unspecified, will try to guess based upon whether
            existing value is a list)
        :permanent: make changes to os env, not just for this session
        :allusers: if makeing changes to os env, apply to all users
            (False=just current user)
        """
        if not isinstance(k,str):
            k=str(k)
        if not isinstance(v,str):
            if isinstance(v,Iterable):
                v=self.delimiter.join([str(vv) for vv in v])
            else:
                v=str(v)
        # from here on out v is always a string
        # if append is not specified, guess based upon whether it is a list
        if append is None:
            append=self.getStr(k,'').find(self.delimiter)>=0
        # append to existing if necessary
        if append:
            current=self.get(k)
            allvalues:typing.List[str]=[]
            if current is None:
                pass
            elif isinstance(current,str):
                allvalues=[current]
            elif isinstance(current,Iterable):
                allvalues=[str(vv) for vv in current]
            else:
                allvalues=[str(current)]
            allvalues.append(v)
            v=self.delimiter.join(allvalues)
        # make changes permanent if requested
        if permanent:
            if os.name=='nt':
                cmd=['setx'] # run "setx /?" from command line for more info
                if allusers:
                    cmd.append('/M')
                cmd.append('"%s"'%k)
                cmd.append('"%s"'%v)
                # TODO: must be elevated to work?
                po=subprocess.Popen(cmd,
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                _,errb=po.communicate()
                err=errb.decode('utf-8',errors='ignore').strip()
                if err:
                    raise Exception(err)
            else:
                raise NotImplementedError()
        # set the global environment value for the running app
        os.environ[k]=v

    # no need to be this specific, but for parity with get() functions...
    setList=set
    setStr=set
    setStrList=set

# global and its aliases
EnvironmentVariables=_EnvironmentVariables()
environmentVariables=EnvironmentVariables
env=EnvironmentVariables
