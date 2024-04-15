from dataclasses import dataclass


@dataclass
class Box:
    left: int
    top: int
    right: int
    bottom: int

    def __iter__(self):
        return iter((self.left, self.top, self.right, self.bottom))

    def toPIL(self):
        return (self.left, self.top, self.right, self.bottom)


def boxFromFaceLocation(location):
    top, right, bottom, left = location
    return Box(left, top, right, bottom)
