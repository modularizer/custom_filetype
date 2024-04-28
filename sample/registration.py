import traceback
from pathlib import Path

from custom_filetype import register_custom_filetype
from thumbnail import CustomFileTypeThumbnailProvider

if __name__ == "__main__":
    try:
        register_custom_filetype(".cft",
                                 "CustomFileType",
                                 str((Path(__file__).parent / "viewer.py").resolve()),
                                 CustomFileTypeThumbnailProvider,
                         {"Run My Script": "--context-menu"})
    except Exception as e:
        print(f"Error: {str(e)}")
        print(str(traceback.format_exc()))

    a = input("Press enter to exit")