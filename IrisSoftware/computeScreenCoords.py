from enum import Enum
import numpy as np
from sklearn.linear_model import LinearRegression
import pandas as pd 
from scipy.interpolate import LinearNDInterpolator
from typing import List, Tuple
import os
import pickle
from ui import CALIBRATION_FILE_NAME

class InterpolationType(Enum):
    LINEAR = 1
    RBF_LINEAR = 2
    LINEAR_REGRESSION = 3

def unpackEyeCoords(eyeCoords: List[List[Tuple]]) -> List[Tuple]:
    # unpacks [[(1,2),(3,4)], [(5,6), (7,8)]] to [(1,2,3,4), (5,6,7,8)]
    return [sum(tupList,()) for tupList in eyeCoords]

def unpackScreenCoords(screenCoords):
    screenXCoords, screenYCoords = zip(*screenCoords)
    return (list(screenXCoords), list(screenYCoords))

class LinearRegressionInterpolator():
    def __init__(self, eyeCoords: List[Tuple], screenXCoords: List, screenYCoords: List):
        df_X = pd.DataFrame(eyeCoords)
        # TODO: restructure to perform unpacking in models instead of beforehand to account for differences in implementations
        df_Y = pd.DataFrame(zip(screenXCoords, screenYCoords))
        self.model = LinearRegression()
        self.model.fit(df_X, df_Y)
    def computeScreenCoords(self, eyeCoords):
        df_X = pd.DataFrame(eyeCoords)
        prediction = self.model.predict(df_X)
        return prediction.tolist()[-1]
        
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
    def __init__(self):
        self.interpolator = None

    def calibrateInterpolatorManual(self, eyeCoords: List[List[Tuple]], screenCoords: List[Tuple], interpType = InterpolationType.LINEAR_REGRESSION):
        # eyeCoords of shape [[(x1.1,y1.1),(x1.2,y1.2)], [(x2.1,y2.1, x2.2, y2.2)], etc.]
        # screenCoords of shape [(x1,y1), (x2,y2), (x3,y3), etc]
        if interpType == InterpolationType.LINEAR:
            unpackedEyeCoords = unpackEyeCoords(eyeCoords)
            unpackedXScreenCoords, unpackedYScreenCoords = unpackScreenCoords(screenCoords)
            self.interpolator = LinearInterpolator(unpackedEyeCoords, unpackedXScreenCoords, unpackedYScreenCoords)
        elif interpType == InterpolationType.LINEAR_REGRESSION:
            unpackedEyeCoords = unpackEyeCoords(eyeCoords)
            unpackedXScreenCoords, unpackedYScreenCoords = unpackScreenCoords(screenCoords)
            self.interpolator = LinearRegressionInterpolator(unpackedEyeCoords, unpackedXScreenCoords, unpackedYScreenCoords)
        return
    
    def calibrateInterpolator(self, calibration_file = CALIBRATION_FILE_NAME, interpType = InterpolationType.LINEAR_REGRESSION):
        if not os.path.exists(calibration_file):
            raise ValueError('Error when calibrating interpolator')

        with open(calibration_file, 'rb') as calibration_data:
            calibrationData = pickle.load(calibration_data)
        self.calibrateInterpolatorManual(calibrationData['eyeCoords'], calibrationData['calibrationCircleLocations'], interpType)

    def computeScreenCoords(self, eyeCoords) -> Tuple:
        unpackedEyeCoords = unpackEyeCoords(eyeCoords)
        if self.interpolator is None:
            raise ValueError('Error when calibrating interpolator') # TODO: create exception class to be more accurate? not sure
        return self.interpolator.computeScreenCoords(unpackedEyeCoords)