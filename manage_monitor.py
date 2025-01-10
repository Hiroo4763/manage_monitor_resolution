import ctypes
from ctypes import wintypes
import sys
import uuid
import tkinter as tk
from tkinter import messagebox
import pywintypes
import win32api
import win32con

# ------------------- Windows API 설정 -------------------

# Windows API 라이브러리 로드
setupapi = ctypes.WinDLL('setupapi.dll')
cfgmgr32 = ctypes.WinDLL('cfgmgr32.dll')

# 필요한 상수 정의
DIGCF_PRESENT = 0x00000002
DIGCF_ALLCLASSES = 0x00000004
DIF_PROPERTYCHANGE = 0x12
DICS_ENABLE = 1
DICS_DISABLE = 2
DICS_FLAG_GLOBAL = 1

# 해상도 변경
def changere() :
    devmode = pywintypes.DEVMODEType()
    devmode.PelsWidth = 1568  
    devmode.PelsHeight = 1080

    devmode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT

    win32api.ChangeDisplaySettings(devmode, 0)

def changerer() :
    devmode = pywintypes.DEVMODEType()
    devmode.PelsWidth = 1920 
    devmode.PelsHeight = 1080

    devmode.Fields = win32con.DM_PELSWIDTH | win32con.DM_PELSHEIGHT

    win32api.ChangeDisplaySettings(devmode, 0)

# GUID 구조체 정의
class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8)
    ]

    def __init__(self, guid_string):
        super().__init__()
        u = uuid.UUID(guid_string)
        self.Data1 = u.time_low
        self.Data2 = u.time_mid
        self.Data3 = u.time_hi_version
        self.Data4[:] = u.bytes[8:]

# SP_CLASSINSTALL_HEADER 구조체 정의
class SP_CLASSINSTALL_HEADER(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("InstallFunction", wintypes.DWORD)
    ]

# SP_PROPCHANGE_PARAMS 구조체 정의
class SP_PROPCHANGE_PARAMS(ctypes.Structure):
    _fields_ = [
        ("ClassInstallHeader", SP_CLASSINSTALL_HEADER),
        ("StateChange", wintypes.DWORD),
        ("Scope", wintypes.DWORD),
        ("HwProfile", wintypes.DWORD)
    ]

# SP_DEVINFO_DATA 구조체 정의
class SP_DEVINFO_DATA(ctypes.Structure):
    _fields_ = [
        ('cbSize', wintypes.DWORD),
        ('ClassGuid', GUID),
        ('DevInst', wintypes.DWORD),
        ('Reserved', ctypes.POINTER(ctypes.c_ulong)),
    ]

# 함수 원형 설정
setupapi.SetupDiGetClassDevsW.restype = wintypes.HANDLE
setupapi.SetupDiGetClassDevsW.argtypes = [
    ctypes.POINTER(GUID),
    wintypes.LPCWSTR,
    wintypes.HWND,
    wintypes.DWORD
]

setupapi.SetupDiEnumDeviceInfo.restype = wintypes.BOOL
setupapi.SetupDiEnumDeviceInfo.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    ctypes.POINTER(SP_DEVINFO_DATA)
]

setupapi.SetupDiGetDeviceInstanceIdW.restype = wintypes.BOOL
setupapi.SetupDiGetDeviceInstanceIdW.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(SP_DEVINFO_DATA),
    wintypes.LPWSTR,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD)
]

setupapi.SetupDiSetClassInstallParamsW.restype = wintypes.BOOL
setupapi.SetupDiSetClassInstallParamsW.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(SP_DEVINFO_DATA),
    ctypes.POINTER(SP_PROPCHANGE_PARAMS),
    wintypes.DWORD
]

setupapi.SetupDiCallClassInstaller.restype = wintypes.BOOL
setupapi.SetupDiCallClassInstaller.argtypes = [
    wintypes.DWORD,
    wintypes.HANDLE,
    ctypes.POINTER(SP_DEVINFO_DATA)
]

setupapi.SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL
setupapi.SetupDiDestroyDeviceInfoList.argtypes = [wintypes.HANDLE]

# ------------------- 장치 상태 변경 함수 -------------------

def change_device_state(device_instance_id, enable=True):
    """
    주어진 Device Instance ID를 가진 장치를 활성화 또는 비활성화합니다.
    """
    # GUID_DEVCLASS_MONITOR = {4d36e96e-e325-11ce-bfc1-08002be10318}
    GUID_DEVCLASS_MONITOR = GUID('{4d36e96e-e325-11ce-bfc1-08002be10318}')

    # 장치 클래스의 장치 목록 가져오기
    hDevInfo = setupapi.SetupDiGetClassDevsW(
        ctypes.byref(GUID_DEVCLASS_MONITOR),
        None,
        None,
        DIGCF_PRESENT | DIGCF_ALLCLASSES
    )

    if hDevInfo == ctypes.c_void_p(-1).value:
        messagebox.showerror("오류", "장치 목록을 가져오는 데 실패했습니다.")
        return False

    try:
        index = 0
        devinfo = SP_DEVINFO_DATA()
        devinfo.cbSize = ctypes.sizeof(SP_DEVINFO_DATA)

        while setupapi.SetupDiEnumDeviceInfo(hDevInfo, index, ctypes.byref(devinfo)):
            # 장치 인스턴스 ID 가져오기
            buffer_size = 256
            device_id_buffer = ctypes.create_unicode_buffer(buffer_size)
            required_size = wintypes.DWORD()

            if setupapi.SetupDiGetDeviceInstanceIdW(
                hDevInfo,
                ctypes.byref(devinfo),
                device_id_buffer,
                buffer_size,
                ctypes.byref(required_size)
            ):
                current_device_id = device_id_buffer.value
                if current_device_id.lower() == device_instance_id.lower():
                    # SP_PROPCHANGE_PARAMS 구조체 설정
                    propchange = SP_PROPCHANGE_PARAMS()
                    propchange.ClassInstallHeader.cbSize = ctypes.sizeof(SP_CLASSINSTALL_HEADER)
                    propchange.ClassInstallHeader.InstallFunction = DIF_PROPERTYCHANGE
                    propchange.StateChange = DICS_ENABLE if enable else DICS_DISABLE
                    propchange.Scope = DICS_FLAG_GLOBAL
                    propchange.HwProfile = 0

                    # 클래스 설치 매개변수 설정
                    if not setupapi.SetupDiSetClassInstallParamsW(
                        hDevInfo,
                        ctypes.byref(devinfo),
                        ctypes.byref(propchange),
                        ctypes.sizeof(propchange)
                    ):
                        messagebox.showerror("오류", "SetupDiSetClassInstallParamsW 실패.")
                        return False

                    # 클래스 설치 프로그램 호출하여 장치 상태 변경
                    if not setupapi.SetupDiCallClassInstaller(
                        DIF_PROPERTYCHANGE,
                        hDevInfo,
                        ctypes.byref(devinfo)
                    ):
                        messagebox.showerror("오류", "SetupDiCallClassInstaller 실패.")
                        return False

                    action = "활성화" if enable else "비활성화"
                    messagebox.showinfo("성공", f"장치 {device_instance_id}가 성공적으로 {action}되었습니다.")
                    return True

            index += 1

        action = "활성화" if enable else "비활성화"
        messagebox.showwarning("경고", f"장치 {device_instance_id}를 찾을 수 없습니다.")
        return False
    finally:
        setupapi.SetupDiDestroyDeviceInfoList(hDevInfo)

# ------------------- Tkinter GUI 설정 -------------------

class DeviceManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("모니터 장치 관리")
        self.root.geometry("500x200")
        self.root.resizable(False, False)

        # 버튼 프레임
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(pady=20)

        # 활성화 버튼
        self.enable_button = tk.Button(self.button_frame, text="활성화", width=15, command=self.enable_device, bg="green", fg="white", font=("Arial", 12))
        self.enable_button.grid(row=0, column=0, padx=10)

        # 비활성화 버튼
        self.disable_button = tk.Button(self.button_frame, text="비활성화", width=15, command=self.disable_device, bg="red", fg="white", font=("Arial", 12))
        self.disable_button.grid(row=0, column=1, padx=10)

    def enable_device(self):
        device_id = "DISPLAY\\DELA1C4\\5&1249343B&3&UID4353"
        device_id2 = "DISPLAY\\BNQ7F81\\5&1249343B&3&UID4357"

        if not device_id:
            messagebox.showwarning("입력 오류", "Device Instance ID를 입력하세요.")
            return
        result = change_device_state(device_id, enable=True)
        result2 = change_device_state(device_id2, enable=True)
        changerer()
        if result:
            # 추가 작업이 필요하면 여기에 작성
            pass
        if result2:
            pass

    def disable_device(self):
        device_id = "DISPLAY\\DELA1C4\\5&1249343B&3&UID4353"
        device_id2 = "DISPLAY\\BNQ7F81\\5&1249343B&3&UID4357"

        if not device_id:
            messagebox.showwarning("입력 오류", "Device Instance ID를 입력하세요.")
            return
        result = change_device_state(device_id, enable=False)
        result2 = change_device_state(device_id2, enable=False)
        changere()
        if result:
            # 추가 작업이 필요하면 여기에 작성
            pass
        if result2:
            pass

# ------------------- 메인 실행 -------------------

def main():
    # 관리자 권한 확인
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    if not is_admin:
        messagebox.showerror("권한 오류", "이 스크립트를 관리자 권한으로 실행하세요.")
        sys.exit(1)

    # Tkinter 루트 생성
    root = tk.Tk()
    app = DeviceManagerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
