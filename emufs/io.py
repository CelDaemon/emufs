from typing import IO, Any, Self, TypeVar, TYPE_CHECKING
from pathlib import PurePosixPath
from io import RawIOBase, SEEK_END, SEEK_SET
from uuid import uuid4
from collections.abc import Buffer
from .inode import Inode, TYPE_FILE

if TYPE_CHECKING:
    from .fs import EmuFS


T = TypeVar("T", bound="EmuFileIO")

class EmuFileIO(RawIOBase):
    _fs: "EmuFS"
    _closed: bool
    _inode_id: str
    _inner: IO[Any]

    def __init__(self, fs: "EmuFS", path: PurePosixPath, mode: str = "r"):
        exclusive = "x" in mode
        creatable = ("x" in mode) | ("w" in mode) | ("a" in mode)

        inode_id = fs._resolve_path(path)

        if exclusive and inode_id:
            raise Exception(f"Already exists: {path}")

        if not inode_id:
            if not creatable:
                raise Exception(f"No such file: {path}")

            parent_inode_id = fs._resolve_path(path.parent)
            if not parent_inode_id:
                raise Exception(f"No such directory: {path.parent}")

            inode_id = str(uuid4())
            data_id = str(uuid4())
            inode = Inode.new_empty(data_id, 0, TYPE_FILE | 0o644)

            fs._write_inode(inode, inode_id)
            fs._add_dir_entry(parent_inode_id, path.name, inode_id)

        inode = fs._read_inode(inode_id)

        self._fs = fs
        self._closed = False
        self._inode_id = inode_id
        self._inner = open(self._fs._get_physical_path(inode.data_id), mode)

    def write(self, data: Any):
        self._inner.write(data)

        inode = self._fs._read_inode(self._inode_id)
        inode.update_modified_time(True)
        previous_cursor = self._inner.tell()
        self._inner.seek(0, SEEK_END)
        inode.size = self._inner.tell()
        self._inner.seek(previous_cursor, SEEK_SET)
        self._fs._write_inode(inode, self._inode_id)

    def read(self, size: int = -1) -> bytes:
        inode = self._fs._read_inode(self._inode_id)

        inode.update_accessed_time()

        self._fs._write_inode(inode, self._inode_id)

        return self._inner.read(size)


    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_) -> None:
        self._closed = True
        self._inner.close()

