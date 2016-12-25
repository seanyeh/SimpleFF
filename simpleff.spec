# -*- mode: python -*-

import sys

_os = sys.platform
if _os.startswith("linux"):
    _os = "linux"

block_cipher = None

datas = [
    ("src/bin/ffmpeg-" + _os, "bin"),
    ("src/bin/ffprobe-" + _os, "bin"),
]

a = Analysis(['src/simpleff.py'],
             pathex=['.'],
             binaries=datas,
             datas=None,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='simpleff',
          debug=False,
          strip=False,
          upx=True,
          console=True )
