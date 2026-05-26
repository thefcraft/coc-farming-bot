from typing import Protocol
from numpy.typing import NDArray
import numpy as np
from PIL.Image import Image as ImagePil


type ImageCv2 = NDArray[np.uint8]


class HasRead[T](Protocol):
    def read(self, size: int | None = -1, /) -> T: ...

class PointLike(Protocol):
    x: int
    y: int

class RegionLike(Protocol):
    x: int
    y: int
    w: int
    h: int



__all__ = [
    "ImageCv2",
    "ImagePil",
    "HasRead",
]
