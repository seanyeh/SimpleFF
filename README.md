# SimpleFF

A simple cross-platform (Windows, OS X, Linux/Unix) frontend to FFmpeg for easy video converting and slicings.

The aim of SimpleFF is to make it super easy for everyone to perform the common video converting tasks.


### Features

 * Converting any video format to MP4
 * Extracting the audio of any video format as MP3
 * Slicing a portion of the video
 * ... with more features to come!


## Building

Since this repository uses git submodules for the FFmpeg binaries
([SimpleFF-Binaries](https://github.com/seanyeh/SimpleFF-binaries)), make sure
to use the `--recursive` flag when cloning this repository. See
[this](https://git-scm.com/book/en/v2/Git-Tools-Submodules) for more
information on submodules.

#### Requirements
 * Python 3
 * PyQt5
 * PyInstaller

Once you have the requirements installed, just run `make`.



## License

SimpleFF is licensed under the GPLv3

Special thanks to
[qtRangeSlider](https://github.com/ZhuangLab/storm-control/blob/master/hal4000/qtWidgets/qtRangeSlider.py),
which is licensed under the MIT License.
