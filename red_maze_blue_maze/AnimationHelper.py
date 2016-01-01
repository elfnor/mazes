#I created the AnimationHelper.py module to help with the playing of animations. The biggest benefit of 
#this is that it allows for variable playing speed. It is intended to completely replace logic bricks and 
#object.playAction for playing actions, and should not be used in tandem with them for a single armature.
#(Although it uses playAction internally)

#The two main functions of this module are setLayerAnim and manageAnims. setLayerAnim is used to set what
#animation should be playing on a specified layer for a specified armature. This information is stored as 
#properties in the target armature. manageAnims MUST be called EVERY FRAME for each armature that you
#wish to be managed by AnimationHelper. It performs the necessary managing of actions, regulating play
#speed, looping, etc. If you don't call it every frame, the results will be incorrect.

import bge
logic = bge.logic


###The Animation Class###

#This is a class that stores animation properties, as well as the aname of an action. It has no methods, 
#it's essentially a bag of properties. The functions in this module (as well as the animation settings
#in  the Config.py module) use this class to represent animation data.
#An Animation object is expected to contain the following properties(if it doesn't, manageAnims will fail):
#'name', 'playType', 'playSpeed', 'blendin', 'entryFrame', 'endFrame'
#However, 'playType', 'playSpeed', 'blendin', and 'entryFrame' are initialized to default values, so
#you don't have to explicitly set them unless you want something other than the default.

#Accepted values for playType are 'play', 'loop', and 'flip' (you should know what these mean if you're familiar
#with BGE's animation system)

#Important Note:
#The Frame of Entry is NOT like the start_frame parameter of the object.playAction function, because start_frame
#dictates one of the looping and flip flop points, whereas frame of entry merely influences the starting point 
#(the looping and flip flop points are always taken to be zero and LastFrame)
class Animation:
   def __init__(self):
       #Default values       
       self.playType = 'play'
       self.playSpeed = 1
       self.blendin = 10
       self.entryFrame = 0

       
#This function takes an armature and layer, and Animation object, and sets the Animation to play on the
#given layer for the given armature. It does this by storing the info as a property in the target armature.
#manageAnims reads back this info and uses it to play the Animations for the armature.
def setLayerAnim(armature, layer, animation):
    arm = armature
    if not 'Ready' in arm:
        arm['Ready'] = True
        arm['Old'] = []
        arm['FlipDir1'] = []
        arm['Layers'] = []
        
    while len(arm['Old']) <= layer:
        arm['Old'].append(None)
        arm['FlipDir1'].append(False)  
        arm['Layers'].append(None)
        
    arm['Layers'][layer] = animation
 
#Given an armature, manageAnims will search it for animation info set by setLayerAnim, and will play and
#manage actions for the given armature, based on the animation info. Must be called every frame for each 
#armature for proper behavior.
def manageAnims(arm):    
    anims = arm['Layers']
        
    for index in range(len(anims)):
        anim = anims[index]
        
        if anim == None:
            arm.stopAction(index)
            
        else:               
            old = arm['Old'][index]                    
            flipDir = arm['FlipDir1'][index]
            
            name = anim.name
            playType = anim.playType
            speed = anim.playSpeed
            endFrame = anim.endFrame
            blendin = anim.blendin  
            entryFrame = anim.entryFrame    
                         
            if name != old:
                
                arm.playAction(name, 0, endFrame+1, index, 0, blendin, logic.KX_ACTION_MODE_PLAY) 
                arm.setActionFrame(entryFrame, index)   
                old = name
                flipDir = False        
                  
            if name == old:
                if flipDir == False:
                    frame = arm.getActionFrame(index) + speed
                else:
                    frame = arm.getActionFrame(index) - speed
                if playType == 'flip':
                   if frame > endFrame:
                       flipDir = True
                       frame = endFrame
                   if frame < 0:
                       flipDir = False
                       frame = 0           
                if playType == 'loop' and frame >= endFrame:                
                   frame -= endFrame                
                arm.setActionFrame(frame, index) 
                   
                arm['FlipDir1'][index] = flipDir      
                    
                arm['Old'][index] = old   
    
def getLayerAnim(arm, layer):
    try: return arm['Layers'][layer]
    except (KeyError, IndexError): return None
    
    