from enum import Enum
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
import sklearn
import pandas as pd 
from scipy.interpolate import LinearNDInterpolator
import os
import pickle
import math
import matplotlib.pyplot as plt
from statistics import mean
from ui import CALIBRATION_FILE_NAME

class InterpolationType(Enum):
    LINEAR = 1
    RBF_LINEAR = 2
    LINEAR_REGRESSION = 3
    LOGISTIC_REGRESSION = 4
    TANGENT_LINEAR_REGRESSION = 5
    JOYSTICK = 6

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

class TangentLinearRegressionInterpolator():
    def __init__(self, eyeCoords: list[list[tuple]], screenCoords: list[tuple]):
        df_X, df_Y = toCalibrationDataframes(eyeCoords, screenCoords)
  
        X_pupil_left = df_X.iloc[:,0]
        X_pupil_right = df_X.iloc[:,2]
        Y_pupil_left = df_X.iloc[:,1]
        Y_pupil_right = df_X.iloc[:,3]
        X_screen_coords = df_Y.iloc[:,0]
        Y_screen_coords = df_Y.iloc[:,1]
        # small angle approx --> tan(theta) ≈ theta. In our case, theta is distance offset in camera frame for each pupil
        X_pupil_left_theta = X_pupil_left - X_pupil_left.iat[4]
        X_pupil_right_theta = X_pupil_right - X_pupil_right.iat[4]
        X_screen_coords_diff = X_screen_coords - X_screen_coords.iat[4]
        X_screen_coords_diff = pd.concat([X_screen_coords_diff, X_screen_coords_diff]).values.reshape(-1,1)
        X_pupil_theta = pd.concat([X_pupil_left_theta, X_pupil_right_theta]).values.reshape(-1,1)

        Y_pupil_left_theta = Y_pupil_left - Y_pupil_left.iat[4]
        Y_pupil_right_theta = Y_pupil_right - Y_pupil_right.iat[4]
        Y_screen_coords_diff = Y_screen_coords - Y_screen_coords.iat[4]
        Y_screen_coords_diff = pd.concat([Y_screen_coords_diff, Y_screen_coords_diff]).values.reshape(-1,1)
        Y_pupil_theta = pd.concat([Y_pupil_left_theta, Y_pupil_right_theta]).values.reshape(-1,1)
        # distance to screen *  tan(theta) = screen offset (distance from center per calibration point)
        X_dist_model = LinearRegression()
        X_dist_model.fit(X_pupil_theta, X_screen_coords_diff)
        Y_dist_model = LinearRegression()
        Y_dist_model.fit(Y_pupil_theta, Y_screen_coords_diff)
        # take average of calculated distances per pupil tangent
        self.x_dist = X_dist_model.coef_[0][0]
        self.y_dist = Y_dist_model.coef_[0][0]
        self.avg_dist = np.average([X_dist_model.coef_, Y_dist_model.coef_])

        self.x_pupil_left_center = X_pupil_left.iat[4]
        self.x_pupil_right_center = X_pupil_right.iat[4]
        self.y_pupil_left_center = Y_pupil_left.iat[4]
        self.y_pupil_right_center = Y_pupil_right.iat[4]

        self.x_center_screen = X_screen_coords.iat[4]
        self.y_center_screen = Y_screen_coords.iat[4]

    def computeScreenCoords(self, eyeCoords):
        # x_screen = dist_to_screen * tan(x_camera - x_camera_center) + x_screen_center
        x_tan = math.avg(math.tan(eyeCoords[0][0] - self.x_pupil_left_center), math.tan(eyeCoords[1][0] - self.x_pupil_right_center))
        x_prediction = (self.x_dist * x_tan) + self.x_center_screen

        y_tan = math.avg(math.tan(eyeCoords[0][1] - self.y_pupil_left_center), math.tan(eyeCoords[1][1] - self.y_pupil_right_center))
        y_prediction = (self.y_dist * y_tan) + self.y_center_screen
        # prediction = self.model.predict(df_X.T)
        return(x_prediction, y_prediction)
        # return prediction[-1]
      
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
            print('Moving right')
            return self.screenXMax, self.screenYMax / 2
        elif leftEyeX > self.leftXMax and rightEyeX > self.rightXMax:
            print('Moving left')
            return (0, self.screenYMax / 2)

        if leftEyeY < self.leftYMin and rightEyeY < self.rightYMin:
            print('Moving up')
            return self.screenXMax / 2, 0
        elif leftEyeY > self.leftYMax and rightEyeY > self.rightYMax:
            print('Moving down')
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
            self.interpolator = LogisticRegressionInterpolator(eyeCoords, screenCoords)
        elif interpType == InterpolationType.TANGENT_LINEAR_REGRESSION:
            self.interpolator = TangentLinearRegressionInterpolator(eyeCoords, screenCoords)
        elif interpType == InterpolationType.JOYSTICK:
            self.interpolator = JoystickInterpolator(zip(eyeCoords, screenCoords))
            
    def calibrateInterpolator(self, calibration_file = CALIBRATION_FILE_NAME, interpType = InterpolationType.TANGENT_LINEAR_REGRESSION):
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
