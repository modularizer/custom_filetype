import traceback

import PyQt5
import PyQt5.QtWidgets
import PyQt5.QtGui

from thumbnail import CustomFileTypeThumbnailProvider


class CustomApplicationWindow(PyQt5.QtWidgets.QMainWindow):
    def __init__(self, file_path):
        super().__init__()
        # give the window a title
        self.setWindowTitle(f"Custom Application: {file_path}")
        # set the window size
        self.resize(800, 600)
        # create a central widget
        self.central_widget = PyQt5.QtWidgets.QWidget()

        # create a layout
        self.layout = PyQt5.QtWidgets.QVBoxLayout()

        # create a label
        self.label = PyQt5.QtWidgets.QLabel()

        # create a pixmap
        self.pixmap = PyQt5.QtGui.QPixmap()

        # set the pixmap to the label
        self.label.setPixmap(self.pixmap)

        # add the label to the layout
        self.layout.addWidget(self.label)

        # set the layout to the central widget
        self.central_widget.setLayout(self.layout)

        # set the central widget
        self.setCentralWidget(self.central_widget)

        # load the thumbnail
        self.load_thumbnail(file_path)
        self.show()

    def load_thumbnail(self, file_path):
        print(f"Loading thumbnail for {file_path}")
        handler = CustomFileTypeThumbnailProvider(file_path)
        thumbnail_bytes, fmt = handler.get_thumbnail_bytes(500)
        if fmt == 'png':
            pixmap = PyQt5.QtGui.QPixmap()
            pixmap.loadFromData(thumbnail_bytes)
            self.label.setPixmap(pixmap)
        else:
            print("Unsupported format")

    @classmethod
    def run(cls, file_path=None):
        import sys
        if file_path is None:
            file_path = sys.argv[1] if len(sys.argv) > 1 else None
            if file_path is None:
                print("Please provide a file path")
                return
        app = PyQt5.QtWidgets.QApplication([])
        window = cls(file_path)
        sys.exit(app.exec_())



if __name__ == "__main__":
    try:
        CustomApplicationWindow.run()
    except Exception as e:
        print(f"Error: {str(e)}")
        print(str(traceback.format_exc()))
    input("Press enter to exit")