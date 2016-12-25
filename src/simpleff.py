import atexit
import functools
import os
import signal
import sys

from PyQt5.QtWidgets import (
        QApplication,
        QComboBox,
        QDesktopWidget,
        QFileDialog,
        QFormLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QTabWidget,
        QTextEdit,
        QVBoxLayout,
        QWidget,
        )

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon

# Local imports
import ff
from output_codecs import AVAILABLE_CODECS
import qtRangeSlider


# Globals
FF = ff.FF()

WIDTH = 600
HEIGHT = 480


class App(QMainWindow):

    def __init__(self):
        super().__init__()
        self.title = "SimpleFF"
        self.resize(WIDTH, HEIGHT)
        self.setWindowTitle(self.title)
        center = QDesktopWidget().availableGeometry().center()
        self.move(center.x() - (WIDTH/2), center.y() - (HEIGHT/2))

        self.table_widget = TabWidget(self)
        self.setCentralWidget(self.table_widget)

        self.show()

    def closeEvent(self, event):
        # First terminate running processes
        FF.terminate()

        event.accept()


class FilePickerWidget(QWidget):

    def __init__(self, parent, is_input):
        super(QWidget, self).__init__(parent)
        self.parent = parent

        self.is_input = is_input
        self.filename = None

        # Setup GUI
        self.layout = QHBoxLayout(self)

        if is_input:
            self.file_button = QPushButton("Choose file")
        else:
            self.file_button = QPushButton("Save as")

        self.file_button.clicked.connect(
                functools.partial(self.on_file_select, is_input=is_input))

        self.input_line = QLineEdit()
        self.input_line.setReadOnly(True)

        self.layout.addWidget(self.input_line)
        self.layout.addWidget(self.file_button)


        self.setLayout(self.layout)


    def _get_current_ext(self):
        return "." + self.parent.codecs_widget.get_codec().ext

    def on_file_select(self, is_input):
        if self.is_input:
            fdialog, title = QFileDialog.getOpenFileName, "Choose input file"
        else:
            fdialog, title = QFileDialog.getSaveFileName, "Save as"

        start_dir = os.getenv("Home")

        # If filename already chosen before, make the file picker default to
        # that file (path) when opened
        if self.filename:
            start_dir = self.filename

        self.filename, _ = fdialog(self, title, start_dir)

        # If filename is valid
        if is_input and self.validate_file(self.filename, is_input):
            # Set filename
            self.set_filename(self.filename)

            self.set_default_output()

        if not is_input:
            self.set_default_output(self.filename)


    def validate_file(self, filename, is_input):
        if is_input:
            error_code, length = FF.get_duration(filename)

            if error_code == 0:
                # Reset slider to match new input video length
                self.parent.slice_widget.set_hslider(length)
                return True
            else:
                if filename != "":
                    # Don't show "Invalid file" message if no file was chosen
                    QMessageBox.critical(self, "Error", "Not a valid video file")
                return False

        return True


    def set_default_output(self, filename=None):
        '''
        Set a valid filename for the output_widget

        Called with a filename arg only on output_file change
        '''

        input_widget = self.parent.input_widget
        output_widget = self.parent.output_widget

        if filename == None:
            filename = output_widget.get_filename()


        new_ext = self._get_current_ext()

        if filename.endswith(new_ext):
            # If filename is okay, don't change it
            output_widget.set_filename(filename)
            return

        if filename == "":
            # If output is blank, use input filename as base
            base = input_widget.get_filename().rsplit(".", 1)[0]
        else:
            base = filename.rsplit(".", 1)[0]

        new_filename = base + new_ext
        output_widget.set_filename(new_filename)


    def get_filename(self):
        return self.input_line.text()


    def set_filename(self, filename):
        self.input_line.setText(filename)



class CodecsWidget(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.parent = parent
        self.layout = QHBoxLayout(self)

        self.combo = QComboBox()
        for codec_obj in AVAILABLE_CODECS:
            self.combo.addItem(codec_obj.name, codec_obj)

        self.combo.currentIndexChanged.connect(self.on_change)

        self.layout.addWidget(self.combo)
        self.setLayout(self.layout)


    def on_change(self):
        # Update output filename extension
        output_widget = self.parent.output_widget

        if output_widget.get_filename() != "":
            output_widget.set_default_output()


    def get_codec(self):
        return self.combo.currentData()


class SliceWidget(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)

        self.is_reversed = False

        # Setup GUI
        self.layout = QVBoxLayout(self)

        self.hlayout = QWidget()

        status = QHBoxLayout(self.hlayout)
        self.min_ts = QLabel("00:00:00.000")
        self.max_ts = QLabel("00:00:00.000")
        self.max_ts.setAlignment(Qt.AlignRight)

        status.addWidget(self.min_ts)
        status.addWidget(self.max_ts)

        self.hlayout.setLayout(status)

        # Sets up self.hslider
        self.set_hslider(ff.FFTime(2000))
        self.hslider.setEnabled(False)

        def on_change(min_val, max_val):
            if self.is_reversed:
                # Swap min,max if reversed
                min_val, max_val = max_val, min_val

            if min_val > max_val:
                self.is_reversed = not self.is_reversed

            min_ts = ff.FFTime(min_val)
            self.min_ts.setText(str(min_ts))

            max_ts = ff.FFTime(max_val)
            self.max_ts.setText(str(max_ts))

            print("on_change: %s,%s" % (str(min_val), str(max_val)))

        self.hslider.rangeChanged.connect(on_change)

        self.layout.addWidget(self.hlayout)
        self.layout.addWidget(self.hslider)

        self.setLayout(self.layout)


    def set_hslider(self, length):
        ms = length.to_ms()

        try:
            self.hslider.setEnabled(True)
            self.hslider.setRange([0, ms, 1])
            self.hslider.setValues([0, ms])

            self.min_ts.setText("00:00:00.000")
            self.max_ts.setText(str(length))
        except:
            # First setup
            self.hslider = qtRangeSlider.QHRangeSlider(
                    slider_range=[0, ms, 100],
                    values=[0, ms])
            self.hslider.setMinimumHeight(16)
            self.hslider.setMaximumHeight(16)
            self.hslider.setEmitWhileMoving(True)

            self.min_ts.setText("00:00:00.000")
            self.max_ts.setText("00:00:00.000")


    def get_slice_timestamps(self):
        slice_start, slice_time = None, None
        min_val, max_val = self.get_values()

        if min_val > 0:
            slice_start = ff.FFTime(min_val)
        if max_val < self.hslider.end:
            slice_time = ff.FFTime(max_val - min_val)

        return (slice_start, slice_time)


    def get_values(self):
        if self.is_reversed:
            return (self.hslider.max_val, self.hslider.min_val)

        return (self.hslider.min_val, self.hslider.max_val)


class ConsoleArea(QTextEdit):

    msg_signal = pyqtSignal(str)

    def __init__(self, parent):
        super(QTextEdit, self).__init__(parent)

        self.msg_signal.connect(self.append)


    def append(self, s):
        self.insertPlainText(s)
        self.ensureCursorVisible()


class RunButton(QPushButton):
    finish_signal = pyqtSignal()

    # Enums
    IDLE = 0
    RUNNING = 1

    def __init__(self, parent):
        super(QPushButton, self).__init__("Run", parent)
        self.parent = parent

        self.clicked.connect(self.on_click)

        self.status = RunButton.IDLE;

        self.finish_signal.connect(self.on_finish)


    def set_status(self, status):
        self.status = status

        if status == RunButton.RUNNING:
            self.setText("Stop")

        if status == RunButton.IDLE:
            self.setText("Run")

    def on_click(self):

        if self.status == RunButton.IDLE:

            input_file = self.parent.input_widget.get_filename()
            output_file = self.parent.output_widget.get_filename()
            codec = self.parent.codecs_widget.get_codec()
            slice_timestamps = self.parent.slice_widget.get_slice_timestamps()

            # Exit if input/output file not chosen
            if not input_file or not output_file:
                QMessageBox.critical(self, "Error",
                        "You must select an input and output file")
                return


            # Warn if will overwrite existing file
            if os.path.exists(output_file):
                msg = "File \"%s\" already exists. Do you want to replace it?" \
                        % output_file

                reply = QMessageBox.warning(self, "Warning", msg,
                        QMessageBox.Yes, QMessageBox.No)
                if not reply == QMessageBox.Yes:
                    return


            # Run process
            self.set_status(RunButton.RUNNING)
            FF.run(input_file, output_file, codec,
                    slice_timestamps,
                    self.parent.msg_text.msg_signal, self.finish_signal)

        elif self.status == RunButton.RUNNING:
            # Terminate process
            self.set_status(RunButton.IDLE)
            FF.terminate()


    def on_finish(self):
        self.set_status(RunButton.IDLE)
        self.parent.msg_text.append("\nDone\n")


class TabWidget(QWidget):

    def __init__(self, parent):
        super(QWidget, self).__init__(parent)
        self.layout = QVBoxLayout(self)

        # Initialize tab screen
        self.tabs = QTabWidget()

        tab1 = QWidget()
        # self.tab2 = QWidget()
        form = QWidget()

        # Add tabs
        self.tabs.addTab(tab1, "Convert")
        # self.tabs.addTab(self.tab2, "Custom")

        # Create first tab
        tab1.layout = QVBoxLayout(self)

        form.layout = QFormLayout(self)

        # Inputs/outputs
        self.input_widget = FilePickerWidget(self, is_input=True)
        self.output_widget = FilePickerWidget(self, is_input=False)
        form.layout.addRow("Input:", self.input_widget)
        form.layout.addRow("Output:", self.output_widget)

        # Codecs
        self.codecs_widget = CodecsWidget(self)
        form.layout.addRow("Output Format:", self.codecs_widget)


        # Slice
        self.slice_widget = SliceWidget(self)
        form.layout.addRow("Slice:", self.slice_widget)

        form.setLayout(form.layout)
        ## End Form

        # button
        self.go_button = RunButton(self)

        # Message area
        self.msg_text = ConsoleArea(self)
        self.msg_text.setReadOnly(True)


        tab1.layout.addWidget(form)
        tab1.layout.addWidget(self.go_button)
        tab1.layout.addWidget(self.msg_text)

        tab1.setLayout(tab1.layout)

        # Add tabs to widget
        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)



def on_sigint(*args):
    FF.cleanup()
    QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Interpreter thread every half second
    timer = QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    # Allow Ctrl-C to exit
    signal.signal(signal.SIGINT, on_sigint)

    # Cleanup temp files on exit
    atexit.register(FF.cleanup)

    # Run
    main_app = App()
    sys.exit(app.exec_())
