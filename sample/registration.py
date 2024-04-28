import traceback
from pathlib import Path

from win32comext.shell.shell import SHChangeNotify
from win32comext.shell.shellcon import SHCNE_ASSOCCHANGED, SHCNF_IDLIST

from custom_filetype import register_custom_filetype
from viewer import CustomFileTypeThumbnailProvider

if __name__ == "__main__":
    try:

        register_custom_filetype()
        CustomFileTypeThumbnailProvider.register()
        SHChangeNotify(SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None)
    except Exception as e:
        print(f"Error: {str(e)}")
        print(str(traceback.format_exc()))
    input("Press enter to exit")