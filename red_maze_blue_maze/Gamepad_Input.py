import sys
import Config as C
from mathutils import Vector

os = sys.platform[0:3]

gamepad = bge.logic.joysticks[0]

joystickThreshold = C.joystickTreshold

triggerThreshold = C.

def LSinput():
   if os == 'win' or os == 'dar' or os == 'lin':
        if abs(gamepad.axisValues[1]) > joystickThreshold:
            axisY = gamepad.axisValues[1]
        else: 
            axisY = 0
        if abs(gamepad.axisValues[0]) > joystickThreshold:
            axisX = gamepad.axisValues[0]
        else:
            axisX = 0
	
	return Vector(axisX, axisY)
	
		
def RSinput():
   if os == 'win' or os =='lin':
        if abs(gamepad.axisValues[3]) > joystickThreshold:
            axisY = gamepad.axisValues[3]
        else: 
            axisY = 0
        if abs(gamepad.axisValues[4]) > joystickThreshold:
            axisX = gamepad.axisValues[4]
        else:
            axisX = 0
	
	elif os == 'dar':
		if abs(gamepad.axisValues[3]) > joystickThreshold:
            axisY = gamepad.axisValues[3]
        else: 
            axisY = 0
        if abs(gamepad.axisValues[2]) > joystickThreshold:
            axisX = gamepad.axisValues[2]
        else:
            axisX = 0
	
	return Vector(axisX, axisY)
		
def buttonA():
	if os == 'win':
		if 0 in gamepad.activeButtons:
            return True
        else:
            return False
	elif os == 'dar':
		if 11 in gamepad.activeButtons:
			return True
		else:
			return False
			
def buttonB():
	if os == 'win':
		if 1 in gamepad.activeButtons:
            return True
        else:
            return False
	elif os == 'dar':
		if 12 in gamepad.activeButtons:
			return True
		else:
			return False
			
def buttonX():
	if os == 'win' or os == 'lin':
		if 2 in gamepad.activeButtons:
            return True
        else:
            return False
	elif os == 'dar':
		if 13 in gamepad.activeButtons:
			return True
		else:
			return False
		
def buttonY():
	if os == 'win':
		if 3 in gamepad.activeButtons:
            return True
        else:
            return False
	elif os == 'dar':
		if 14 in gamepad.activeButtons:
			return True
		else:
			return False