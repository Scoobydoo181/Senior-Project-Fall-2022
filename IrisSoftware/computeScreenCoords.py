from enum import Enum
import numpy as np
from sklearn.linear_model import LinearRegression
import pandas as pd 
from scipy.interpolate import LinearNDInterpolator
import os
import pickle
from ui import CALIBRATION_FILE_NAME
class InterpolationType(Enum):
    LINEAR = 1
    RBF_LINEAR = 2
    LINEAR_REGRESSION = 3
    

def unpackEyeCoords(eyeCoords: list[list[tuple]]) -> list[tuple]:
    # unpacks [[(1,2),(3,4)], [(5,6), (7,8)]] to [(1,2,3,4), (5,6,7,8)]
    return [sum(tupList,()) for tupList in eyeCoords]

def unpackScreenCoords(screenCoords):
    screenXCoords, screenYCoords = zip(*screenCoords)
    return (list(screenXCoords), list(screenYCoords))

def toCalibrationDataframes(eyeCoords: list[list[tuple]], screenCoords: list[tuple]):
    unpackedEyes = unpackEyeCoords(eyeCoords)
    df1 =pd.DataFrame(unpackedEyes)
    df2 =pd.DataFrame(screenCoords)
    df3 = pd.concat([df1,df2])
    X = df3.iloc[:, 0:4]
    Y = df3.iloc[:, -2:]
    return X,Y
class LinearRegressionInterpolator():
    def __init__(self, eyeCoords: list[list[tuple]], screenCoords: list[tuple]):
        df_X, df_Y = toCalibrationDataframes(eyeCoords, screenCoords)
        self.model = LinearRegression()
        self.model.fit(df_X, df_Y)
    def computeScreenCoords(self, eyeCoords):
        df_X = pd.DataFrame(sum(eyeCoords, ()))
        prediction = self.model.predict(df_X.T)
        return prediction[-1]

        
class LinearInterpolator():
    def __init__(self, eyeCoords: list[tuple], screenXCoords: list, screenYCoords: list):
        self.xInterpolator = LinearNDInterpolator(eyeCoords, screenXCoords)
        self.yInterpolator = LinearNDInterpolator(eyeCoords, screenYCoords)
    def computeScreenCoords(self, eyeCoords):
        return (self.xInterpolator(eyeCoords), self.yInterpolator(eyeCoords))

class Interpolator():
    def __init__(self):
        self.interpolator = None

    def calibrateInterpolatorManual(self, eyeCoords: list[list[tuple]], screenCoords: list[tuple], interpType = InterpolationType.LINEAR_REGRESSION):
        # eyeCoords of shape [[(x1.1,y1.1),(x1.2,y1.2)], [(x2.1,y2.1, x2.2, y2.2)], etc.]
        # screenCoords of shape [(x1,y1), (x2,y2), (x3,y3), etc]
        if interpType == InterpolationType.LINEAR:
            unpackedEyeCoords = unpackEyeCoords(eyeCoords)
            unpackedXScreenCoords, unpackedYScreenCoords = unpackScreenCoords(screenCoords)
            self.interpolator = LinearInterpolator(unpackedEyeCoords, unpackedXScreenCoords, unpackedYScreenCoords)
        elif interpType == InterpolationType.LINEAR_REGRESSION:
            self.interpolator = LinearRegressionInterpolator(eyeCoords, screenCoords)
        elif interpType == InterpolationType.LOGISTIC_REGRESSION:
            self.interpolator = LinearRegressionInterpolator(eyeCoords, screenCoords)
        return
    def calibrateInterpolator(self, calibration_file = CALIBRATION_FILE_NAME, interpType = InterpolationType.LINEAR_REGRESSION):
        if not os.path.exists(calibration_file):
            raise ValueError('Error when calibrating interpolator')

        with open(calibration_file, 'rb') as calibration_data:
            calibrationData = pickle.load(calibration_data)
        self.calibrateInterpolatorManual(calibrationData['eyeCoords'], calibrationData['calibrationCircleLocations'], interpType)


    
    def computeScreenCoords(self, eyeCoords: list[tuple]) -> tuple:
        # eyeCoords of shape [x1,y1,x2,y2]
        # unpackedEyeCoords = unpackEyeCoords(eyeCoords)
        # print(unpackedEyeCoords)
        if self.interpolator is None:
            raise ValueError('Error calibrating interpolator.')
        return self.interpolator.computeScreenCoords(eyeCoords)
