import io
import os
import sqlite3
import sys

import numpy as np
import lz4.frame


class CustomFileTypeWriter:
    def __init__(self, file_path):
        self.file_path = file_path
        if not os.path.exists(file_path):
            self.write()

    def write(self):
        conn = sqlite3.connect(self.file_path)
        cursor = conn.cursor()
        cursor.executescript("""
CREATE TABLE IF NOT EXISTS thumbnails (
    cx INTEGER PRIMARY KEY,
    thumbnail BLOB
);

CREATE TABLE IF NOT EXISTS layers (
    number INTEGER PRIMARY KEY,
    layer BLOB
);
""")
        stackup = np.zeros((1000, 1000), dtype=np.uint8)
        for layer in range(25):
            im = np.zeros((1000, 1000), dtype=np.uint8)
            s = 100 + layer * 50
            e = s + 300
            im[s:e, s:e] = 255
            stackup += (10 * (im > 0)).astype(np.uint8)
            data = self.encode(im)
            cursor.execute("INSERT INTO layers (number, layer) VALUES (?, ?);", (layer, data))
        data = self.encode(stackup)
        cursor.execute("INSERT INTO layers (number, layer) VALUEs (?, ?);", (-1, data))
        conn.commit()

    def encode(self, data):
        with io.BytesIO() as f:
            np.save(f, data)
            b = f.getvalue()
        return lz4.frame.compress(b)


if __name__ == '__main__':
    fn = sys.argv[1] if len(sys.argv) > 1 else "test.cft"
    writer = CustomFileTypeWriter(fn)