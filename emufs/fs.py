from tempfile import TemporaryDirectory
from pathlib import Path, PurePosixPath
from zipfile import ZipFile
from typing import Self, Generator
from base64 import b64encode
from json import loads, dumps
from uuid import uuid4

from .inode import Inode, TYPE_DIR
from .io import EmuFileIO
from .stat import Stat

_ROOT_INODE_ID = "/"


class EmuFS:
    _tmp: TemporaryDirectory
    _fs_path: Path
    _base: Path
    _closed: bool

    def __init__(self, tmp: TemporaryDirectory, base: Path) -> None:
        self._tmp = tmp
        self._base = base
        self._fs_path = base / "indexeddb"
        self._closed = False

    def write(self, path: Path) -> None:
        assert(not self._closed)
        with ZipFile(path, "w") as zip:
            for [dirpath, _, filenames] in self._base.walk():
                for filename in filenames:
                    filepath = dirpath / filename
                    zip.write(filepath, filepath.relative_to(self._base))

    def stat(self, path: PurePosixPath) -> Stat | None:
        inode_id = self._resolve_path(path)

        if not inode_id:
            return None

        inode = self._read_inode(inode_id)

        return Stat.from_inode(inode_id, inode)

    def mkdir(self, path: PurePosixPath) -> None:
        parent_inode_id = self._resolve_path(path.parent)
        if not parent_inode_id:
            raise Exception(f"Directory does not exist: {path.parent}")

        new_inode_id = str(uuid4())
        new_data_id = str(uuid4())
        new_entries_data = dumps({}).encode("ascii")
        new_inode = Inode.new_empty(new_data_id, len(new_entries_data), TYPE_DIR | 0o755)

        self._get_physical_path(new_data_id).write_bytes(new_entries_data)
        self._write_inode(new_inode, new_inode_id)
        self._add_dir_entry(parent_inode_id, path.name, new_inode_id)

    def unlink(self, path: PurePosixPath) -> None:
        inode_id = self._resolve_path(path)

        if not inode_id:
            raise Exception(f"No such file or directory: {path}")

        parent_inode_id = self._resolve_path(path.parent) # TODO: Optimise path resolving to start from known parent id.

        assert(parent_inode_id != None)

        inode = self._read_inode(inode_id)

        if inode.is_dir() and len(self._get_dir_entries(inode_id)) > 0:
            raise Exception("Directory is not empty")

        self._get_physical_path(inode.data_id).unlink()
        self._get_physical_path(inode_id).unlink()
        self._remove_dir_entry(parent_inode_id, path.name)

    def listdir(self, path: PurePosixPath) -> list[str]:
        inode_id = self._resolve_path(path)
        
        if not inode_id:
            raise Exception(f"No such directory: {path}")

        return list(self._get_dir_entries(inode_id).keys())

    def walk(self, path: PurePosixPath, topdown: bool=True):
        inode_id = self._resolve_path(path)

        if not inode_id:
            raise Exception(f"No such directory: {path}")

        entries = self._get_dir_entries(inode_id)
        dirs: list[str] = []
        nondirs: list[str] = []
        for name, item_inode_id in entries.items():
            inode = self._read_inode(item_inode_id)
            if inode.is_dir():
                dirs.append(name)
            else:
                nondirs.append(name)

        if topdown:
            yield path, dirs, nondirs

        for name in dirs:
            new_path = path / name
            for x in self.walk(new_path, topdown):
                yield x

        if not topdown:
            yield path, dirs, nondirs


    def chmod(self, path: PurePosixPath, mode: int) -> None:
        inode_id = self._resolve_path(path)

        if not inode_id:
            raise Exception(f"No such file or directory: {path}")

        inode = self._read_inode(inode_id)
        inode.mode = (inode.mode & ~0xFF) | (mode & 0xFF)
        inode.update_modified_time(False)
        self._write_inode(inode, inode_id)

    def open(self, path: PurePosixPath, mode: str) -> EmuFileIO:
        return EmuFileIO(self, path, mode)

    def close(self) -> None:
        self._closed = True
        self._tmp.cleanup()

    def _read_inode(self, inode_id: str) -> Inode:
        path = self._get_physical_path(inode_id)
        return Inode.from_bytes(path.read_bytes())
    
    def _write_inode(self, inode: Inode, inode_id: str) -> None:
        path = self._get_physical_path(inode_id)
        path.write_bytes(inode.to_bytes())

    def _get_dir_entries(self, inode_id: str) -> dict[str, str]:
        inode = self._read_inode(inode_id)
        assert(inode.is_dir())
        return loads(self._get_physical_path(inode.data_id).read_bytes())

    def _add_dir_entry(self, dir_inode_id: str, entry_name: str, entry_inode_id: str) -> None:
        inode = self._read_inode(dir_inode_id)
        assert(inode.is_dir())
        data_path = self._get_physical_path(inode.data_id)
        entries = loads(self._get_physical_path(inode.data_id).read_bytes())
        entries[entry_name] = entry_inode_id
        data_path.write_bytes(dumps(entries).encode("ascii"))

    def _remove_dir_entry(self, dir_inode_id: str, entry_name: str) -> None:
        inode = self._read_inode(dir_inode_id)
        assert(inode.is_dir())
        data_path = self._get_physical_path(inode.data_id)
        entries = loads(self._get_physical_path(inode.data_id).read_bytes())
        del entries[entry_name]
        data_path.write_bytes(dumps(entries).encode("ascii"))

    def _get_physical_path(self, inode_id: str) -> Path:
        return self._fs_path / b64encode(inode_id.encode("ascii")).decode("ascii")

    def _resolve_path(self, path: PurePosixPath) -> str | None:
        path = PurePosixPath("/") / path
        path = path.relative_to("/")
        inode_id = _ROOT_INODE_ID
        entries = self._get_dir_entries(inode_id)
        for part in path.parts[:-1]:
            if not part in entries:
                return None
            inode_id = entries[part]
            entries = self._get_dir_entries(inode_id)

        if len(path.name) == 0:
            return _ROOT_INODE_ID

        if not path.name in entries:
            return None

        return entries[path.name]


    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_) -> None:
        self.close()


def open(file: Path) -> EmuFS:
    tmp = TemporaryDirectory()
    with ZipFile(file) as zip:
        zip.extractall(tmp.name)
    return EmuFS(tmp, Path(tmp.name))

