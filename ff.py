import math
from subprocess import Popen, PIPE, CalledProcessError
from threading import Thread


class FF:

    def __init__(self):
        # Find binaries
        self.ffprobe = "ffprobe"
        self.ffmpeg = "ffmpeg"

        self.process = None
        self.thread = None


    def get_duration(self, filename):
        p = Popen([
            self.ffprobe,
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


        cmd = [self.ffmpeg] + \
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

