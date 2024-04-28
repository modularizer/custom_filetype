import io
import sqlite3

import numpy as np
import lz4.frame
import cv2

from custom_filetype import ThumbnailProvider


class CustomFileTypeThumbnailProvider(ThumbnailProvider):
    def encode(self, data):
        with io.BytesIO() as f:
            np.save(f, data)
            b = f.getvalue()
        return lz4.frame.compress(b)

    def decode(self, data):
        b = lz4.frame.decompress(data)
        with io.BytesIO(b) as f:
            return np.load(f)

    def get_thumbnail_bytes(self, cx):
        conn = sqlite3.connect(self.file_path)
        cursor = conn.cursor()
        thumbnail_data = cursor.execute("SELECT thumbnail FROM thumbnails WHERE cx = ?", (cx,)).fetchone()
        if thumbnail_data:
            print("Thumbnail found in database")
            return thumbnail_data[0], 'png'

        stackup_data = cursor.execute("SELECT layer FROM layers WHERE number = -1").fetchone()[0]
        stackup = self.decode(stackup_data)
        min_shape = min(stackup.shape)
        i = (min_shape // cx)
        thumbnail = stackup[::i, ::i][:cx, :cx]
        # convert to png bytes
        b = cv2.imencode('.png', thumbnail)[1].tobytes()
        print("Thumbnail not found in database, creating")
        cursor.execute("INSERT INTO thumbnails (cx, thumbnail) VALUES (?, ?);", (cx, b))
        conn.commit()
        return b, 'png'
