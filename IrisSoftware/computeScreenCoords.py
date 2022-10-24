from enum import Enum
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
import sklearn
import pandas as pd 
from scipy.interpolate import LinearNDInterpolator
import os
import pickle
import matplotlib.pyplot as plt
from statistics import mean
from ui import CALIBRATION_FILE_NAME
class InterpolationType(Enum):
    LINEAR = 1
    RBF_LINEAR = 2
    LINEAR_REGRESSION = 3
    LOGISTIC_REGRESSION = 4
    JOYSTICK = 5

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

class JoystickInterpolator():
    def __init__(self, calibrationData):
        leftEyeXData = []
        leftEyeYData = []
        rightEyeXData = []
        rightEyeYData = []

        screenXData = []
        screenYData = []

        for ([(leftEyeX, leftEyeY), (rightEyeX, rightEyeY)], (screenX, screenY)) in calibrationData:
            if leftEyeX and leftEyeY and rightEyeX and rightEyeY and screenX and screenY:
                leftEyeXData.append(leftEyeX)
                leftEyeYData.append(leftEyeY)
                rightEyeXData.append(rightEyeX)
                rightEyeYData.append(rightEyeY)
                screenXData.append(screenX)
                screenYData.append(screenY)

        self.leftYMin = mean(sorted(leftEyeYData)[:3])
        self.rightYMin = mean(sorted(rightEyeYData)[:3])

        self.leftXMin = mean(sorted(leftEyeXData)[:3])
        self.rightXMin = mean(sorted(rightEyeXData)[:3])

        self.leftYMax = mean(sorted(leftEyeYData)[-3:])
        self.rightYMax = mean(sorted(rightEyeYData)[-3:])

        self.leftXMax = mean(sorted(leftEyeXData)[-3:])
        self.rightXMax = mean(sorted(rightEyeXData)[-3:])

        self.screenXMax = mean(sorted(screenXData)[-3:])
        self.screenYMax = mean(sorted(screenYData)[-3:])

    def computeScreenCoords(self, eyeCoords):
        leftEyeX, leftEyeY = eyeCoords[0]
        rightEyeX, rightEyeY = eyeCoords[1]

        if leftEyeX < self.leftXMin and rightEyeX < self.rightXMin:
            # print('Moving right')
            return self.screenXMax, self.screenYMax / 2
        elif leftEyeX > self.leftXMax and rightEyeX > self.rightXMax:
            # print('Moving left')
            return (0, self.screenYMax / 2)

        if leftEyeY < self.leftYMin and rightEyeY < self.rightYMin:
            # print('Moving up')
            return self.screenXMax / 2, 0
        elif leftEyeY > self.leftYMax and rightEyeY > self.rightYMax:
            # print('Moving down')
            return self.screenXMax / 2, self.screenYMax

    # what if both at same time? Make nested

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
        elif interpType == InterpolationType.JOYSTICK:
            self.interpolator = JoystickInterpolator(zip(eyeCoords, screenCoords))


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

if __name__ == '__main__':
    leftEyeXData = []
    leftEyeYData = []
    rightEyeXData = []
    rightEyeYData = []

    screenXData = []
    screenYData = []
    
    with open(CALIBRATION_FILE_NAME, 'rb') as calibration_data:
        calibrationData = pickle.load(calibration_data)       
            
        for val in zip(calibrationData['eyeCoords'], calibrationData['calibrationCircleLocations']):
            ([(leftEyeX, leftEyeY), (rightEyeX, rightEyeY)], (screenX, screenY)) = val
            print(val)
            if leftEyeX and leftEyeY and rightEyeX and rightEyeY and screenX and screenY:
                leftEyeXData.append(leftEyeX)
                leftEyeYData.append(leftEyeY)
                rightEyeXData.append(rightEyeX)
                rightEyeYData.append(rightEyeY)
                screenXData.append(screenX)
                screenYData.append(screenY)

    plt.scatter(rightEyeYData, screenYData)
    plt.title('Eye coordinate vs Screen coordinate')
    plt.xlabel('Eye Y coordinate')
    plt.ylabel('Screen Y coordinate')
    plt.show()
