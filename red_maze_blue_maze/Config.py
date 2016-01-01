#####Config File#####
#All values should be 0 or greater, unless otherwise specified

#Any reference to 'Player' or 'Player Object' should be taken to mean the player's physics mesh,
#not his display model.

#BU = Blender Units

import math
from AnimationHelper import Animation

###Player settings###

Cam = 'Camera' #Name of the camera that the player will move relative to

Height = 1.5 #How high to position the player object's center above the ground (in BU)

ResetSceneUponDeath = False

###Camera settings###

Follow = 'Player' #Name of the object for the camera to follow(should be the player object)
Angle = .5 #Elevation angle of the camera, in radians
Distance = 8.0 #Distance from the player, in BU
TurnSpeed = 0.015 #How fast the camera turns in auto mode (value between 0 and 1)
LookAheadAmt = 13.0 #Amount to look ahead of the player when turning in auto mode
LookAheadSpd = 0.2 #How suddenly to look ahead (auto mode only)
VerticalOffset = 0.0 #Vertical offset of the camera, to make it higher or lower (in BU)
ManualTurnSpeed = 0.035 #Turn speed with the manual controls
AngleLimitUp = 1.0 #Highest angle of elevation the user can move the camera
    #Should be greater than AngleLimitDown, but not more than 1.5
AngleLimitDown = -0.3 #Lowest angle of elevation the user can move the camera (Can be negative)
    #Should be less than AngleLimitUp, but not less than -1.5

###Control Input Settings

mouseSensitivity = 37.5
mouseSmooth = 0.3  

joystickThreshold = 0.25

#On-land movement settings
TurnSmoothness = 0.75
WalkSpeed = 3.5 #Speed while not holding the run button
MaxSpeed = 8.0 #Speed while running

    #Acceleration and Deceleration must be greater than 0 and no greater than 1.
    # 1.0 means instant accel/decel, 0.00001 means extremely slow accel/decel.
Deceleration = 0.1
Acceleration = 0.05

#Death
DeathDelay = 2

#Spawn
SpawnObjectName = 'SpawnHere'

#Jump and gravity settings
Jump = 8.0 #Jump strength
ShortJump = .5 #Jump hieght multiplier when jump button is tapped, not held 
    #(should be between 1 and 0, 1 for constant jump height)
Gravity = 0.5 #Gravity strength (the player object ignores global gravity)
TerminalVelocity = 50.0 #Maximum fall speed
    
#Air control settings
AirAccelFront = 0.25 #The rate of forward acceleration (due to directional input) in the air
AirAccelBack = 0.25
AirAccelSide = 0.2
AirMaxFront = 8.0 #The maximum forward speed you can attain in the air 
    #(If you start with a higher speed, i.e. from a running jump, you will keep your speed)
AirMaxBack = 6.0
AirMaxSide = 6.0

#Stair and step settings    
Step = 0.6 #The maximum height (in BU) that can be stepped down from without detaching 
           #from the ground. Should be less than Height.
StepSmoothing = .75 #Amount of smoothing when the player climbs up or down a step
           #This setting impacts how steep your staircases can be without the player
           #detaching from them upon walking down them. See note #2 for details

#Slope settings
UphillSlopeFac = 1.0 #How much the player is slowed down when moving uphill. (0 for no effect)
DownhillSlopeFac = 1.0 #How much the player is sped up when moving downhill. (0 for no effect)
    #(Can be greater than 1)

###Ledge hang settings

UseLedgeHang = True #Enable or disable ledge hang

MaxRayDistance = 0.9 #Maximum distance from player's center from which a ledge can be grabbed.
MinRayDistance = 0.6 #Minimum distance from player's center from which a ledge can be grabbed.
    #Should be about equal to the distance from player center to furthest forward part of collision mesh
    
NumRays = 4 #Increasing this increases the accuracy of the ledge detection.

    #The height of the highest ledge that can be grabbed (RELATIVE to player center)
MaxGrabHeight = 1.3

    #Lowest height (relative)
MinGrabHeight = 0.5
    #IMPORTANT: min grab height MUST NOT be lower than widest point of player collision mesh!
    #So if widest point of C. mesh is .25 units above player center, MinGrabHeight must be at least as high

    #Distance from player center to ledge while hanging
HangDistance = 0.7 #recommended to be very slightly greater than actual distance from center to
    #front of hitbox, due to bullet physics margin(or whatever the issue is)


HangHeight = 1.3 #How far the ledge should be above the player's center while hanging    
SteepestGrabAngle = math.pi/6 #Steepest angle of ledge (relative to player Z-axis) that can be grabbed

MinGrabSpeed = 4.0
HorizontalGrabSpeed = 6.0

GrabTolerance = .5

ClimbLength = .5
ClimbTolerance = .5


#Animation settings

Armature = 'PlayerArmature' #The armature to animate

#########################
WalkAnim = Animation()  #   #Don't change this
#########################
WalkAnim.name = 'Walk'      #Name of the walk action to play
WalkAnim.playType = 'loop'  #Play type: 'loop' 'flip' or 'play'
WalkAnim.playSpeed = 2      #Play speed factor (1 = normal speed)
WalkAnim.endFrame = 110     #Last frame of the action
WalkAnim.blendin = 10       #Amount of frames to blend in

########################
RunAnim = Animation()  #
########################
RunAnim.name = 'Run'
RunAnim.playType = 'loop'
RunAnim.playSpeed = 2
RunAnim.endFrame = 110
RunAnim.blendin = 10

########################
FallAnim = Animation() #
########################
FallAnim.name = 'Fall'
FallAnim.playType = 'flip'
FallAnim.endFrame = 48
FallAnim.blendin = 20

########################
IdleAnim = Animation() #
########################
IdleAnim.name = 'Stand'
IdleAnim.playType = 'play'
IdleAnim.endFrame = 10
IdleAnim.blendin = 10

########################
HangAnim = Animation() #
########################
HangAnim.name = 'Hang'
HangAnim.playType = 'play'
HangAnim.endFrame = 10
HangAnim.blendin = 10

########################
ClimbAnim = Animation()#
########################
ClimbAnim.name = 'Climb'
ClimbAnim.endFrame = 56

########################
DeathAnim = Animation()#
########################
DeathAnim.name = 'Death'
DeathAnim.endFrame = 100