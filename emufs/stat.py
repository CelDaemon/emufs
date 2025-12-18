from typing import Type, TypeVar
from dataclasses import dataclass
from .inode import Inode, TYPE_DIR, TYPE_FILE

T = TypeVar("T", bound="Stat")

@dataclass
class Stat:
    ino: str
    mode: int
    size: int
    atime: float
    mtime: float
    ctime: float

    @classmethod
    def from_inode(cls: Type[T], inode_id: str, inode: Inode) -> T:
        return cls(inode_id, inode.mode, inode.size, inode.atime, inode.mtime, inode.ctime)


    def is_dir(self) -> bool:
        return (self.mode & 0xF000) == TYPE_DIR


    def is_file(self) -> bool:
        return (self.mode & 0xF000) == TYPE_FILE
