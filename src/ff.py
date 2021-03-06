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


import math
import os
import pkgutil
import stat
import sys
import tempfile

from subprocess import Popen, PIPE, CalledProcessError
from threading import Thread

import bin

class FF:

    def __init__(self):
        # Setup binaries

        _os = sys.platform

        if _os == "win32":
            _os += ".exe"
        if _os.startswith("linux"):
            _os = "linux" # change linux2, etc. to just linux

        self.ffprobe = self._gen_ffbinary("ffprobe-" + _os)
        self.ffmpeg = self._gen_ffbinary("ffmpeg-" + _os)

        self.process = None
        self.thread = None


    def _gen_ffbinary(self, ffname):
        bin_data = pkgutil.get_data("bin", ffname)

        temp = tempfile.NamedTemporaryFile(delete=False)
        temp.write(bin_data)
        temp.close()

        # chmod +x
        os.chmod(temp.name, os.stat(temp.name).st_mode | stat.S_IEXEC)

        return temp


    def get_duration(self, filename):
        p = Popen([
            self.ffprobe.name,
            "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            filename
            ],
            stdout=PIPE, stderr=PIPE)

        (output, _) = p.communicate()
        code = p.returncode
        result = None

        if code == 0:
            # If success
            try:
                secs = float(output.decode("utf-8"))
                result = FFTime(1000 * secs)
            except ValueError:
                # If no duration found, then probably is not valid file
                code = 1

        return code, result


    # Adapted from http://stackoverflow.com/a/4417735
    def _execute_gen(self, process):
        for stderr_line in iter(process.stderr.readline, ""):
            yield stderr_line

        process.stderr.close()
        return_code = process.wait()

        if return_code:
            raise CalledProcessError(return_code, "")


    def _execute(self, process, msg_signal, finish_signal):
        try:
            for line in self._execute_gen(process):
                msg_signal.emit(line)
        except CalledProcessError:
            # Can either result when ffmpeg fails for some reason(?)
            #   OR when process terminated. Should differentiate?
            pass

        finish_signal.emit()


    def run(self, input_file, output_file, output_codecs, slice_timestamps, msg_signal, finish_signal):
        print("run:", slice_timestamps)

        slice_start, slice_time = [], []
        if slice_timestamps[0]:
            slice_start = ["-ss", str(slice_timestamps[0])]
        if slice_timestamps[1]:
            slice_time = ["-t", str(slice_timestamps[1])]


        cmd = [self.ffmpeg.name] + \
                slice_start + ["-y", "-i", input_file] + slice_time + \
                output_codecs.args + [output_file]

        print(" ".join(cmd))

        self.process = Popen(cmd, stdout=PIPE, stderr=PIPE, universal_newlines=True)

        self.thread = Thread(target=lambda: self._execute(self.process, msg_signal, finish_signal))
        self.thread.start()


    def terminate(self):
        if self.process:
            self.process.terminate()
            self.process = None


    def _try_rm(self, filename):
        try:
            os.remove(filename)
        except:
            pass


    def cleanup(self):
        ''' Delete temporary files '''
        print("Cleaning up")

        self._try_rm(self.ffprobe.name)
        self._try_rm(self.ffmpeg.name)



class FFTime:
    def __init__(self, milliseconds):
        self.milliseconds = milliseconds
        pass

    def isfloat(x):
        try:
            float(x)
            return True
        except:
            return False


    # Overload add and subtract
    def __add__(self, other):
        if FFTime.isfloat(other):
            other_secs = float(other)
        else:
            other_secs = other.milliseconds

        return FFTime(self.milliseconds + other_secs)


    def __radd__(self, other):
        return self.__add__(other)


    def __sub__(self, other):
        if FFTime.isfloat(other):
            other_secs = float(other)
        else:
            other_secs = other.milliseconds

        return FFTime(self.milliseconds - other_secs)


    def _pad(n, length=2):
        s = str(n)
        padding = length * "0"

        return (padding + s)[-length:]


    # Pretty
    def __str__(self):
        secs = math.floor(self.milliseconds / 1000)

        hours = math.floor(secs/3600)
        secs -= 3600 * hours

        mins = math.floor(secs/60)
        secs -= 60 * mins

        ms = int(self.milliseconds % 1000)


        return "%s:%s:%s.%s" % (
                FFTime._pad(hours),
                FFTime._pad(mins),
                FFTime._pad(secs),
                FFTime._pad(ms, 3)
                )


    def to_ms(self):
        return self.milliseconds

