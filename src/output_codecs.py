# Copyright (C) 2016 Sean Yeh
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


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
