import shlex
import sys


class OutputCodec:
    def __init__(self, name, ext, args):
        self.name = name
        self.ext = ext

        if sys.platform == 'win32':
            self.args = [args]
        else:
            self.args = shlex.split(args)



AVAILABLE_CODECS = [
        OutputCodec("MP4 (libx264)", "mp4",
            "-c:v libx264 -crf 22 -c:a aac -b:a 160k"),

        OutputCodec("MP3 (Audio-only)", "mp3",
            "-vn -c:a libmp3lame -q:a 0")
]
