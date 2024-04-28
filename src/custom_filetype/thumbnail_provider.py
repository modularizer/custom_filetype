import datetime
from typing import Literal

from pathlib import Path
import win32ui
import logging
from comtypes import IUnknown, GUID, COMMETHOD, HRESULT
from ctypes import POINTER, c_wchar_p, c_ulong, windll
from ctypes.wintypes import DWORD

from win32gui import GetDC


def get_file_logger(name, path):
    logger = logging.getLogger(name)
    logging.basicConfig(level=logging.DEBUG)
    # create file handler
    handler = logging.FileHandler(path)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger

logger = get_file_logger(__name__, Path(__file__).parent / "cft_log.log")

logger.info(f"{datetime.datetime.now()} - initializing")


def bmp_bytes_to_hbitmap(bmp_bytes, cx):
    try:
        # Create a device context
        hdc = win32ui.CreateDCFromHandle(GetDC(0))

        # Create a bitmap
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(hdc, cx, cx)

        # Prepare the bitmap information
        bmp_info = bmp.GetInfo()

        # Load image data into the bitmap
        windll.gdi32.SetDIBits(hdc.GetSafeHdc(), bmp.GetHandle(), 0, bmp_info['bmHeight'], bmp_bytes, bmp_info, 0)

        # Return the HBITMAP handle
        return bmp.GetHandle()
    except Exception as e:
        print(f"Error in bmp_bytes_to_hbitmap: {str(e)}")
        return None


def png_bytes_to_hbitmap(png_bytes, cx):
    # Get device context
    hdc = win32ui.CreateDCFromHandle(GetDC(0))

    # Create bitmap
    bmp = hdc.CreateBitmap()
    bmp.CreateBitmap(cx, cx, 1, 32, png_bytes)  # 32 bits per pixel

    # Return the HBITMAP handle
    return bmp.GetHandle()


class IInitializeWithFile(IUnknown):
    _iid_ = GUID('{b7d14566-0509-4cce-a71f-0a554233bd9b}')
    _methods_ = [
        COMMETHOD([], HRESULT, 'Initialize',
                  (['in'], POINTER(c_wchar_p), 'pszFilePath'),
                  (['in'], DWORD, 'grfMode')),
    ]


class IThumbnailProvider(IUnknown):
    _iid_ = GUID('{e357fccd-a995-4576-b01f-234630154e96}')
    _methods_ = [
        COMMETHOD([], HRESULT, 'GetThumbnail',
                  (['in'], c_ulong, 'cx'),
                  (['out'], POINTER(POINTER(DWORD)), 'phbmp')),
    ]


class ThumbnailProvider(IUnknown):
    _public_methods_ = ['GetThumbnail']
    _com_interfaces_ = [IThumbnailProvider, IInitializeWithFile]

    def __init__(self, file_path=None):
        super(ThumbnailProvider, self).__init__()
        self.file_path = file_path

    def Initialize(self, pszFilePath, grfMode):
        logger.info(f"Initialize: {pszFilePath}")
        self.file_path = pszFilePath
        return HRESULT(0)  # S_OK

    def GetThumbnail(self, cx, *args):
        logger.info(f"GetThumbnail: {cx}, {args}")
        try:
            bytes, fmt = self.get_thumbnail_bytes(cx)
            logger.info(f"GetThumbnail: {len(bytes)}, {fmt}")
            if fmt == 'bmp':
                hbitmap = bmp_bytes_to_hbitmap(bytes, cx)
                return hbitmap
            elif fmt == 'png':
                return png_bytes_to_hbitmap(bytes, cx)
        except Exception as e:
            return HRESULT(1)  # E_FAIL
        return HRESULT(1)  # E_FAIL

    def get_thumbnail_bytes(self, cx) -> tuple[bytes, Literal['bmp', 'png']]:
        """Return the thumbnail bytes and format

        Args:
            cx (int): The width and height of the thumbnail

        Returns:
            bytes: The thumbnail bytes
            str: The thumbnail format (bmp or png)
        """
        raise NotImplementedError

    @classmethod
    def register(cls):
        import win32com.server.register
        win32com.server.register.UseCommandLine(cls)