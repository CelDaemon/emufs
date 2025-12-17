import emufs
from pathlib import Path, PurePosixPath

with emufs.open(Path("~/Downloads/source.devz").expanduser()) as fs:
    print(fs.stat(PurePosixPath("/code/cpu")))
    fs.mkdir(PurePosixPath("/code/meow"))
    print(fs.ls(PurePosixPath("/code")))

    with fs.open(PurePosixPath("/code/meow.txt"), "a+") as f:
        f.write("meow")

    with fs.open(PurePosixPath("/code/Controller.js"), "r") as f:
        print(f.read(100))

    fs.chmod(PurePosixPath("/code/Cartridge.js"), 0o000)

    fs.unlink(PurePosixPath("/code/Controller.js"))
    fs.write(Path("~/Downloads/target.devz").expanduser())
