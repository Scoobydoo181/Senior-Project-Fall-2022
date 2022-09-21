from enum import Enum
import numpy as np
from scipy.interpolate import LinearNDInterpolator
from typing import List, Tuple
class InterpolationType(Enum):
    LINEAR = 1
    RBF_LINEAR = 2

def unpackEyeCoords(eyeCoords: List[List[Tuple]]) -> List[Tuple]:
    # unpacks [[(1,2),(3,4)], [(5,6), (7,8)]] to [(1,2,3,4), (5,6,7,8)]
    return [sum(tupList,()) for tupList in eyeCoords]

def unpackScreenCoords(screenCoords):
    screenXCoords, screenYCoords = zip(*screenCoords)
    return (list(screenXCoords), list(screenYCoords))

class LinearInterpolator():
    def __init__(self, eyeCoords: List[Tuple], screenXCoords: List, screenYCoords: List):
        self.xInterpolator = LinearNDInterpolator(eyeCoords, screenXCoords)
        self.yInterpolator = LinearNDInterpolator(eyeCoords, screenYCoords)
    def computeScreenCoords(self, eyeCoords):
        return (self.xInterpolator(eyeCoords), self.yInterpolator(eyeCoords))

class RBFInterpolator():
    # def __init__(self, eyeCoords: List[Tuple], screenXCoords: List, screenYCoords: List, kernel=None, smoothing=None):
    #     self.kernel = kernel
    #     self.smoothing = smoothing
    #     self.rbf = RBFInterpolator()
    pass

class Interpolator():
    def __init(self):
        self.interpolator = None

    def calibrateInterpolator(self, eyeCoords: List[List[Tuple]], screenCoords: List[Tuple], interpType = InterpolationType.LINEAR):
        # eyeCoords of shape [[(x1.1,y1.1),(x1.2,y1.2)], [(x2.1,y2.1, x2.2, y2.2)], etc.]
        # screenCoords of shape [(x1,y1), (x2,y2), (x3,y3), etc]
        if interpType == InterpolationType.LINEAR:
            unpackedEyeCoords = unpackEyeCoords(eyeCoords)
            unpackedXScreenCoords, unpackedYScreenCoords = unpackScreenCoords(screenCoords)
            self.interpolator = LinearInterpolator(unpackedEyeCoords, unpackedXScreenCoords, unpackedYScreenCoords)
        return
    
    def computeScreenCoords(self, eyeCoords) -> Tuple:
        # eyeCoords of shape [x1,y1,x2,y2]
        unpackedEyeCoords = unpackEyeCoords(eyeCoords)
        if self.interpolator is None:
            raise ValueError('Interpolator not calibrated yet.') # TODO: create exception class to be more accurate? not sure
        return self.interpolator.computeScreenCoords(unpackedEyeCoords)

def computeScreenCoords(eyeCoords):
    pass



if __name__ == "__main__":
    pass