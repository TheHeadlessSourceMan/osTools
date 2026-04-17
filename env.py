"""
More user-friendly way of dealing with environment variables

This can be assigned from external sources, translated to/from json,
and return values in a desired variable type.
"""
import typing
import os
from pathlib import Path


EnvVariableValue=typing.Any
EnvVariablesCompatible=typing.Union[None,str,typing.List[str],typing.Dict[str,EnvVariableValue]]


def setSystemEnv(name:str,value:typing.Any,listSplitter:str='')->None:
    """
    set a system-wide environment variable

    TODO: this could be dangerous and needs a better shell-escape solution!
    """
    import subprocess
    if not isinstance(value,str):
        if isinstance(value,(list,tuple)):
            value=listSplitter.join([str(v) for v in value])
        else:
            value=str(value)
    value=value.replace('\\','\\\\').replace('"','\\"')
    if value.find(' ')>=0 or value.find('\n')>=0:
        value=f'"{value}"'
    if os=='nt':
        cmd=['setx',name,value]
    else:
        cmd=['export',f'{name}={value}']
    po=subprocess.Popen(cmd,shell=True,stderr=subprocess.PIPE)
    _,err=po.communicate()
    err=err.strip()
    if err:
        raise Exception(err.decode('utf-8',errors='ignore'))


ENV_VARIABLES_SCOPE=typing.Literal[
    'isolated', # value is isolated to just a single object
    'application', # value is applied to the entire application via os.environ
    'system'] # value is exported to the operating system


class EnvVariables:
    """
    More user-friendly way of dealing with environment variables

    This can be assigned from external sources, translated to/from json,
    and return values in a desired variable type.
    """

    def __init__(self,
        environ:EnvVariablesCompatible=None,
        listSplitter:str='',
        scope:ENV_VARIABLES_SCOPE='isolated'):
        """ """
        self.scope:ENV_VARIABLES_SCOPE=scope
        self._origin:ENV_VARIABLES_SCOPE='application'
        if not listSplitter:
            if os.name=='nt':
                listSplitter=';'
            else:
                listSplitter=':'
        self._environ:typing.Dict[str,typing.Union[str,typing.List[str]]]={}
        self.listSplitter=listSplitter
        self.extend(environ)

    @property
    def jsonString(self)->str:
        """
        get as a json-compatible string
        """
        import json
        return json.dumps(self.jsonObj)
    @jsonString.setter
    def jsonString(self,jsonString:str):
        import json
        self.jsonObj=json.loads(jsonString)

    @property
    def jsonObj(self)->typing.Dict[str,typing.Any]:
        """
        get as a json compatible object
        """
        ret={}
        for k,v in self._environ.items():
            if not isinstance(v,str):
                if v is None:
                    v=''
                elif isinstance(v,list):
                    v=[str(vv) for vv in v]
                else:
                    v=str(v)
            ret[k]=v
        return ret
    @jsonObj.setter
    def jsonObj(self,jsonObj:typing.Dict[str,typing.Any]):
        self.assign(jsonObj)

    def clear(self,
        scope:typing.Optional[ENV_VARIABLES_SCOPE]=None):
        """
        Clear out the current value assignments
        """
        if scope is None:
            scope=self.scope
        if scope=='system':
            raise NotImplementedError('We never, ever, ever clear the system environment!')
        self._environ={}
        if scope=='application':
            os.environ.clear()

    def assign(self,
            environ:EnvVariablesCompatible,
            scope:typing.Optional[ENV_VARIABLES_SCOPE]=None):
        """
        Assign this to a specific set of environment variables
        """
        if scope is None:
            scope=self.scope
        if scope!='system':
            # never, ever clear the system environment!
            self.clear(scope)
        self.extend(environ,scope)

    def append(self,k:str,v:typing.Union[str,typing.List[str]],
            scope:typing.Optional[ENV_VARIABLES_SCOPE]=None):
        """
        Append to an existing environment variable

        1) will create if it does not exist
        2) if there is only one value it will be a string
        3) if there are more than one value, it will be a list
        """
        if scope is None:
            scope=self.scope
        if isinstance(v,str):
            if not v:
                return
            v=[v]
        elif not v:
            return
        current=self._environ.get(k,None)
        if current is None:
            if len(v)==1:
                current=v[0]
            else:
                current=[str(vv) for vv in v]
            self._environ[k]=current
        elif not isinstance(current,str):
            current.extend(v)
        else:
            current=[current]
            current.extend(v)
            self._environ[k]=current
        # save to application and possibly system scope
        if scope!='isolated':
            if isinstance(current,list):
                current=self.listSplitter.join(current)
            os.environ[k]=current
            if scope=='system':
                setSystemEnv(k,current,self.listSplitter)

    def extend(self,
            environ:EnvVariablesCompatible,
            scope:typing.Optional[ENV_VARIABLES_SCOPE]=None):
        """
        Extend these values with another set of values
        """
        if not environ:
            return
        env:typing.Dict[str,typing.Union[str,list[str]]]={}
        if isinstance(environ,str):
            environ=environ.split('\n')
        if isinstance(environ,list):
            for item in environ:
                kv=str(item).split('=',1)
                if len(kv)>1:
                    v=kv[-1].split(self.listSplitter)
                    if len(v)==1:
                        v=v[0]
                    else:
                        raise NotImplementedError('may be multiline??')
                    env[kv[0]]=v
        else:
            for k,v in environ.items():
                if isinstance(v,(list,tuple)):
                    v=[str(vv) for vv in v]
                else:
                    v=str(v)
                env[k]=v
        if scope is None:
            scope=self.scope
        for k,v in env.items():
            self.append(k,v)
    union=extend
    add=extend

    def keys(self):
        """
        act like a dict
        """
        return self._environ.keys()
    def values(self):
        """
        act like a dict
        """
        for v in self._environ.values():
            if isinstance(v,list):
                v=self.listSplitter.join(v)
            yield v
    def items(self):
        """
        act like a dict
        """
        for k,v in self._environ.items():
            if isinstance(v,list):
                v=self.listSplitter.join(v)
            yield k,v
    def __iter__(self):
        return self.items()

    def __len__(self):
        return len(self._environ)

    @typing.overload
    def getString(self,name:str,default:str='')->str:
        ...
    @typing.overload
    def getString(self,name:str,default:typing.Any)->typing.Any:
        ...
    def getString(self,name:str,default:typing.Any='')->typing.Any:
        """
        always returns a string
        """
        val=self._environ.get(name,default)
        return val
    get=getString
    getStr=getString
    def __getitem__(self,idx:str):
        ret=self.getString(idx,None)
        if ret is None:
            raise IndexError(f'Item "{idx}" not in list')

    def set(self,
        name:str,
        value:typing.Any,
        scope:typing.Optional[ENV_VARIABLES_SCOPE]=None):
        """
        Eiter set one value or a list of values.
        """
        if isinstance(value,(list,tuple)):
            self.setStringList(name,value,scope)
        else:
            self.setString(name,value,scope)
    __setitem__=set

    def setString(self,
        name:str,
        value:typing.Any,
        scope:typing.Optional[ENV_VARIABLES_SCOPE]=None):
        """
        Set a string value
        """
        if isinstance(value,(list,tuple)):
            value=self.listSplitter.join([str(v) for v in value])
        else:
            value=str(value)
        self._environ[name]=value
        # save to application and possibly system scope
        if scope!='isolated':
            os.environ[name]=value
            if scope=='system':
                setSystemEnv(name,value,self.listSplitter)

    @typing.overload
    def getFloat(self,name:str,default:float=0.0)->float:
        ...
    @typing.overload
    def getFloat(self,name:str,default:typing.Any)->typing.Any:
        ...
    def getFloat(self,name:str,default:typing.Any=0.0)->typing.Any:
        """
        always returns a float
        """
        val=self.getString(name,default)
        try:
            val=float(val)
        except Exception:
            return default
        return val
    def setFloat(self,
        name:str,
        value:typing.Any,
        scope:typing.Optional[ENV_VARIABLES_SCOPE]=None):
        """
        Set a float value
        """
        self.setString(name,float(value),scope)

    @typing.overload
    def getInt(self,name:str,default:int=0)->int:
        ...
    @typing.overload
    def getInt(self,name:str,default:typing.Any)->typing.Any:
        ...
    def getInt(self,name:str,default:typing.Any=0)->typing.Any:
        """
        always returns an int
        """
        val=self.getString(name,default)
        try:
            val=int(val)
        except Exception:
            return default
        return val
    def setInt(self,
        name:str,
        value:typing.Any,
        scope:typing.Optional[ENV_VARIABLES_SCOPE]=None):
        """
        Set an int value
        """
        self.setString(name,int(value),scope)

    def getStringList(self,name:str)->typing.Iterable[str]:
        """
        get env variable as a list of strings
        """
        ret=self._environ.get(name,[])
        if isinstance(ret,str):
            return [ret]
        return ret
    getStrList=getStringList
    getList=getStringList
    def setStringList(self,
            name:str,
            values:typing.Iterable[typing.Any],
            scope:typing.Optional[ENV_VARIABLES_SCOPE]=None):
        """
        get env variable as a list of strings
        """
        if isinstance(values,str):
            values=[values]
        else:
            values=[str(v) for v in values]
        self._environ[name]=values
        # save to application and possibly system scope
        if scope!='isolated':
            values=self.listSplitter.join(values)
            os.environ[name]=values
            if scope=='system':
                setSystemEnv(name,values,self.listSplitter)

    def getFilenameList(self,name:str)->typing.Iterable[Path]:
        """
        get env variable as a list of files
        """
        for fn in self.getStringList(name):
            yield Path(fn)
    setFilenameList=setStringList


# a drop-in replacement for os.environ
environ=EnvVariables(scope='application')
# global aliases
EnvironmentVariables=environ
environmentVariables=environ
env=environ
