from dataclasses import dataclass
from typing import Type, TypeVar
from time import time
import struct

_NODE_FORMAT = "<IH3d"
_NODE_FORMAT_SIZE = struct.calcsize(_NODE_FORMAT)

TYPE_DIR = 0x4000
TYPE_FILE = 0x8000

def _get_now():
    return time() * 1000

T = TypeVar("T", bound="Inode")

@dataclass
class Inode:
    data_id: str
    size: int
    mode: int
    atime: float
    mtime: float
    ctime: float

    @classmethod
    def from_bytes(cls: Type[T], data: bytes) -> T:
        [size, mode, atime, mtime, ctime] = struct.unpack(_NODE_FORMAT, data[:_NODE_FORMAT_SIZE])

        return cls(data[_NODE_FORMAT_SIZE:].decode("ascii"),
                   size,
                   mode,
                   atime,
                   mtime,
                   ctime
                )

    @classmethod
    def new_empty(cls: Type[T], data_id: str, size: int, mode: int) -> T:
        now = _get_now()
        return cls(data_id, size, mode, now, now, now)

    def to_bytes(self) -> bytes:
        data_bytes = struct.pack(_NODE_FORMAT, self.size, 
                                 self.mode, self.atime, self.mtime, self.ctime)
        id_bytes = self.data_id.encode("ascii")
        return data_bytes + id_bytes

    def update_modified_time(self, file_data: bool) -> None:
        now = _get_now()
        if file_data:
            self.mtime = now
        self.ctime = now

    def update_accessed_time(self) -> None:
        now = _get_now()
        self.atime = now

    def is_dir(self) -> bool:
        return (self.mode & 0xF000) == TYPE_DIR


    def is_file(self) -> bool:
        return (self.mode & 0xF000) == TYPE_FILE

