﻿# servo_controller_modify2
# modified by robertchoi

import sys
sys.path.append("..")

import Kinematics.kinematics as kn
import numpy as np

from adafruit_pca9685 import PCA9685
from adafruit_motor import servo
import board
import busio
import time
import copy

class Controllers:
    def __init__(self):

        print("Initializing Servos")
        self._i2c_bus0=(busio.I2C(board.SCL_1, board.SDA_1))
        print("Initializing ServoKit")
        self._pca_1 = PCA9685(self._i2c_bus0, address=0x40)
        self._pca_1.frequency = 60
        self._pca_2 = PCA9685(self._i2c_bus0, address=0x41)
        self._pca_2.frequency = 60
        self._servos = list()
        for i in range(0, 12):
            if i<6:
                self._servos.append(servo.Servo(self._pca_1.channels[i], min_pulse=771, max_pulse=2740))
            else:
                self._servos.append(servo.Servo(self._pca_2.channels[i], min_pulse=771, max_pulse=2740))

        # servos.append(servo.Servo(pca[int(i/6)].channels[int(i%6)], min_pulse=460, max_pulse=2440)) CL motor
        # servos.append(servo.Servo(pca[int(i/6)].channels[int(i%6)], min_pulse=771, max_pulse=2740)) MG996R
        print("Done initializing")

        #1 by 12 array
        self.MOTOR_LEG_FRONT = 0
        self.MOTOR_LEG_BACK = 0
        self.MOTOR_LEG_LEFT = 0 
        self.MOTOR_LEG_RIGHT = 0
        self.MOTOR_LEG_SHOULDER =0
        self.MOTOR_LEG_UPPER = 0
        self.MOTOR_LEG_LOWER = 0

        #4 by 3 matrix
        self.SIM_LEG_FRONT = 0
        self.SIM_LEG_BACK =6
        self.SIM_LEG_LEFT = 0
        self.SIM_LEG_RIGHT = 1
        self.SIM_LEG_THETA1 = 0
        self.SIM_LEG_THETA2 = 1
        self.SIM_LEG_THETA3 = 2

        # [0]~[2] : 왼쪽 앞 다리 // [3]~[5] : 오른쪽 앞 다리 // [6]~[8] : 왼쪽 뒷 다리 // [9]~[11] : 오른쪽 뒷 다리
        # centered position perpendicular to the ground
        self._servo_offsets = [180, 90, 90, 1, 90, 90, 180, 90, 90, 1, 90, 90]
        self._val_list = np.zeros(12) #[ x for x in range(12) ] 

        # All Angles for Leg 3 * 4 = 12 length
        self._thetas = []

    def getDegreeAngles(self, La):
        # radian to degree
        Lp_cp = copy.deepcopy(La)
        Lp_cp *= 180/np.pi
        Lp_cp = [ [ int(x) for x in y ] for y in Lp_cp ]

        self._thetas = Lp_cp
        print(f'self._thetas : {self._thetas}')

    # Angle mapping from radian to servo angles
    def angleToServo(self, La):
        self.getDegreeAngles(La)

        #FL Lower
        self._val_list[0] = self._servo_offsets[0] - self._thetas[0][2]
        #FL Upper
        self._val_list[1] = self._servo_offsets[1] - self._thetas[0][1]    
        #FL Shoulder
        self._val_list[2] = self._servo_offsets[2] + self._thetas[0][0]

        #FR Lower
        self._val_list[3] = self._servo_offsets[3] + self._thetas[1][2]
        #FR Upper
        self._val_list[4] = self._servo_offsets[4] + self._thetas[1][1]    
        #FR Shoulder
        self._val_list[5] = self._servo_offsets[5] - self._thetas[1][0]

        #BL Lower
        self._val_list[6] = self._servo_offsets[6] - self._thetas[2][2]
        #BL Upper
        self._val_list[7] = self._servo_offsets[7] - self._thetas[2][1]    
        #BL Shoulder, Formula flipped from the front
        self._val_list[8] = self._servo_offsets[8] - self._thetas[2][0]

        #BR Lower. 
        self._val_list[9] = self._servo_offsets[9] + self._thetas[3][2]
        #BR Upper
        self._val_list[10] = self._servo_offsets[10] + self._thetas[3][1]    
        #BR Shoulder, Formula flipped from the front
        self._val_list[11] = self._servo_offsets[11] + self._thetas[3][0]     

    def getServoAngles(self):
        return self._val_list

    def servoRotate(self, thetas):
        self.angleToServo(thetas)

        for x in range(len(self._val_list)):
            
            if x>=0 and x<12:
                # self._val_list[x] = (self._val_list[x]-26.36)*(1980/1500)
                #print(self._val_list[x], end=' ')
                #if x%3 == 2: print()
                # print(self._val_list[x])

                if (self._val_list[x] > 180):
                    print("Over 180!!")
                    self._val_list[x] = 179
                    raise Exception(f"[Error] Motor {x} Over 180!!")
                    continue
                if (self._val_list[x] <= 0):
                    print("Under 0!!")
                    self._val_list[x] = 1
                    raise Exception(f"[Error] Motor {x} Under 0!!")
                    continue
                if x < 6:
                    self._servos[x].angle = self._val_list[x]
                else:
                    self._servos[x].angle = self._val_list[x]


def input_handle(controller, thetas):
    num=int(input("Enter Servo to rotate (0-11): "))        
    angle=int(input("Enter new angles (0-180): "))
    print(f'Servo {num} will be set to {angle}\n')

    if(num > 11):
        print("[Error] Num should be smaller than 12")
        input_handle(controller, thetas)    

    controller._servo_offsets[num] = angle
    print(controller._servo_offsets)

    try:
        controller.servoRotate(thetas)
    except Exception as e:
        print(e)
        input_handle(controller, thetas)
    finally:
        # Get AngleValues for Debugging
        svAngle = controller.getServoAngles()
        print(f'Current Servo angle : {svAngle}')

if __name__=="__main__":
    legEndpoints=np.array([[100,-100,87.5,1],[100,-100,-87.5,1],[-100,-100,87.5,1],[-100,-100,-87.5,1]])
    thetas = kn.initIK(legEndpoints) #radians
    
    controller = Controllers()

    # Get radian thetas, transform to integer servo angles
    # then, rotate servos

    kn.plotKinematics()
    
    while True:
        input_handle(controller, thetas)


