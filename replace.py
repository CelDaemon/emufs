#!/usr/bin/env python
import emufs
import os
from sys import argv
from pathlib import Path, PurePosixPath

source = Path(argv[1])
target = Path(argv[2])

source_inner = Path(argv[3])

target_inner = PurePosixPath(argv[4])

with emufs.open(source) as fs:
    if stat := fs.stat(target_inner):
        assert(stat.is_dir())
        for path, dirs, nondirs in fs.walk(target_inner, False):
            for entry in dirs + nondirs:
                fs.unlink(path / entry)
    else:
        fs.mkdir(target_inner)

    for path, dirs, nondirs in os.walk(source_inner):
        path = Path(path)
        path_inner = target_inner / path.relative_to(source_inner).as_posix()
        print(path_inner)
        for dir in dirs:
            print(path_inner / dir)
            fs.mkdir(path_inner / dir)
        for nondir in nondirs:
            assert(os.path.isfile(path / nondir))
            print(path_inner / nondir)
            with fs.open(path_inner / nondir, "wb") as f:
                f.write((path / nondir).read_bytes())
    fs.write(target)
