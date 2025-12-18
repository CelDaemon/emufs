import emufs
from pathlib import Path, PurePosixPath

with emufs.open(Path("~/Downloads/source.devz").expanduser()) as fs:
    fs.rmdirs(PurePosixPath("/code"))
    fs.write(Path("~/Downloads/target.devz").expanduser())
