# custom_filetype

Tools for registering custom filetypes to the system.

## Features
* [x] The default application to launch when opening a file
  * [x] Windows
  * [ ] Linux
* [x] Context menu actions when you right click a file
  * [x] Windows
  * [ ] Linux
* [ ] Thumbnail icon for each file in the file explorer
  * [ ] Windows
  * [ ] Linux
* [ ] File preview in the preview tab
  * [ ] Windows
  * [ ] Linux


## Usage

```python
from typing import Literal
from custom_filetype import register_custom_filetype, ThumbnailProvider


class CustomFileTypeThumbnailProvider(ThumbnailProvider):
    def get_thumbnail_bytes(self, cx) -> tuple[bytes, Literal['bmp', 'png']]:
        """Return the thumbnail bytes and format

        Args:
            cx (int): The width and height of the thumbnail

        Returns:
            bytes: The thumbnail bytes
            str: The thumbnail format (bmp or png)
        """
        # TODO: Implement this
        raise NotImplementedError("This method must be implemented, to return png_bytes, 'png'")


register_custom_filetype(".cft",
                         "CustomFileType",
                         str((Path(__file__).parent / "viewer.py").resolve()),
                         CustomFileTypeThumbnailProvider,
                         {"Run My Script": "--context-menu"})
```

