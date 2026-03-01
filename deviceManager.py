"""
Class that does all the things
Windows Device Manager does
"""
import typing
import subprocess


class DeviceClass:
    """
    Windows device class
    """
    def __init__(self,deviceManager:"DeviceManager",deviceClassText:str):
        self.deviceManager=deviceManager
        self.classGUID:str=''
        self.className:str=''
        self.classDescription:str=''
        for line in deviceClassText.split('\n'):
            kv=line.split(':',1)
            k=kv[0]
            v=kv[1].strip()
            k=k[0].lower()+k[1:].replace(' ','')
            setattr(self,k,v)

    @property
    def guid(self)->str:
        """
        guid for the class
        """
        return self.classGUID
    @property
    def name(self)->str:
        """
        name of the class
        """
        return self.className
    @property
    def description(self)->str:
        """
        description for the class
        """
        return self.classDescription

    def __repr__(self):
        ret=[]
        for k,v in self.__dict__.items():
            ret.append(f'{k}={v}')
        return '\n'.join(ret)


class Driver:
    """
    Windows driver
    """
    def __init__(self,deviceManager:"DeviceManager",driverText:str):
        self.deviceManager=deviceManager
        self.publishedName:str=''
        self.originalName:str=''
        self.providerName:str=''
        self.className:str=''
        self.classGUID:str=''
        self.driverVersion:str=''
        self.signerName:str=''

        for line in driverText.split('\n'):
            kv=line.split(':',1)
            k=kv[0]
            v=kv[1].strip()
            k=k[0].lower()+k[1:].replace(' ','')
            setattr(self,k,v)

    @property
    def deviceClass(self)->typing.Optional[DeviceClass]:
        """
        Device class for this device
        """
        for c in self.deviceManager.findDeviceClasses(self.classGUID):
            return c
        return None

    def deleteDriver(self):
        """
        Delete this driver from the system
        """
        cmd=['pnputil','/delete-driver',self.publishedName]
        po=subprocess.Popen(cmd,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        out,_=po.communicate()
        out=out.decode("utf-8",errors="ignore")
        print(out)
    removeDriver=deleteDriver
    uninstallDriver=deleteDriver
    uninstall=deleteDriver

    def __repr__(self):
        ret=[
            f'{self.publishedName=}',
            f'{self.originalName=}',
            f'{self.providerName=}',
            f'{self.className=}',
            f'{self.classGUID=}',
            f'{self.driverVersion=}',
            f'{self.signerName=}']
        return '\n'.join(ret)


class Device:
    """
    Windows device
    """
    def __init__(self,deviceManager:"DeviceManager",deviceText:str):
        self.deviceManager=deviceManager
        self.instanceID:str=''
        self.deviceDescription:str=''
        self.className:str=''
        self.classGUID:str=''
        self.manufacturerName:str=''
        self.status:str=''
        self.driverName:str=''
        k=''
        for line in deviceText.split('\n'):
            kv=line.split(':',1)
            if len(kv)<2:
                lastV=getattr(self,k,[])
                if not isinstance(lastV,list):
                    lastV=[lastV]
                    setattr(self,k,lastV)
                v=kv[0].strip()
                lastV.append(v)
            else:
                k=kv[0]
                v=kv[1].strip()
                k=k[0].lower()+k[1:].replace(' ','')
                setattr(self,k,v)

    @property
    def running(self)->bool:
        """
        Is the device running?
        """
        return self.status=='Started'

    def restart(self)->None:
        """
        Restart this device
        """
        cmd=['pnputil','/restart-device',self.instanceID]
        po=subprocess.Popen(cmd,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        out,_=po.communicate()
        outS=out.decode("utf-8",errors="ignore")
        print(outS)
    reset=restart

    def enable(self)->None:
        """
        Enable this device
        """
        cmd=['pnputil','/enable-device',self.instanceID]
        po=subprocess.Popen(cmd,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        out,_=po.communicate()
        outS=out.decode("utf-8",errors="ignore")
        print(outS)
    start=enable

    def disable(self)->None:
        """
        Disable this device
        """
        cmd=['pnputil','/disable-device',self.instanceID]
        po=subprocess.Popen(cmd,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        out,_=po.communicate()
        outS=out.decode("utf-8",errors="ignore")
        print(outS)
    stop=disable

    def eject(self):
        """
        Safely remove a device

        TODO: this is surprisingly involved.  See:
        https://stackoverflow.com/questions/85649/safely-remove-a-usb-drive-using-the-win32-api
        """
        raise NotImplementedError()

    @property
    def name(self)->str:
        """
        name of the device
        """
        return self.deviceDescription

    @property
    def driver(self)->typing.Optional[Driver]:
        """
        Driver for this device
        """
        for d in self.deviceManager.findDrivers(
            deviceDriverFilename=self.driverName):
            return d
        return None

    @property
    def deviceClass(self)->typing.Optional[DeviceClass]:
        """
        Class of the device
        """
        for d in self.deviceManager.findDeviceClasses(
            self.classGUID):
            return d
        return None

    def __repr__(self):
        ret=[]
        for k,v in self.__dict__.items():
            if k not in ('deviceManager',):
                ret.append(f'{k}={v}')
        return '\n'.join(ret)


class DeviceManager:
    """
    Class that does all the things
    Windows Device Manager does
    """

    def __init__(self)->None:
        """ """
        self._drivers:typing.List[Driver]=[]
        self._classes:typing.List[DeviceClass]=[]
        self._devices:typing.List[Device]=[]
        self.refresh()

    def getDriver(self,
        driverName:str,
        default:typing.Optional[Driver]=None
        )->typing.Optional[Driver]:
        """
        Get a driver with a given id
        """
        for driver in self._drivers:
            if driver.originalName==driverName:
                return driver
        return default

    def installDriver(self,driverName:str):
        """
        Install a new driver
        """
        infFile=driverName
        if not infFile.endswith('.inf'):
            infFile=infFile+'.inf'
        if not os.path.exists(infFile):
            # TODO: be smarter about finding
        cmd=[
            'pnputil',
            '/add-driver',
            infFile,
            '/subdirs',
            '/install'
        po=subprocess.Popen(cmd,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        out,_=po.communicate()
        outS=out.decode("utf-8",errors="ignore")
        print(outS)

    def uninstallDriver(self,driverName:str):
        """
        uninstall a driver
        """
        driver=self.getDriver(driverName)
        if driver is not None:
            driver.deleteDriver()
    deleteDriver=uninstallDriver
    removeDriver=uninstallDriver

    def getDevice(self,
        deviceID:str,
        default:typing.Optional[Device]=None
        )->typing.Optional[Device]:
        """
        Get a driver with a given id
        """
        for device in self._devices:
            if device.name==deviceID:
                return device
        return default

    def ejectDevice(self,
        deviceID:str):
        """
        eject a device
        """
        device=self.getDevice(deviceID)
        if device is None:
            raise Exception('No device named "{deviceID}"')
        device.eject()

    def resetDevice(self,
        deviceID:str):
        """
        reset a device
        """
        device=self.getDevice(deviceID)
        if device is None:
            raise Exception('No device named "{deviceID}"')
        device.reset()
    restartDevice=resetDevice

    def stopDevice(self,
        deviceID:str):
        """
        stop a device
        """
        device=self.getDevice(deviceID)
        if device is None:
            raise Exception('No device named "{deviceID}"')
        device.stop()
    disableDevice=stopDevice

    def startDevice(self,
        deviceID:str):
        """
        stop a device
        """
        device=self.getDevice(deviceID)
        if device is None:
            raise Exception('No device named "{deviceID}"')
        device.start()
    enableDevice=startDevice

    def findDeviceClasses(self,
        deviceClassNameOrGUID:typing.Optional[str]=None
        )->typing.Generator[DeviceClass,None,None]:
        """
        Get a device class for a guid/name
        """
        if deviceClassNameOrGUID is None:
            yield from iter(self._classes)
            return
        m=deviceClassNameOrGUID.lower().replace(' ','')
        for c in self._classes:
            if c.guid==deviceClassNameOrGUID:
                yield c
            if c.name.lower().replace(' ','').find(m)>=0:
                yield c
            if c.description.lower().replace(' ','').find(m)>=0:
                yield c
        return None

    def findDevices(self,
        deviceName:typing.Optional[str]=None,
        running:typing.Optional[bool]=None,
        bus:typing.Optional[str]=None,
        driverProviderName:typing.Optional[str]=None,
        deviceClassNameOrGUID:typing.Optional[str]=None,
        deviceDriverFilename:typing.Optional[str]=None
        )->typing.Generator[Device,None,None]:
        """
        Find devices that match a given pattern
        """
        if bus is not None:
            bus=bus.upper()+'\\'
        if deviceName is not None:
            deviceName=deviceName.replace(' ','').lower()
        driverNames:typing.List[str]=[]
        if driverProviderName is not None \
            or deviceClassNameOrGUID is not None \
            or deviceDriverFilename is not None:
            driverNames=[d.publishedName for d in self.findDrivers(
                driverProviderName,
                deviceClassNameOrGUID,
                deviceDriverFilename)]
        for device in self._devices:
            if driverNames:
                if device.driverName not in driverNames:
                    continue
            if deviceName is not None:
                if device.manufacturerName\
                    .replace(' ','').lower().find(deviceName)<0 \
                    and device.className\
                    .replace(' ','').lower().find(deviceName)<0: # noqa: E129
                    continue
            if running is not None:
                if device.running!=running:
                    continue
            if bus is not None:
                if not device.instanceID.startswith(bus):
                    continue
            yield device

    def findDrivers(self,
        driverProviderName:typing.Optional[str]=None,
        deviceClassNameOrGUID:typing.Optional[str]=None,
        deviceDriverFilename:typing.Optional[str]=None
        )->typing.Generator[Driver,None,None]:
        """
        Find devices that match a given pattern
        """
        if driverProviderName is not None:
            driverProviderName=driverProviderName.replace(' ','').lower()
        classGuids:typing.Optional[typing.List[str]]=None
        if deviceClassNameOrGUID is not None:
            classGuids=[c.guid for c in \
                self.findDeviceClasses(deviceClassNameOrGUID)]
        for driver in self._drivers:
            if classGuids is not None:
                if driver.classGUID not in classGuids:
                    continue
            if deviceDriverFilename is not None:
                if driver.publishedName!=deviceDriverFilename \
                    and driver.originalName!=deviceDriverFilename:
                    continue
            if driver.providerName is not None:
                if driver.providerName.replace(' ','').lower()\
                    !=driverProviderName:
                    continue
            yield driver

    def refresh(self,systemRescan:bool=False):
        """
        refresh driver list

        :systemRescan: cause the system to scan
            for hardware changes
            same thing as clicking refresh button in device manager
        """
        if systemRescan:
            cmd=['pnputil','/scan-devices']
            po=subprocess.Popen(cmd,
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            out,_=po.communicate()
            outS=out.decode("utf-8",errors="ignore")
            print(outS)
        self._classes=[]
        cmd=['pnputil','/enum-classes']
        po=subprocess.Popen(cmd,stdout=subprocess.PIPE)
        out,_=po.communicate()
        outS=out.decode("utf-8",errors="ignore")\
            .replace('\r','')\
            .replace('\n ','\n')\
            .strip()
        for deviceClassText in outS.split('\n\n')[1:]:
            self._classes.append(DeviceClass(self,deviceClassText))
        self._drivers=[]
        cmd=['pnputil','/enum-drivers']
        po=subprocess.Popen(cmd,stdout=subprocess.PIPE)
        out,_=po.communicate()
        outS=out.decode("utf-8",errors="ignore")\
            .replace('\r','')\
            .replace('\n ','\n')\
            .strip()
        for driverText in outS.split('\n\n')[1:]:
            self._drivers.append(Driver(self,driverText))
        self._drivers=[]
        cmd=['pnputil','/enum-devices']
        po=subprocess.Popen(cmd,stdout=subprocess.PIPE)
        out,_=po.communicate()
        outS=out.decode("utf-8",errors="ignore")\
            .replace('\r','')\
            .replace('\n ','\n')\
            .strip()
        for deviceText in outS.split('\n\n')[1:]:
            self._devices.append(Device(self,deviceText))

    def __repr__(self):
        return '\n\n'.join([repr(d) for d in self._drivers])


def cmdline(args:typing.Iterable[str])->int:
    """
    Run the command line

    :param args: command line arguments (WITHOUT the filename)
    """
    didSomething=False
    printHelp=False
    inLsMode=False
    showStoppedDevices=False
    whatToList='devices'
    dMan=DeviceManager()
    def doLs(searchStr:typing.Optional[str]=None):
        """
        Perform an --ls
        """
        results:typing.Iterable[typing.Any]=[]
        if whatToList.find('class')>=0:
            results=list(dMan.findDeviceClasses(searchStr))
        elif whatToList.startswith('device'):
            running=None
            if not showStoppedDevices:
                running=True
            results=dMan.findDevices(searchStr,running)
        elif whatToList.startswith('driver'):
            results=dMan.findDrivers(searchStr)
        for result in results:
            print(result)
    for arg in args:
        if arg.startswith('-'):
            av=arg.split('=',1)
            av[0]=av[0].lower()
            if av[0] in ('-h','--help'):
                printHelp=True
            elif av[0].startswith('--showstopped'):
                showStoppedDevices=True
            elif av[0]=='--ls':
                inLsMode=True
                didSomething=True
                if len(av)>1:
                    whatToList=av[1].lower()
                else:
                    whatToList='devices'
            elif av[0]=='--reset':
                if inLsMode:
                    doLs()
                    inLsMode=False
                else:
                    didSomething=True
                if len(av)<2:
                    print('Missing deviceID for --reset')
                else:
                    deviceID=av[1]
                    dMan.resetDevice(deviceID)
            elif av[0] in ('--stop','--disable'):
                if inLsMode:
                    doLs()
                    inLsMode=False
                else:
                    didSomething=True
                if len(av)<2:
                    print('Missing deviceID for --stop')
                else:
                    deviceID=av[1]
                    dMan.stopDevice(deviceID)
            elif av[0] in ('--start','--enable'):
                if inLsMode:
                    doLs()
                    inLsMode=False
                else:
                    didSomething=True
                if len(av)<2:
                    print('Missing deviceID for --start')
                else:
                    deviceID=av[1]
                    dMan.startDevice(deviceID)
            elif av[0]=='--eject':
                if inLsMode:
                    doLs()
                    inLsMode=False
                else:
                    didSomething=True
                if len(av)<2:
                    print('Missing deviceID for --eject')
                else:
                    deviceID=av[1]
                    dMan.ejectDevice(deviceID)
            elif av[0]=='--uninstall':
                if inLsMode:
                    doLs()
                    inLsMode=False
                else:
                    didSomething=True
                if len(av)<2:
                    print('Missing driver for --uninstall')
                else:
                    driver=av[1]
                    dMan.uninstallDriver(driver)
            elif av[0]=='--install':
                if inLsMode:
                    doLs()
                    inLsMode=False
                else:
                    didSomething=True
                if len(av)<2:
                    print('Missing driver for --install')
                else:
                    driver=av[1]
                    dMan.installDriver(driver)
            else:
                print(f'Unknown parameter "{arg}"')
                printHelp=True
        else:
            if inLsMode:
                doLs(arg)
            else:
                print(f'Unknown parameter "{arg}"')
                printHelp=True
    if inLsMode:
        doLs()
    if printHelp or not didSomething:
        print('USAGE:')
        print('  deviceManager [options] [filename]')
        print('OPTIONS:')
        print('  --ls[=devices] [match] .......... list devices,classes,or drivers') # noqa: E501 # pylint: disable=line-too-long
        print('  --showStopped[Devices] .......... also list devices that are stopped') # noqa: E501 # pylint: disable=line-too-long
        print('  --reset=deviceID ................ reset a device')
        print('  --restart=deviceID .............. reset a device')
        print('  --stop=deviceID ................. stop a device')
        print('  --disable=deviceID .............. stop a device')
        print('  --start=deviceID ................ start a device')
        print('  --enable=deviceID ............... start a device')
        print('  --eject=deviceID ................ eject a device')
        print('  --uninstall=driver .............. uninstall a driver')
        print('  --install=driver ................ install a driver')
        print('  -h .............................. this help')
        return 1
    return 0


if __name__=='__main__':
    import sys
    cmdline(sys.argv[1:])
