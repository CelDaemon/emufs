import emufs
from pathlib import Path, PurePosixPath

with emufs.open(Path("~/Downloads/source.devz").expanduser()) as fs:
    print(fs.listdir(PurePosixPath("/")))
    print(fs.listdir(PurePosixPath("/code")))
    print(fs.stat(PurePosixPath("/code/cpu")))
    fs.mkdir(PurePosixPath("/code/meow"))
    print(fs.listdir(PurePosixPath("/code")))

    for dat in fs.walk(PurePosixPath("/code"), False):
        print(dat)

    with fs.open(PurePosixPath("/code/meow/aaaaaa.txt"), "a+") as f:
        f.write("aaaaaaaaaaa")

    with fs.open(PurePosixPath("/tmpl/bbbbb.txt"), "a+") as f:
        f.write("bbbbbbbb")

    with fs.open(PurePosixPath("/code/Controller.js"), "r") as f:
        print(f.read(100))

    fs.chmod(PurePosixPath("/code/Cartridge.js"), 0o000)

    fs.unlink(PurePosixPath("/code/Controller.js"))
    fs.write(Path("~/Downloads/target.devz").expanduser())
