#This module gathers all input for the player & camera controls

import bge
import math
import mathutils
import Config
import sys
logic = bge.logic
events = bge.events   
render = bge.render
Vector = mathutils.Vector

controlScheme = 'WASD/Mouse'

#This function takes two lists, 'a' and 'b', and returns true only if
#each element of 'a' is equal to any element WITHIN the corresponding element of 'b'
#So each element of 'a' can be compared with multiple values
#'a' will generally be an ordinary list, and 'b' will be a list containing lists and/or singular elements
#I use this function to speed up the process of checking what direction is being input
def isEqual(a,b):
    equal = True
    for i in range(len(a)):
        equal2 = False
        try:
            for x in b[i]:
                if x == a[i]:
                    equal2 = True
        except:
            if b[i] == a[i]:
                equal2 = True
        if equal2 == False:
            equal = False
    return equal
                
#If a key is currently pressed, its corresponding element in the logic.keyboard.events
#will be either 1 or 2. Otherwise, it'll be either 0 or 3. The keymask values (look way down in WASD/AKeys input)
#are taken straight from logic.keyboard.events, so they hold the same values. 
#I hold both possibilities for either situation in a list, for convenience
p = [1,2] #possible values if the key is pressed
d = [0,3] #not pressed    

def moveInput():  
    key = logic.keyboard.events
    mouse = logic.mouse.events
    global controlScheme
    
    if controlScheme == 'ArrowKeys/WASD':    
        inputVec = arrowKeysInput()
        if not (isEqual([key[events.ZKEY]],[p]) or isEqual([key[events.LEFTSHIFTKEY]],[p])):
            inputVec *= Config.WalkSpeed/Config.MaxSpeed
            
    elif controlScheme == 'WASD/Mouse':        
        inputVec = WASDInput() 
        if not isEqual([mouse[events.RIGHTMOUSE]],[p]):
            inputVec *= Config.WalkSpeed/Config.MaxSpeed
    
    elif controlScheme == 'Gamepad':
        try:
            return LSinput()
        except IndexError:
            raise Exception("Index Error raised while gathering gamepad input.\nReverting to WASD/Mouse control scheme")            
            controlScheme = 'WASD/Mouse'        
    else:
        raise Exception(controlScheme + " is not a valid control scheme")
    
    return inputVec

    
def jumpInput():
    
    key = logic.keyboard.events
    mouse = logic.mouse.events
    
    if controlScheme == 'ArrowKeys/WASD' and (key[events.XKEY] == 1 or key[events.SPACEKEY] == 1):
        jump = True
    elif controlScheme == 'WASD/Mouse' and mouse[events.LEFTMOUSE] == 1:
        jump = True
    elif controlScheme == 'Gamepad' and A_BUTTON == 1:
        jump = True
    else:
        jump = False
        
    return jump

def jumpIsHeldDown():

    key = logic.keyboard.events
    mouse = logic.mouse.events
    
    if controlScheme == 'ArrowKeys/WASD' and (isEqual([key[events.XKEY]],[p]) or isEqual([key[events.SPACEKEY]],[p])):
        jump = True
    elif controlScheme == 'WASD/Mouse' and isEqual([mouse[events.LEFTMOUSE]], [p]):
        jump = True
    elif controlScheme == 'Gamepad' and isEqual([A_BUTTON], [p]):
        jump = True
    else:
        jump = False
        
    return jump
 
def dropInput():
   
    key = logic.keyboard.events
    mouse = logic.mouse.events
    
    if controlScheme == 'ArrowKeys/WASD' and (key[events.ZKEY] == 1 or key[events.LEFTSHIFTKEY] == 1):
        drop = True
    elif controlScheme == 'WASD/Mouse' and mouse[events.RIGHTMOUSE] == 1:
        drop = True
    elif controlScheme == 'Gamepad' and B_BUTTON == 1:
        drop = True
    else:
        drop = False
        
    return drop

auto = True

def camInput():    
    global controlScheme
    key = logic.keyboard.events
    mouse = logic.mouse.events
    global auto         
    
    if controlScheme == 'ArrowKeys/WASD':
        if key[events.LEFTCTRLKEY] == 1:   
            auto = True
        inputVec = WASDInput()
        if inputVec.length > 0:
            auto = False
        
    elif controlScheme == 'WASD/Mouse':
        inputVec = mouseInput() 
        if mouse[events.MIDDLEMOUSE] == 1:
            auto = not auto
    elif controlScheme == 'Gamepad':
        try:
            inputVec = RSinput()
            if Y_BUTTON == 1:
                auto = not auto
        except IndexError:
            raise Exception("Index Error raised while gathering gamepad input.\nPlease use WASD/Mouse control scheme instead.")           
            controlScheme = 'WASD/Mouse'            
    else:
        raise Exception(controlScheme + " is not a valid control scheme")
        
    return [-inputVec, auto]



def WASDInput():      
    
    keymask =[0,0,0,0]
    
    key = logic.keyboard.events
    keymask[0] = key[events.AKEY]
    keymask[1] = key[events.WKEY]
    keymask[2] = key[events.DKEY]
    keymask[3] = key[events.SKEY]
                
    p = [1,2]
    d = [0,3]
    
    inputVec = mathutils.Vector([0,0])   
    
    #Primary directions
    if isEqual(keymask, [p,d,d,d]):
        inputVec = mathutils.Vector([-1,0])
    if isEqual(keymask, [d,p,d,d]):
        inputVec = mathutils.Vector([0,1])
    if isEqual(keymask, [d,d,p,d]):
        inputVec = mathutils.Vector([1,0])
    if isEqual(keymask, [d,d,d,p]):
        inputVec = mathutils.Vector([0,-1])
         
    #Diagonal directions
    SR2 = 0.5 * math.sqrt(2.0)
    
    if isEqual(keymask, [p,p,d,d]):
        inputVec = mathutils.Vector([-SR2,SR2])
    if isEqual(keymask, [d,p,p,d]):
        inputVec = mathutils.Vector([SR2,SR2])
    if isEqual(keymask, [d,d,p,p]):
        inputVec = mathutils.Vector([SR2,-SR2])
    if isEqual(keymask, [p,d,d,p]):
        inputVec = mathutils.Vector([-SR2,-SR2])
    
    return inputVec


oldMouseVec = None
mouseSensitivity = Config.mouseSensitivity
mouseSmooth = Config.mouseSmooth

def mouseInput():    
    
    cont = logic.getCurrentController()
    owner = cont.owner 
    
    centerX = (render.getWindowWidth()//2)/render.getWindowWidth()
    centerY = (render.getWindowHeight()//2)/render.getWindowHeight()
    
    global oldMouseVec
    if oldMouseVec == None:
        oldMouseVec = mathutils.Vector([0.0,0.0])
        logic.mouse.position = (centerX,centerY)
        return mathutils.Vector([0,0])
            
    x = logic.mouse.position[0] - centerX
    if abs(x) < abs(2/render.getWindowWidth()): x = 0
    y = centerY - logic.mouse.position[1]
    if abs(y) < abs(2/render.getWindowWidth()): y = 0
    newMouseVec = mathutils.Vector([x, y])  
    
    global mouseSensitivity 
    
    newMouseVec *= mouseSensitivity
    
    # Smooth movement
    global mouseSmooth
    
    oldMouseVec = oldMouseVec*mouseSmooth + newMouseVec*(1.0-mouseSmooth)
    newMouseVec = oldMouseVec
    
    # Center mouse in game window
    logic.mouse.position = (centerX,centerY)    
    
    return mathutils.Vector(newMouseVec)

def arrowKeysInput():
    keymask =[0,0,0,0]
    
    key = logic.keyboard.events
    keymask[0] = key[events.LEFTARROWKEY]
    keymask[1] = key[events.UPARROWKEY]
    keymask[2] = key[events.RIGHTARROWKEY]
    keymask[3] = key[events.DOWNARROWKEY]    
    
    inputVec = mathutils.Vector([0,0])   
    
    #Primary directions
    if isEqual(keymask, [p,d,d,d]):    #If left is pressed, and no others are...
        inputVec = mathutils.Vector([-1,0])        
    if isEqual(keymask, [d,p,d,d]):    #Up
        inputVec = mathutils.Vector([0,1])
    if isEqual(keymask, [d,d,p,d]):    #Right
        inputVec = mathutils.Vector([1,0])
    if isEqual(keymask, [d,d,d,p]):    #Down
        inputVec = mathutils.Vector([0,-1])
         
    #Diagonal directions
    SR2 = 0.5 * math.sqrt(2.0)
    
    if isEqual(keymask, [p,p,d,d]):    #Up-Left
        inputVec = mathutils.Vector([-SR2,SR2])
    if isEqual(keymask, [d,p,p,d]):    #etc
        inputVec = mathutils.Vector([SR2,SR2])
    if isEqual(keymask, [d,d,p,p]):
        inputVec = mathutils.Vector([SR2,-SR2])
    if isEqual(keymask, [p,d,d,p]):
        inputVec = mathutils.Vector([-SR2,-SR2])
    
    return inputVec

os = sys.platform[0:3]
gamepad = bge.logic.joysticks[0]
joystickThreshold = Config.joystickThreshold

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
    
    return Vector([axisX, -axisY])
    
        
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
    
    return Vector([axisX, -axisY])
 
D_PAD_UP = 0
D_PAD_DOWN = 0
D_PAD_RIGHT = 0
D_PAD_LEFT = 0
L_TRIGGER = 0
R_TRIGGER = 0
A_BUTTON = 0
B_BUTTON = 0
X_BUTTON = 0
Y_BUTTON = 0
L_BUMPER = 0
R_BUMPER = 0
BACK_BUTTON = 0
START_BUTTON = 0
L_JS_BUTTON = 0
R_JS_BUTTON = 0
 
triggerThreshold = 0.25
 
def pollButtons():
    global D_PAD_UP
    global D_PAD_DOWN
    global D_PAD_RIGHT
    global D_PAD_LEFT
    global L_TRIGGER
    global R_TRIGGER
    global A_BUTTON
    global B_BUTTON
    global X_BUTTON
    global Y_BUTTON
    global L_BUMPER
    global R_BUMPER
    global BACK_BUTTON
    global START_BUTTON
    global L_JS_BUTTON
    global R_JS_BUTTON
    
    #If running on Windows:
    if os == 'win':
        #Triggers:
        if gamepad.axisValues[2] > triggerThreshold:
            L_TRIGGER = nextButtonVal(True, L_TRIGGER)
        else:
            L_TRIGGER = nextButtonVal(False,L_TRIGGER)
        if gamepad.axisValues[2] < -triggerThreshold:
            R_TRIGGER = nextButtonVal(True, R_TRIGGER)
        else:
            R_TRIGGER = nextButtonVal(False, R_TRIGGER)
        #D-Pad
        if gamepad.hatValues[0] == 1:
            D_PAD_UP = nextButtonVal(True, D_PAD_UP)
        else:
            D_PAD_UP = nextButtonVal(False, D_PAD_UP)
        if gamepad.hatValues[0] == 2:
            D_PAD_RIGHT = nextButtonVal(True,D_PAD_RIGHT)
        else:
            D_PAD_RIGHT = nextButtonVal(False, D_PAD_RIGHT)
        if gamepad.hatValues[0] == 8:
            D_PAD_LEFT = nextButtonVal(True,D_PAD_LEFT)
        else:
            D_PAD_LEFT = nextButtonVal(False, D_PAD_LEFT)
        if gamepad.hatValues[0] == 4:
            D_PAD_DOWN = nextButtonVal(True,D_PAD_DOWN)
        else:
            D_PAD_DOWN = nextButtonVal(False, D_PAD_DOWN)
        #Buttons
        if 0 in gamepad.activeButtons:
            A_BUTTON = nextButtonVal(True,A_BUTTON)
        else:
             A_BUTTON = nextButtonVal(False, A_BUTTON)
        if 1 in gamepad.activeButtons:
            B_BUTTON = nextButtonVal(True, B_BUTTON)
        else: 
            B_BUTTON = nextButtonVal(False, B_BUTTON)
        if 2 in gamepad.activeButtons:
            X_BUTTON = nextButtonVal(True, X_BUTTON)
        else:
            X_BUTTON = nextButtonVal(False, X_BUTTON)
        if 3 in gamepad.activeButtons:
            Y_BUTTON = nextButtonVal(True, Y_BUTTON)
        else:
            Y_BUTTON = nextButtonVal(False, Y_BUTTON)
        if 4 in gamepad.activeButtons:
            L_BUMPER = nextButtonVal(True, L_BUMPER)
        else:
            L_BUMPER = nextButtonVal(False, L_BUMPER)
        if 5 in gamepad.activeButtons:
            R_BUMPER = nextButtonVal(True, R_BUMPER)
        else:
            R_BUMPER = nextButtonVal(False, R_BUMPER)
        if 6 in gamepad.activeButtons:
            BACK_BUTTON = nextButtonVal(True, BACK_BUTTON)
        else:
            BACK_BUTTON = nextButtonVal(False, BACK_BUTTON)
        if 7 in gamepad.activeButtons:
            START_BUTTON = nextButtonVal(True, START_BUTTON)
        else:
            START_BUTTON = nextButtonVal(False, START_BUTTON)
        if 8 in gamepad.activeButtons:
            L_JS_BUTTON = nextButtonVal(True, L_JS_BUTTON)
        else:
            L_JS_BUTTON = nextButtonVal(False,L_JS_BUTTON)
        if 9 in gamepad.activeButtons:
            L_JS_BUTTON = nextButtonVal(True, L_JS_BUTTON)
        else:
            R_JS_BUTTON = nextButtonVal(False,R_JS_BUTTON)
    #If running on MAC
    elif os == 'dar':
        #Triggers
        if gamepad.axisValues[4] > triggerThreshold:
            L_TRIGGER = nextButtonVal(True, L_TRIGGER)
        else:
            L_TRIGGER = nextButtonVal(False,L_TRIGGER)
        if gamepad.axisValues[5] > triggerThreshold:
            R_TRIGGER = nextButtonVal(True, R_TRIGGER)
        else:
            R_TRIGGER = nextButtonVal(False, R_TRIGGER)
        #D-Pad
        if 0 in gamepad.activeButtons:
            D_PAD_UP = nextButtonVal(True, D_PAD_UP)
        else:
            D_PAD_UP = nextButtonVal(False, D_PAD_UP)
        if 1 in gamepad.activeButtons:
            D_PAD_DOWN = nextButtonVal(False, D_PAD_DOWN)
        else:
            D_PAD_DOWN = nextButtonVal(False, D_PAD_DOWN)
        if 2 in gamepad.activeButtons:
            D_PAD_LEFT = nextButtonVal(True,D_PAD_LEFT)
        else:
            D_PAD_LEFT = nextButtonVal(False, D_PAD_LEFT)
        if 3 in gamepad.activeButtons:
            D_PAD_RIGHT = nextButtonVal(True,D_PAD_RIGHT)
        else:
            D_PAD_RIGHT = nextButtonVal(False, D_PAD_RIGHT)
        #Buttons
        if 4 in gamepad.activeButtons:
            START_BUTTON = nextButtonVal(True, START_BUTTON)
        else:
            START_BUTTON = nextButtonVal(False, START_BUTTON)
        if 5 in gamepad.activeButtons:
            BACK_BUTTON = nextButtonVal(True, BACK_BUTTON)
        else:
            BACK_BUTTON = nextButtonVal(False, BACK_BUTTON)
        if 6 in gamepad.activeButtons:
            L_JS_BUTTON = nextButtonVal(True, L_JS_BUTTON)
        else: 
            L_JS_BUTTON = nextButtonVal(False,L_JS_BUTTON)
        if 7 in gamepad.activeButtons:
            R_JS_BUTTON = nextButtonVal(True, R_JS_BUTTON)
        else:
            R_JS_BUTTON = nextButtonVal(False,R_JS_BUTTON)
        if 8 in gamepad.activeButtons:
            L_BUMPER = nextButtonVal(True, L_BUMPER)
        else:
            L_BUMPER = nextButtonVal(False, L_BUMPER)
        if 9 in gamepad.activeButtons:
            R_BUMPER = nextButtonVal(True, R_BUMPER)
        else:
            R_BUMPER = nextButtonVal(False, R_BUMPER)
        #if 10 in xbox.activeButtons:
            #HOME_BUTTON = nextButtonVal(True, HOME_BUTTON)
        #else:
            #HOME_BUTTON = nextButtonVal(False, HOME_BUTTON)
        if 11 in gamepad.activeButtons:
            A_BUTTON = nextButtonVal(True,A_BUTTON)
        else:
            A_BUTTON = nextButtonVal(False, A_BUTTON)
        if 12 in gamepad.activeButtons:
            B_BUTTON = nextButtonVal(True, B_BUTTON)
        else:
            B_BUTTON = nextButtonVal(False, B_BUTTON)
        if 13 in gamepad.activeButtons:
            X_BUTTON = nextButtonVal(True, X_BUTTON)
        else: 
            X_BUTTON = nextButtonVal(False, X_BUTTON)
        if 14 in gamepad.activeButtons:
            Y_BUTTON = nextButtonVal(True, Y_BUTTON)
        else:
            Y_BUTTON = nextButtonVal(False, Y_BUTTON)
    #If running on Linux
    elif os == 'lin': 
        #Triggers:
        if gamepad.axisValues[2] > triggerThreshold:
            L_TRIGGER = nextButtonVal(True, L_TRIGGER)
        else:
            L_TRIGGER = nextButtonVal(False,L_TRIGGER)
        if gamepad.axisValues[5] < triggerThreshold:
            R_TRIGGER = nextButtonVal(True, R_TRIGGER)
        else:
            R_TRIGGER = nextButtonVal(False, R_TRIGGER)
        #D-Pad
        if 11 in gamepad.activeButtons:
            D_PAD_LEFT = nextButtonVal(True,D_PAD_LEFT)
        else:
            D_PAD_LEFT = nextButtonVal(False, D_PAD_LEFT)
        if 12 in gamepad.activeButtons:
            D_PAD_RIGHT = nextButtonVal(True,D_PAD_RIGHT)
        else:
            D_PAD_RIGHT = nextButtonVal(False, D_PAD_RIGHT)
        if 13 in gamepad.activeButtons:
            D_PAD_UP = nextButtonVal(True, D_PAD_UP)
        else:
            D_PAD_UP = nextButtonVal(False, D_PAD_UP)
        if 14 in gamepad.hatValues:
            D_PAD_DOWN = nextButtonVal(True,D_PAD_DOWN)
        else:
            D_PAD_DOWN = nextButtonVal(False, D_PAD_DOWN)
        #Buttons
        if 0 in gamepad.activeButtons:
            A_BUTTON = nextButtonVal(True,A_BUTTON)
        else:
            A_BUTTON = nextButtonVal(False, A_BUTTON)
        if 1 in gamepad.activeButtons:
            B_BUTTON = nextButtonVal(True, B_BUTTON)
        else: 
            B_BUTTON = nextButtonVal(False, B_BUTTON)
        if 2 in gamepad.activeButtons:
            X_BUTTON = nextButtonVal(True, X_BUTTON)
        else:
            X_BUTTON = nextButtonVal(False, X_BUTTON)
        if 3 in gamepad.activeButtons:
            Y_BUTTON = nextButtonVal(True, Y_BUTTON)
        else:
            Y_BUTTON = nextButtonVal(False, Y_BUTTON)
        if 4 in gamepad.activeButtons:
            L_BUMPER = nextButtonVal(True, L_BUMPER)
        else:
            L_BUMPER = nextButtonVal(False, L_BUMPER)
        if 5 in gamepad.activeButtons:
            R_BUMPER = nextButtonVal(True, R_BUMPER)
        else:
            R_BUMPER = nextButtonVal(False, R_BUMPER)
        if 6 in gamepad.activeButtons:
            BACK_BUTTON = nextButtonVal(True, BACK_BUTTON)
        else:
            BACK_BUTTON = nextButtonVal(False, BACK_BUTTON)
        if 7 in gamepad.activeButtons:
            START_BUTTON = nextButtonVal(True, START_BUTTON)
        else:
            START_BUTTON = nextButtonVal(False, START_BUTTON)
        #if 8 in xbox.activeButtons:
        #    HOME_BUTTON = nextButtonVal(True, HOME_BUTTON)
        #else:
        #    HOME_BUTTON = nextButtonVal(False, HOME_BUTTON)
        if 9 in gamepad.activeButtons:
            L_JS_BUTTON = nextButtonVal(True, L_JS_BUTTON)
        else:
            L_JS_BUTTON = nextButtonVal(False,L_JS_BUTTON)
        if 10 in gamepad.activeButtons:
            R_JS_BUTTON = nextButtonVal(True, R_JS_BUTTON)
        else:
            R_JS_BUTTON = nextButtonVal(False,R_JS_BUTTON)
            
def nextButtonVal(current, last):
    if current == True:
        if last == 1 or last == 2:
            return 2
        else:
            return 1
    else:
        if last == 0 or last == 3:
            return 0
        else:
            return 3
            
def compatibleGamepadFound():
    if gamepad == None:
        return 'NOT_FOUND'
    try:
        pollButtons()
        LSinput()
        RSinput()
    except IndexError:
        return 'INCOMPATIBLE'
    return 'FOUND_AND_COMPATIBLE'
            
