from enum import Enum
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
import pandas as pd 
from scipy.interpolate import LinearNDInterpolator
import os
import pickle
import math
from ui import CALIBRATION_FILE_NAME
class InterpolationType(Enum):
    LINEAR = 1
    RBF_LINEAR = 2
    LINEAR_REGRESSION = 3
    LOGISTIC_REGRESSION = 4

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
    df3 = pd.concat([df1,df2], axis =1)
    df3.dropna(inplace=True)
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

class LogisticRegressionInterpolator():
    def __init__(self, eyeCoords: list[list[tuple]], screenCoords: list[tuple]):
        df_X, df_Y = toCalibrationDataframes(eyeCoords, screenCoords)
        self.model = LogisticRegression()
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

class TangentLinearRegressionInterpolator():
    def __init__(self, eyeCoords: list[list[tuple]], screenCoords: list[tuple]):
        df_X, df_Y = toCalibrationDataframes(eyeCoords, screenCoords)
        # X_coords = pd.concat([df_X.iloc[:, 0], df_X.iloc[:,2]])
        # Y_coords = pd.concat([df_X.iloc[:,1], df_X.iloc[:, 3]])
        # df_screen_x = pd.concat([df_Y.iloc[:,0], df_Y.iloc[:,0]])
        # df_screen_y = pd.concat([df_Y.iloc[:,1],df_Y.iloc[:,1]])
        X_pupil_left = df_X.iloc[:,0]
        X_pupil_right = df_X.iloc[:,2]
        Y_pupil_left = df_X.iloc[:,1]
        Y_pupil_right = df_X.iloc[:,3]
        X_screen_coords = df_Y.iloc[:,0]
        Y_screen_coords = df_Y.iloc[:,1]
        # small angle approx --> tan(theta) ≈ theta. In our case, theta is distance offset in camera frame for each pupil
        x_pupil_left_theta = X_pupil_left - X_pupil_left.iat[4]
        x_pupil_right_theta = X_pupil_right - X_pupil_right.iat[4]
        X_screen_coords_diff = X_screen_coords - X_screen_coords.iat[4]
        # distance to screen *  tan(theta) = screen offset (distance from center per calibration point)
        # 
        self.model = LinearRegression()
        self.model.fit(df_X, df_Y)
    def computeScreenCoords(self, eyeCoords):
        df_X = pd.DataFrame(sum(eyeCoords, ()))
        prediction = self.model.predict(df_X.T)
        return prediction[-1]

