"""
This is a stripped-down verson of pyvda library.
If you run into any problems, try using that instead.

References:
    * GUIDs, Interfaces: https://github.com/Ciantic/VirtualDesktopAccessor/blob/master/VirtualDesktopAccessor/Win10Desktops.h
    * Service provider: https://docs.microsoft.com/en-us/dotnet/api/system.iserviceprovider?view=netframework-4.8
    * Object array: https://docs.microsoft.com/en-us/windows/win32/api/objectarray/nn-objectarray-iobjectarray
    * HSTRING: https://docs.microsoft.com/en-us/uwp/cpp-ref-for-winrt/hstring
    * comtypes: http://svn.python.org/projects/ctypes/tags/comtypes-0.3.2/docs/com_interfaces.html
    * dev blogs:
        * http://grabacr.net/archives/5601
        * https://www.cyberforum.ru/blogs/105416/blog3671.html
"""
from typing import Any,Iterator
import sys
import ctypes
from ctypes import HRESULT, POINTER, c_ulonglong
from ctypes.wintypes import (
    BOOL,
    DWORD,
    HWND,
    INT,
    LPCWSTR,
    LPVOID,
    RECT,
    SIZE,
    UINT,
    ULONG,
    WCHAR
)

from comtypes import COMMETHOD, GUID, STDMETHOD, IUnknown

GUID_IVirtualDesktop_26100 = GUID("{3F07F4BE-B107-441A-AF0F-39D82529072C}")
GUID_IVirtualDesktopManagerInternal_26100 = GUID("{53F5CA0B-158F-4124-900C-057158060B27}")

CLSID_ImmersiveShell = GUID("{C2F03A33-21F5-47FA-B4BB-156362A2F239}")
CLSID_VirtualDesktopManagerInternal = GUID("{C5E0CDCA-7B6E-41B2-9FC4-D93975CC467B}")
CLSID_IVirtualDesktopManager = GUID("{AA509086-5CA9-4C25-8F95-589D3C07B48A}")
CLSID_VirtualDesktopPinnedApps = GUID("{B5A399E7-1C87-46B8-88E9-FC5747B171BD}")

# Ignore following APIs:
IAsyncCallback = UINT
IImmersiveMonitor = UINT
APPLICATION_VIEW_COMPATIBILITY_POLICY = UINT
IShellPositionerPriority = UINT
IApplicationViewOperation = UINT
APPLICATION_VIEW_CLOAK_TYPE = UINT
IApplicationViewPosition = UINT
IImmersiveApplication = UINT
IApplicationViewChangeListener = UINT

TrustLevel = INT
AdjacentDesktop = UINT

PWSTR = POINTER(WCHAR)
REFGUID = POINTER(GUID)
REFIID = POINTER(GUID)


# Computer\HKEY_LOCAL_MACHINE\SOFTWARE\Classes\Interface\{372E1D3B-38D3-42E4-A15B-8AB2B178F513}
# Found with searching "IApplicationView"
class IApplicationView(IUnknown):
    _iid_ = GUID("{372E1D3B-38D3-42E4-A15B-8AB2B178F513}")

class HSTRING(ctypes.c_void_p):
    def __init__(self, s=None):
        super().__init__()
        if s is None or len(s) == 0:
            self.value = None
            return
        u16str = s.encode("utf-16-le") + b"\x00\x00"
        u16len = (len(u16str) // 2) - 1
        WindowsCreateString(u16str, ctypes.c_uint32(u16len), ctypes.byref(self))
        self._finalizer = weakref.finalize(self, WindowsDeleteString, self.value)  # only register finalizer if we created the string

    def __str__(self):
        if self.value is None:
            return ""
        length = ctypes.c_uint32()
        ptr = WindowsGetStringRawBuffer(self, ctypes.byref(length))
        return ctypes.wstring_at(ptr, length.value)

    def __repr__(self):
        return "HSTRING(%s)" % repr(str(self))



class IObjectArray(IUnknown):
    _iid_ = GUID("{92CA9DCD-5622-4BBA-A805-5E9F541BD8C9}")
    _methods_ = [
        COMMETHOD([], HRESULT, "GetCount", (["out"], POINTER(UINT), "pcObjects"),),
        STDMETHOD(HRESULT, "GetAt", (UINT, REFIID, POINTER(LPVOID),)),
    ]

    def get_at(self, i: int, cls: Any) -> Any:
        item = POINTER(cls)()
        self.GetAt(i, cls._iid_, item) # type: ignore
        return item

    def iter(self, cls: Any) -> Iterator[Any]:
        for i in range(self.GetCount()): # type: ignore
            yield self.get_at(i, cls)

IApplicationView._methods_ = [
    # IInspectable methods
    STDMETHOD(HRESULT, "GetIids", (POINTER(ULONG), POINTER(POINTER(GUID)),)),
    STDMETHOD(HRESULT, "GetRuntimeClassName", (POINTER(HSTRING),)),
    STDMETHOD(HRESULT, "GetTrustLevel", (POINTER(TrustLevel),)),
    # IApplicationView methods
    STDMETHOD(HRESULT, "SetFocus", ()),
    STDMETHOD(HRESULT, "SwitchTo", ()),
    STDMETHOD(HRESULT, "TryInvokeBack", (POINTER(IAsyncCallback),)),
    COMMETHOD([], HRESULT, "GetThumbnailWindow", (["out"], POINTER(HWND), "hwnd")),
    STDMETHOD(HRESULT, "GetMonitor", (POINTER(POINTER(IImmersiveMonitor)),)),
    COMMETHOD([], HRESULT, "GetVisibility", (["out"], POINTER(UINT), "pVisible")),
    STDMETHOD(HRESULT, "SetCloak", (APPLICATION_VIEW_CLOAK_TYPE, UINT,)),
    STDMETHOD(HRESULT, "GetPosition", (REFIID, POINTER(LPVOID),)),
    STDMETHOD(HRESULT, "SetPosition", (POINTER(IApplicationViewPosition),)),
    STDMETHOD(HRESULT, "InsertAfterWindow", (HWND,)),
    STDMETHOD(HRESULT, "GetExtendedFramePosition", (POINTER(RECT),)),
    COMMETHOD([], HRESULT, "GetAppUserModelId", (["out"], POINTER(PWSTR), "pId")),
    STDMETHOD(HRESULT, "SetAppUserModelId", (LPCWSTR,)),
    STDMETHOD(HRESULT, "IsEqualByAppUserModelId", (LPCWSTR, POINTER(UINT),)),
    STDMETHOD(HRESULT, "GetViewState", (POINTER(UINT),)),
    STDMETHOD(HRESULT, "SetViewState", (UINT,)),
    STDMETHOD(HRESULT, "GetNeediness", (POINTER(UINT),)),
    COMMETHOD([], HRESULT, "GetLastActivationTimestamp", (["out"], POINTER(c_ulonglong), "pGuid")),
    STDMETHOD(HRESULT, "SetLastActivationTimestamp", (c_ulonglong,)),
    COMMETHOD([], HRESULT, "GetVirtualDesktopId", (["out"], POINTER(GUID), "pGuid")),
    STDMETHOD(HRESULT, "SetVirtualDesktopId", (REFGUID,)),
    COMMETHOD([], HRESULT, "GetShowInSwitchers", (["out"], POINTER(UINT), "pShown")),
    STDMETHOD(HRESULT, "SetShowInSwitchers", (UINT,)),
    STDMETHOD(HRESULT, "GetScaleFactor", (POINTER(UINT),)),
    STDMETHOD(HRESULT, "CanReceiveInput", (POINTER(BOOL),)),
    STDMETHOD(HRESULT, "GetCompatibilityPolicyType", (POINTER(APPLICATION_VIEW_COMPATIBILITY_POLICY),)),
    STDMETHOD(HRESULT, "SetCompatibilityPolicyType", (APPLICATION_VIEW_COMPATIBILITY_POLICY,)),
    # STDMETHOD(HRESULT, "GetPositionPriority", (POINTER(POINTER(IShellPositionerPriority)),)),
    # STDMETHOD(HRESULT, "SetPositionPriority", (POINTER(IShellPositionerPriority),)),
    STDMETHOD(HRESULT, "GetSizeConstraints", (POINTER(IImmersiveMonitor), POINTER(SIZE), POINTER(SIZE))),
    STDMETHOD(HRESULT, "GetSizeConstraintsForDpi", (UINT, POINTER(SIZE), POINTER(SIZE),)),
    STDMETHOD(HRESULT, "SetSizeConstraintsForDpi", (POINTER(UINT), POINTER(SIZE), POINTER(SIZE))),
    # STDMETHOD(HRESULT, "QuerySizeConstraintsFromApp", ()),
    STDMETHOD(HRESULT, "OnMinSizePreferencesUpdated", (HWND,)),
    STDMETHOD(HRESULT, "ApplyOperation", (POINTER(IApplicationViewOperation),)),
    STDMETHOD(HRESULT, "IsTray", (POINTER(BOOL),)),
    STDMETHOD(HRESULT, "IsInHighZOrderBand", (POINTER(BOOL),)),
    STDMETHOD(HRESULT, "IsSplashScreenPresented", (POINTER(BOOL),)),
    STDMETHOD(HRESULT, "Flash", ()),
    STDMETHOD(HRESULT, "GetRootSwitchableOwner", (POINTER(POINTER(IApplicationView)),)),
    STDMETHOD(HRESULT, "EnumerateOwnershipTree", (POINTER(POINTER(IObjectArray)),)),
    STDMETHOD(HRESULT, "GetEnterpriseId", (POINTER(PWSTR),)),
    STDMETHOD(HRESULT, "IsMirrored", (POINTER(BOOL),)),
    STDMETHOD(HRESULT, "GetFrameworkViewType", (POINTER(UINT),)),
    STDMETHOD(HRESULT, "GetCanTab", (POINTER(UINT),)),
    STDMETHOD(HRESULT, "SetCanTab", (UINT,)),
    STDMETHOD(HRESULT, "GetIsTabbed", (POINTER(UINT),)),
    STDMETHOD(HRESULT, "SetIsTabbed", (UINT,)),
    STDMETHOD(HRESULT, "RefreshCanTab", ()),
    STDMETHOD(HRESULT, "GetIsOccluded", (POINTER(UINT),)),
    STDMETHOD(HRESULT, "SetIsOccluded", (UINT,)),
    STDMETHOD(HRESULT, "UpdateEngagementFlags", (UINT, UINT,)),
    STDMETHOD(HRESULT, "SetForceActiveWindowAppearance", (UINT,)),
    STDMETHOD(HRESULT, "GetLastActivationFILETIME", (POINTER(SIZE),)),
    STDMETHOD(HRESULT, "GetPersistingStateName", (POINTER(PWSTR),)),
]


GUID_IVirtualDesktop = GUID_IVirtualDesktop_26100

# In registry: Computer\HKEY_LOCAL_MACHINE\SOFTWARE\Classes\Interface\{FF72FFDD-BE7E-43FC-9C03-AD81681E88E4}
class IVirtualDesktop(IUnknown):
    _iid_ = GUID_IVirtualDesktop
    _methods_ = [
        STDMETHOD(HRESULT, "IsViewVisible", (POINTER(IApplicationView), POINTER(UINT))),
        COMMETHOD([], HRESULT, "GetID", (["out"], POINTER(GUID), "pGuid"),),
        COMMETHOD([], HRESULT, "GetName", (["out"], POINTER(HSTRING), "pName"),),
        COMMETHOD([], HRESULT, "GetWallpaperPath", (["out"], POINTER(HSTRING), "pPath"),),
        COMMETHOD([], HRESULT, "IsRemote", (["out"], POINTER(HWND), "pW"), ),
    ]


GUID_IVirtualDesktop2 = GUID("{31EBDE3F-6EC3-4CBD-B9FB-0EF6D09B41F4}")
class IVirtualDesktop2(IUnknown):
    _iid_ = GUID_IVirtualDesktop2
    _methods_ = [
        STDMETHOD(HRESULT, "IsViewVisible", (POINTER(IApplicationView), POINTER(UINT))),
        COMMETHOD([], HRESULT, "GetID", (["out"], POINTER(GUID), "pGuid"),),
        COMMETHOD([], HRESULT, "GetName", (["out"], POINTER(HSTRING), "pName"),),
    ]


GUID_IVirtualDesktopManagerInternal = GUID_IVirtualDesktopManagerInternal_26100

# HKEY_LOCAL_MACHINE\SOFTWARE\Classes\Interface\{F31574D6-B682-4CDC-BD56-1827860ABEC6}
class IVirtualDesktopManagerInternal(IUnknown):
    _iid_ = GUID_IVirtualDesktopManagerInternal
    _methods_ = [
        COMMETHOD([], HRESULT, "GetCount",  (["out"], POINTER(UINT), "pCount"),),
        STDMETHOD(HRESULT, "MoveViewToDesktop", (POINTER(IApplicationView), POINTER(IVirtualDesktop))),
        STDMETHOD(HRESULT, "CanViewMoveDesktops", (POINTER(IApplicationView), POINTER(UINT))),
        COMMETHOD([], HRESULT, "GetCurrentDesktop", (["out"], POINTER(POINTER(IVirtualDesktop)), "pDesktop"),),
        COMMETHOD([], HRESULT, "GetDesktops", (["out"], POINTER(POINTER(IObjectArray)), "array")),
        STDMETHOD(HRESULT, "GetAdjacentDesktop", (POINTER(IVirtualDesktop), AdjacentDesktop, POINTER(POINTER(IVirtualDesktop)),)),
        STDMETHOD(HRESULT, "SwitchDesktop", (POINTER(IVirtualDesktop),)),
        STDMETHOD(HRESULT, "SwitchDesktopAndMoveForegroundView", (POINTER(IVirtualDesktop),)),
        COMMETHOD([], HRESULT, "CreateDesktopW", (["out"], POINTER(POINTER(IVirtualDesktop)), "pDesktop"),),
        STDMETHOD(HRESULT, "MoveDesktop", (POINTER(IVirtualDesktop), UINT)),
        COMMETHOD([], HRESULT, "RemoveDesktop", (["in"], POINTER(IVirtualDesktop), "destroyDesktop"), (["in"], POINTER(IVirtualDesktop), "fallbackDesktop")),
        COMMETHOD([], HRESULT, "FindDesktop", (["in"], POINTER(GUID), "pGuid"), (["out"], POINTER(POINTER(IVirtualDesktop)), "pDesktop")),
        STDMETHOD(HRESULT, "GetDesktopSwitchIncludeExcludeViews", (POINTER(IVirtualDesktop), POINTER(POINTER(IObjectArray)), POINTER(POINTER(IObjectArray)))),
        COMMETHOD([], HRESULT, "SetName", (["in"], POINTER(IVirtualDesktop), "pDesktop"), (["in"], HSTRING, "name")),
        COMMETHOD([], HRESULT, "SetWallpaper", (["in"], POINTER(IVirtualDesktop), "pDesktop"), (["in"], HSTRING, "path")),
        COMMETHOD([], HRESULT, "SetWallpaperForAllDesktops", (["in"], HSTRING, "path")),
        COMMETHOD([], HRESULT, "CopyDesktopState", (["in"], POINTER(IApplicationView), "pView0"), (["in"], POINTER(IApplicationView), "pView0")),
        COMMETHOD([], HRESULT, "CreateRemoteDesktop", (["in"], HSTRING, "a1"), (["out"], POINTER(POINTER(IVirtualDesktop)), "out")),
        STDMETHOD(HRESULT, "pDesktop", (POINTER(IVirtualDesktop),)),
        STDMETHOD(HRESULT, "SwitchRemoteDesktop", (POINTER(IVirtualDesktop), UINT)),
        STDMETHOD(HRESULT, "SwitchDesktopWithAnimation", (POINTER(IVirtualDesktop),)),
        COMMETHOD([], HRESULT, "GetLastActiveDesktop", (["out"], POINTER(POINTER(IVirtualDesktop)), "pDesktop"),),
        STDMETHOD(HRESULT, "WaitForAnimationToComplete"),
    ]
  
    def get_all_desktops(self) -> IObjectArray:
        return self.GetDesktops() # type: ignore

    def get_current_desktop(self) -> IVirtualDesktop:
        return self.GetCurrentDesktop() # type: ignore

    def create_desktop(self) -> IVirtualDesktop:
        return self.CreateDesktopW() # type: ignore

    def switch_desktop(self, target: IVirtualDesktop) -> IVirtualDesktop:
        return self.SwitchDesktop(target) # type: ignore


GUID_IVirtualDesktopManagerInternal2 = GUID("{0F3A72B0-4566-487E-9A33-4ED302F6D6CE}")
class IVirtualDesktopManagerInternal2(IUnknown):
    _iid_ = GUID_IVirtualDesktopManagerInternal2
    _methods_ = [
        COMMETHOD([], HRESULT, "GetCount", (["out"], POINTER(UINT), "pCount"),),
        STDMETHOD(HRESULT, "MoveViewToDesktop", (POINTER(IApplicationView), POINTER(IVirtualDesktop))),
        STDMETHOD(HRESULT, "CanViewMoveDesktops", (POINTER(IApplicationView), POINTER(UINT))),
        COMMETHOD([], HRESULT, "GetCurrentDesktop", (["out"], POINTER(POINTER(IVirtualDesktop)), "pDesktop"),),
        COMMETHOD([], HRESULT, "GetDesktops", (["out"], POINTER(POINTER(IObjectArray)), "array")),
        STDMETHOD(HRESULT, "GetAdjacentDesktop", (POINTER(IVirtualDesktop), AdjacentDesktop, POINTER(POINTER(IVirtualDesktop)),)),
        STDMETHOD(HRESULT, "SwitchDesktop", (POINTER(IVirtualDesktop),)),
        COMMETHOD([], HRESULT, "CreateDesktopW", (["out"], POINTER(POINTER(IVirtualDesktop)), "pDesktop"),),
        COMMETHOD([], HRESULT, "RemoveDesktop", (["in"], POINTER(IVirtualDesktop), "destroyDesktop"), (["in"], POINTER(IVirtualDesktop), "fallbackDesktop")),
        COMMETHOD([], HRESULT, "FindDesktop", (["in"], POINTER(GUID), "pGuid"), (["out"], POINTER(POINTER(IVirtualDesktop)), "pDesktop")),
        STDMETHOD(HRESULT, "Unknown", (POINTER(IVirtualDesktop), POINTER(POINTER(IObjectArray)), POINTER(POINTER(IObjectArray)))),
        COMMETHOD([], HRESULT, "SetName", (["in"], POINTER(IVirtualDesktop), "pDesktop"), (["in"], HSTRING, "name")),
    ]


# aa509086-5ca9-4c25-8f95-589d3c07b48a ?
# HKEY_LOCAL_MACHINE\SOFTWARE\Classes\Interface\{A5CD92FF-29BE-454C-8D04-D82879FB3F1B}
class IVirtualDesktopManager(IUnknown):
    _iid_ = GUID("{A5CD92FF-29BE-454C-8D04-D82879FB3F1B}")
    _methods_ = [
        COMMETHOD([], HRESULT, "IsWindowOnCurrentVirtualDesktop",
            (["in"], HWND, "hwnd"),
            (["out"], POINTER(BOOL), "isOnCurrent"),
        ),
        STDMETHOD(HRESULT, "GetWindowDesktopId", (HWND, POINTER(GUID))),
        STDMETHOD(HRESULT, "MoveWindowToDesktop", (HWND, REFGUID)),
    ]


class IVirtualDesktopPinnedApps(IUnknown):
    _iid_ = GUID("{4CE81583-1E4C-4632-A621-07A53543148F}")
    _methods_ = [
        # IVirtualDesktopPinnedApps methods
        COMMETHOD([], HRESULT, "IsAppIdPinned",
            (["in"], LPCWSTR, "appId"),
            (["out"], POINTER(BOOL), "isPinned"),
        ),
        STDMETHOD(HRESULT, "PinAppID", (LPCWSTR,)),
        STDMETHOD(HRESULT, "UnpinAppID", (LPCWSTR,)),
        COMMETHOD([], HRESULT, "IsViewPinned",
            (["in"], POINTER(IApplicationView), "pView"),
            (["out"], POINTER(BOOL), "isPinned"),
        ),
        STDMETHOD(HRESULT, "PinView", (POINTER(IApplicationView),)),
        STDMETHOD(HRESULT, "UnpinView", (POINTER(IApplicationView),)),
    ]


# In registry: Computer\HKEY_LOCAL_MACHINE\SOFTWARE\Classes\Interface\{1841C6D7-4F9D-42C0-AF41-8747538F10E5}
class IApplicationViewCollection(IUnknown):
    _iid_ = GUID("{1841C6D7-4F9D-42C0-AF41-8747538F10E5}")
    _methods_ = [
        # IApplicationViewCollection methods
        STDMETHOD(HRESULT, "GetViews", (POINTER(POINTER(IObjectArray)),)),
        # STDMETHOD(HRESULT, "GetViewsByZOrder", (POINTER(POINTER(IObjectArray)),)),
        COMMETHOD([], HRESULT, "GetViewsByZOrder", (["out"], POINTER(POINTER(IObjectArray)), "array")),
        STDMETHOD(HRESULT, "GetViewsByAppUserModelId", (LPCWSTR, POINTER(POINTER(IObjectArray)))),
        COMMETHOD([], HRESULT, "GetViewForHwnd",
            (["in"], HWND, "hwnd"),
            (["out"], POINTER(POINTER(IApplicationView)), "pView")
        ),
        STDMETHOD(HRESULT, "GetViewForApplication", (POINTER(IImmersiveApplication), POINTER(POINTER(IApplicationView)))),
        STDMETHOD(HRESULT, "GetViewForAppUserModelId", (LPCWSTR, POINTER(POINTER(IApplicationView)))),
        COMMETHOD([], HRESULT, "GetViewInFocus", (["out"], POINTER(POINTER(IApplicationView)), "view")),
        STDMETHOD(HRESULT, "Unknown1", (POINTER(POINTER(IApplicationView)),)),
        STDMETHOD(HRESULT, "RefreshCollection", ()),
        STDMETHOD(HRESULT, "RegisterForApplicationViewChanges", (POINTER(IApplicationViewChangeListener), POINTER(DWORD))),
        # Removed in 1809
        # STDMETHOD(HRESULT, "RegisterForApplicationViewPositionChanges", (POINTER(IApplicationViewChangeListener), POINTER(DWORD),)),
        STDMETHOD(HRESULT, "UnregisterForApplicationViewChanges", (DWORD,)),
    ]


class IServiceProvider(IUnknown):
    _iid_ = GUID("{6D5140C1-7436-11CE-8034-00AA006009FA}")
    _methods_ = [
        STDMETHOD(HRESULT, "QueryService", (REFGUID, REFIID, POINTER(LPVOID),)),
    ]

from comtypes import CLSCTX_LOCAL_SERVER, CoCreateInstance, CoInitializeEx
CLSID_VirtualDesktopManagerInternal = GUID("{C5E0CDCA-7B6E-41B2-9FC4-D93975CC467B}")
GUID_IVirtualDesktopManagerInternal_26100 = GUID("{53F5CA0B-158F-4124-900C-057158060B27}")
CLSID_ImmersiveShell = GUID("{C2F03A33-21F5-47FA-B4BB-156362A2F239}")
GUID_IVirtualDesktopManagerInternal=GUID_IVirtualDesktopManagerInternal_26100
def _get_object(cls,clsid=None):
    try:
        pServiceProvider = CoCreateInstance(
            CLSID_ImmersiveShell,IServiceProvider,CLSCTX_LOCAL_SERVER
        )
        pObject=POINTER(cls)()
        pServiceProvider.QueryService( # type: ignore
            clsid or cls._iid_,
            cls._iid_,
            pObject,
        )
    except Exception as e:
        winver = sys.getwindowsversion()
        platver = sys.getwindowsversion().platform_version
        raise NotImplementedError(
            f"Interface {cls.__name__} with ID {cls._iid_} not supported for windows version {winver.major}.{winver.minor}.{winver.build}, platform version {platver[0]}.{platver[1]}.{platver[2]}. Please open an issue at https://github.com/mrob95/pyvda/issues."
        ) from e
    return pObject