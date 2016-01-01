def main():    
  ###Initial Stuff###
    
    import bge
    import math
    import mathutils
    import TMath
    import AnimationHelper
    import Input
    import Config as C
    import copy
    Vector = mathutils.Vector
    logic = bge.logic
    events = bge.events
    GD = logic.globalDict
    
    cont = logic.getCurrentController()
    own = cont.owner
    sce = logic.getCurrentScene()
    #Get the camera(specified by the player object's 'cam' property)
    cam = sce.objects[C.Cam]    
    orient = own.worldOrientation
    
    ##Here, I create various object properties that the script will need later, if they don't already exist
           
    if not 'State' in own:
        own['State'] = 'idle'
    state = own['State']
    #own['PlatformVelocity'] stores the velocity of the platform the player is stainding on (from the last frame)
    #It's LOCAL to the player's orientation, by the way
    if not 'PlatformVelocity' in own:
        own['PlatformVelocity'] = [0,0,0]
    platformVelocity = own['PlatformVelocity']
    #own['PrevOffset'] is used during ledge grab/hang/climb operations. I'll explain it the relevant sections
    if not 'PrevOffset' in own:
        own['PrevOffset'] = None
    #own['NoMoreGrab'] is used to temporarily toggle on/off ledgeGrab, so you don't re-grab a ledge after falling off.
    if not 'NoMoreGrab' in own:
        own['NoMoreGrab'] = False
    #own['RespawnCount'] counts the frames after you die, and when it reaches a certain value you respawn
    if not 'RespawnCount' in own:
        own['RespawnCount'] = 0
      
    ##Spawning at the start of scene
    
    #own['RespawnObj'] stores the place to respawn at (either the initial spawn point or last touched checkpoint)
    #If RespawnObj does not yet exist in own(e.g. this is the first frame this script has been run), spawn player at spawn object.
    #If Config.ResetSceneUpon death is enabled, then when player dies, respawnObj position and location are stashed in logic.globalDict.
    #Upon restart of scene, position and location are read from globalDict, and 'RespawnObj' is set to None, purely to indicate
    #that the player has finished respawning, so he won't respawn repeatedly.
    if not 'RespawnObj' in own:
        if 'PlayerSpawnPosition' in GD and GD['SpawnPositionScene'] == sce.name:            
            own.worldPosition = GD['PlayerSpawnPosition']
            own.worldOrientation = GD['PlayerSpawnOrientation']
            own['RespawnObj'] = None
        else:
            own['RespawnObj'] = sce.objects[C.SpawnObjectName]
            own.worldPosition = own['RespawnObj'].worldPosition
            own.worldOrientation = own['RespawnObj'].worldOrientation
        
    maxSpd = C.MaxSpeed
    walkSpd = C.WalkSpeed
    #get and tweak the turning smoothness factor
    smooth = (C.TurnSmoothness * .75) + .125
    
    
  ###Calculating The Forward Direction Vector(relative to the camera)###
    
    #Get the direction the camera is facing(as an XYZ vector)
    forwardAxis = -1 * mathutils.Vector(map(lambda x: x[2], cam.worldOrientation))
    #Get the X, Y, and Z axes of the player object
    axisX = mathutils.Vector(orient.col[0])
    axisY = mathutils.Vector(orient.col[1])
    axisZ = mathutils.Vector(orient.col[2])
    #Flatten the camera's direction onto the player object's local XY plane
    forwardAxis = TMath.VecToPlane(forwardAxis, axisX, axisY)
    
    
  ###Get Input###
    if Input.controlScheme == 'Gamepad':
        Input.pollButtons()
  
    input = Input.moveInput()
    
    isMoving = (input.length != 0)
    inputVec = input
    jump = Input.jumpInput()
    heldJump = Input.jumpIsHeldDown()
    drop = Input.dropInput()
            
  ###Floor Raycast### ###
    
    #The starting point of the ray is the player's position
    pos = own.worldPosition
    
    #Get the per-frame vertical offset caused by the player's velocity 
    #(to add to the length of the ray, so the player doesn't fall into the ground at high fall speeds
    velOffset = own.getLinearVelocity(1)[2]/60    
    
    #The ending point is the player's position minus (the player's height times the player's local z-axis(unit length)
    #This means the ray will always point downwards along the player's local z-axis
    pos2 = [pos[i] - C.Height*axisZ[i] for i in range(3)]
    #If the player is on the ground, extend the length of the ray by the player's step size, plus velOffset
    if own['State'] == 'walk' or own['State'] == 'run' or own['State'] == 'idle':
       pos2 = [pos2[i] - (1.001*C.Step-velOffset)*axisZ[i] for i in range(3)]
    #If player is in the air, add all axes of player's linear velocity to ray end position
    elif state == 'fall' or state == 'jump':
       pos2 = [pos2[i] + own.getLinearVelocity(0)[i]/60 for i in range(3)]
    #Do raycast
    ray = own.rayCast(pos2, pos, 0, "", 1, 1)
   
    #Determine whether the detected floor is standable
    noStand = False
    if ray[0] != None and 'NoStand' in ray[0]:
        noStand = True
    
  ###Jump Detection###
    
    justJumped = False
    #If X has just been pressed and the player is not in the fall or jump state
    if jump == True and state != 'fall' and state != 'jump':
        #Set justJumped to True
        justJumped = True
        
  ###Ledge Grab Raycasts###
  
    ###Note: To see test visualization of all the rays used during ledge grab, uncomment lines 167, 238, and 239
	#This can help you understand the code better.
    
    justGrabbed = False #false by default
    #Recover the ledgeRay results, wallRay results, and riseVec from the previous frame, if they exist. This lets us keep reusing the same
    #hit point data over many frames during ledge grabbing    
    if 'LedgeRay' in own: ledgeRay = own['LedgeRay']
    if 'WallRay' in own: wallRay = own['WallRay']
    if 'RiseVec' in own: riseVec = own['RiseVec']    
    
    #While in fall state, do ledge detection
    if own['State'] == 'fall' and own['NoMoreGrab'] == False and C.UseLedgeHang == True:
        #I'm going to cast a series of downward rays to detect ledges
        
        #pos1 is the starting position of the first ray in the series
        #pos1 = player position offset by max grab height and min ray distance.
        pos1 = [pos[i] + C.MaxGrabHeight*axisZ[i] for i in range(3)]
        pos1 = [pos1[i] + C.MinRayDistance*axisY[i] for i in range(3)]        
                
        #offsetVec is the vector that is added to the star position of each ray to determine the end position
        #It goes straight down along -Z axis, and has length of grab range+velOffset
        offsetVec = [(-(C.MaxGrabHeight-C.MinGrabHeight)+velOffset)*axisZ[i] for i in range(3)] 
        #rayStepVec is the vector by which each successive vector in the series is offset from the last
        rayStepVec = [(C.MaxRayDistance-C.MinRayDistance)*axisY[i]/(C.NumRays-1) for i in range(3)]
        
        #pos2 is the ending position of the first ray in the series
        pos2 = [pos1[i] + offsetVec[i] for i in range(3)]
        
        #Calculate how far each successive ray endpoint must rise above the next, so the line of rays matches the incline
        #of the steepest allowed grab angle (this is necessary for complicated reasons)
        tan = math.tan(C.SteepestGrabAngle*1.01)                   
        run = (C.MaxRayDistance-C.MinRayDistance)/(C.NumRays-1)
        rise = max((tan+.1),.1) * run
        
        upStepVec = rise * axisZ
        #Then add it to the rayStepVec to get rayStepVec 2
        rayStepVec2 = [rayStepVec[i]+ upStepVec[i] for i in range(3)]
        
        #for each ray in the series
        for i in range(C.NumRays): 
            #bge.render.drawLine(pos1, pos2, [0,1,1])  #this is for testing 
            ledgeRay = own.rayCast(pos2, pos1, 0, "", 1, 1) #cast the ray from the start to the end positions        
            if ledgeRay[0] != None: #if the ray hit something
                normal = ledgeRay[2]
                angle = normal.angle(axisZ) #get angle between hit normal and local Z-axis
                #if the hit normal is not too steep to grab ledge, and ledge is grabbable...    
                if angle <= C.SteepestGrabAngle and not 'NoGrab' in ledgeRay[0]:                
                    #Obstruction testing
                    #Now I need to make sure there isn't a wall between the player and the ledge. To do this,
                    #I'll shoot a ray that's level with a point just above the hit point, and the ray will 
                    #start above the player's center and end over the hitpoint. If it hits anything, then the ledge is
                    #obstructed 
                    
                    #In case of a ledge surface that slopes upwards going towards the player, I need to account for the rise
                    #of the ledge to make sure the obstruction ray goes just above the edge. That's what I calculate this riseVec for 
                    Yangle = normal.angle(axisY)                   
                    tan = -math.tan(Yangle - math.pi/2)                   
                    run = (C.MaxRayDistance-C.MinRayDistance)/(C.NumRays-1)
                    #The vertical rise over the ray step distance stepping TOWARDS PLAYER:
                    rise = max(tan+.1, .1) * run
                    
                    riseVec =  rise * axisZ
                    
                    #add riseVec to hitpoint to get the obstruction ray's ending pos
                    pos2 = ledgeRay[1] + riseVec
                    #subtract some junk from ending pos to get a starting position above the player's horizontal center
                    pos1 = Vector(pos2) - (C.MinRayDistance*axisY + Vector(rayStepVec)*i)
                    #stash the ray endpoints (plus color [0,1,1], that is, cyan) in a variable to be drawn further down (for testing)
                    own['testvar'] = (pos1, pos2, [0,1,1])
                    obstructionRay = own.rayCast(pos2, pos1, 0, "", 1, 1) #Cast the ray
                    if obstructionRay[0] == None: #If the ray found no obstruction...
                        #Wall Raycasting
                        #Now we want to shoot a ray to detect the wall of the ledge, to determine
                        #the exact direction and position to put the player at while hanging
                        #So we want this ray to go <i>just under</i> the edge
                        
                        #In case of ledges that slope downwards toward the player, I need to account for the fall of
                        #the ledge to make sure the ray goes just under the ledge. VERY similar to calculating riseVec, above.
                        fall = min((tan-.1),-.1) * run
                        fallVec = fall * axisZ
                        
                        #Same things I did for the last raycast (this one is basically the same as the last,
                        #except the ray is positioned a little lower)
                        pos2 = ledgeRay[1] + fallVec
                        pos1 = Vector(pos2) - (C.MinRayDistance*axisY + Vector(rayStepVec)*i)
                        
                        own['testvar2'] = (pos1, pos2, [0,1,1]) #Stash the ray endpoints in variable to be drawn further down
                        wallRay = own.rayCast(pos2, pos1, 0, "", 1, 1) #Do raycast
                                                
                        if wallRay[0] != None: #If the wall way found a wall...
                            justGrabbed = True #finally set justGrabbed to true, to signal the transition into grab state
                            ledgeVelocity = mathutils.Vector(ledgeRay[0].getLinearVelocity(0)) #get ledge velocity
                            
                            own['PrevLedgeVel'] = ledgeVelocity #store it in object property
                            
                            #Save raycast results and risevec data in object properties to be used during ledge grab/climb process
                            ledgeRay = list(ledgeRay)
                            ledgeRay[1] += ledgeVelocity/60
                            wallRay = list(wallRay)
                            wallRay[1] += ledgeVelocity/60
                            own['LedgeRay'] = ledgeRay
                            own['RiseVec'] = riseVec
                            own['WallRay'] = wallRay
                                                        
                break #break if one of the ledge rays has hit a ledge with an angle shallow enough to grab
            
            #Now I need to apply the ray step vecs to the start and end points for the next ray in the loop
            pos1 = [pos1[i] + rayStepVec[i] for i in range(3)]
            pos2 = [pos2[i] + rayStepVec2[i] for i in range(3)]          
    
    #Uncomment these lines for test visualization of obstruction and wall rays
    #if 'testvar' in own: bge.render.drawLine(*own['testvar'])
    #if 'testvar2' in own: bge.render.drawLine(*own['testvar2'])
  
  ###Checkpoint Collision Test###
    #If a checkpoint is touched, store it in the 'RespawnObj' property
    checkSense = cont.sensors['Checkpoint']
    if checkSense.positive:
       checkpoint = checkSense.hitObjectList[0]
       own['RespawnObj'] = checkpoint
  
  ###Death Collision Test###
    justDied = False
    deathSense = cont.sensors['Death']
    #if death collision sensor or floor raycast detect an object with property 'Death'...
    if deathSense.positive or (ray[0] != None and 'Death' in ray[0]):
        justDied = True #You just died!
        
  ###Changing State### 
    initializeClimb = False    
    noFallBlendin = False
    
    if state == 'dead':
        if own['RespawnCount'] >= C.DeathDelay*60: #if time to respawn...
           if C.ResetSceneUponDeath == True:
               #Stash respawn object's position and orientation
               GD['PlayerSpawnPosition'] = Vector(own['RespawnObj'].worldPosition)
               GD['PlayerSpawnOrientation'] = mathutils.Matrix(own['RespawnObj'].worldOrientation)
               GD['SpawnPositionScene'] = sce.name
               sce.restart()
           else:
                state = 'fall'
                
                #If own['RespawnObj'] is not None (it would only be None in the corner case where 
                #ResetSceneUponDeath was set to True, the player died and respawned, and thus
                #respawnObj would be set to None, THEN the user of this template changed
                #ResetSceneUponDeath to false via a script.
               
                if own['RespawnObj'] != None:
                   #copy the respawn point's position and orientation
                   own.worldPosition = own['RespawnObj'].worldPosition
                   axisX, axisY, axisZ = own['RespawnObj'].worldOrientation.col
                #If spawn obj is None, respawn to position and orientation stashed in GlobalDict
                else:
                   own.worldPosition = GD['PlayerSpawnPosition']
                   axisX, axisY, axisZ = GD['PlayerSpawnOrientation'].col
                own['RespawnCount'] = 0 #reset respawn counter to 0
                noFallBlendin = True #Don't blend into fall anim, transition IMMEDIATELY
    elif justDied == True:
       state = 'dead'           
    elif justGrabbed == True:
        state = 'grab'
    elif state == 'climb':
        pass #Do nothing... this is just to escape from the elif chain
    #If player's feet touch the ground while grabbing a ledge...
    elif state == 'grab':
        if ray[0] != None:
            initializeClimb = True #climb immediately
    elif state == 'hanging':
        #Climb up if jump button is pushed
        if justJumped == True:
            initializeClimb = True
        #Drop down if drop button is pushed
        elif drop == True:  
            state = 'fall'
            #Temporarily disable grab (will be re-enabled when player lands on floor again)
            own['NoMoreGrab'] = True 
            #This has to do with the grabbing and climbing process; see relevant sections
            own['PrevOffset'] = None    
    elif justJumped == True:
        state = 'jump'
    #During jump or spring state, when player is no longer moving upward, switch to fall state.
    elif state == 'jump' or state == 'spring':
        if own.getLinearVelocity(1)[2] <= 0:
            state = 'fall' 
    #When not on floor, fall          
    elif ray[0] == None or noStand == True:
        state = 'fall'
    #When standing on a spring surface...
    elif 'Spring' in ray[0] and (state == 'walk' or state == 'idle'):        
        justJumped = True
        state = 'spring'  
        
    elif isMoving  == True:
        #If on ground, allow the player to grab again (if grab was disabled in the first place)
        own['NoMoreGrab'] = False 
        state = 'walk'
    else:
        #If on ground, allow the player to grab again
        own['NoMoreGrab'] = False 
        state = 'idle'    
        
  #Climb state initialization 
    if initializeClimb == True:        
        state = 'climb'
        #Climbing has two phases (it always starts with phase 1):
        #Phase 1: the player (physics object) moves upwards until higher than ledge
        #Phase 2: player moves forward, over and onto ledge
        own['ClimbPhase'] = 1
        own['PrevOffset'] = None #Used during climbing/hanging; see relevant sections
        
  ###Calculating The Movement Direction Vector###
    
    #If the player is inputting a direction
    if isMoving == True:
        #Convert the input vector to an angle(in radians)
        inputAngle = math.atan2(inputVec[1], inputVec[0])
        #Rotate angle so that the vector (0,1) maps to the angle 0
        inputAngle = inputAngle - (math.pi/2)
            
        #Rotate the forward direction vector by the inputAngle
        rotMat = mathutils.Matrix.Rotation(inputAngle, 3, axisZ)
        directionVec = rotMat * forwardAxis
    
  ###Movement###    
  
    noIdleBlendin = False
    
    ##Movement when dead
    
    if state == 'dead':
       own['RespawnCount'] += 1 
       #If not on standable ground, fall according to gravity and don't play death anim
       if ray[0] == None or noStand == True:
           playDeathAnim = False
           Xspeed, Yspeed, Zspeed = own.getLinearVelocity(1)
           Zspeed -= C.Gravity
           if Zspeed < -C.TerminalVelocity:
               Zspeed = -C.TerminalVelocity
       #If on standable ground, copy platform's velocity and play death anim
       else: 
           playDeathAnim = True
           platformVelocity = mathutils.Vector(ray[0].getLinearVelocity(0)) * own.worldOrientation
           Xspeed, Yspeed, Zspeed = platformVelocity
           
    ##Movement during ledge hang, grab, climb
    
    elif state == 'hanging' or state == 'grab' or state == 'climb':
        
        #I use this function to move the player towards(but not past) desired positions at a certain speed during ledge grab/climb process
        #It operates on floats, not vectors(I apply it to eaxh axis individually). It returns a velocity
        def moveCloser(offset, speed):
           offset *= 60
           #if 'offset' is small enough to be reached in one frame traveling at given 'speed', then...
           if abs(offset) <= abs(speed):
                #We've traveled the entire offset, and are now on target
                onTarget = True
                #Return the velocity necessary to reach the offset in one frame (offset *60)
                outSpeed = offset
           #if 'offset' is too large to reach in one frame traveling at given 'speed', then...     
           else:
                #We couldn't travel the entire offset, and so are not on target
                onTarget = False 
                #Return a velocity equal to speed, but in the direction of the offset (negative if offset = negative)
                if offset < 0: outSpeed = -speed
                else: outSpeed = speed 
           #Return whether we're on target and what the velocity is
           return (onTarget, outSpeed)          
       
        #Velocity of the grabbed surface, from the PREVIOUS FRAME (technically two frames ago; see below)
        prevLedgeVel = Vector(own['PrevLedgeVel'])            
        #Current velocity of the grabbed surface (technically one frame ago)
        #(Note that whenever you get the velocity of an object, it will actually be behind one frame)
        ledgeVelocity = Vector(ledgeRay[0].getLinearVelocity(0))
        #Stash the current-frame velocity in own['PrevLedgeVel'] to use next frame
        own['PrevLedgeVel'] = Vector(ledgeVelocity)
        
        #This modifies the working velocity to compensate for the 1-frame lag mentioned above
        ledgeVelocity += ledgeVelocity - prevLedgeVel                      
        
        #Movement during climb    
        if state == 'climb':
            #Stores whether or not player has reached target position (e.g. the climb is finished) (set false by default)
            inPosition = False
            #Stores the frame to start the climb animation on (set to 0 by default)
            climbStartFrame = 0
            #Move the ledge ray hit position according to ledge velocity, to sync with ledge movement
            ledgeRay[1] += ledgeVelocity/60
            #Move the player's position according to ledge velocity, to sync with ledge
            #Note that I'm only changing a COPY of the player's position. I update his actual position by applying velocity.
            pos = Vector(pos) + ledgeVelocity/60  
            
            #The target point to climb towards (above and over the ledge)
            targetPoint = ledgeRay[1] + riseVec + C.Height * axisZ + C.ClimbLength*axisY
            #The difference vector between the player position and the target position
            offset = targetPoint - pos  
            
            #Finds the climb speed that will complete the climb in the number of frames specified by C.ClimbAnim.endFrame
            speed = (C.Height+C.HangHeight+C.ClimbLength+C.HangDistance)/(C.ClimbAnim.endFrame/60)     
            
            Zspeed, Yspeed = 0, 0 #set to 0 by default
            
            #If in first phase of climbing (the going up part)...
            if own['ClimbPhase'] == 1: 
               #Find scalar offset along player's local Z axis from player to target point (projection of offset onto local Z axis)
               Zoffs = axisZ.dot(offset)
               #Find the Z velocity necessary to move towards (but not past) a point level with
               #the target point at given speed (Zspeed). Also find whether moving at that speed will bring us 
               #vertically level with target point by next frame (onTarget).
               onTarget, Zspeed = moveCloser(Zoffs, speed)
               #If vertically aligned with target point, move to phase 2 of climb (the going forwards part)
               if onTarget: own['ClimbPhase'] = 2
            
            #Scalar offset along local Y axis (see Zoffs) 
            Yoffs = axisY.dot(offset) 
            #If in the second phase of climbing(moving forward)...         
            if own['ClimbPhase'] == 2:
                #Get the Yspeed necessary to move towards target point, and whether the climb is finished (inPosition)
                inPosition, Yspeed = moveCloser(Yoffs, speed)
            
            #If on the first frame of the climb...
            if initializeClimb == True:         
               #Determine how large the offset to TargetPoint relative to expected value when climbing out of a hang
               offsetRatio = (abs(Zoffs)+abs(Yoffs))/(C.Height+C.HangHeight+C.ClimbLength+C.HangDistance)   
               #If offset is smaller than expected offset..
               #(e.g. the player's feet touched the ground while grabbing and forced him into a climb before reaching hang state)            
               if offsetRatio < 1:
                  #Determine the climb anim start frame based on offset ratio (if offset is 1/2 usual value, climb anim will start halfway through)
                  climbStartFrame = (1-offsetRatio)*C.ClimbAnim.endFrame 
                  #Snap the armature(NOT collision mesh) into hanging position                        
                  armaturePosition = ledgeRay[1] - C.HangDistance*axisY -C.HangHeight*axisZ
                  sce.objects[C.Armature].worldPosition = armaturePosition   #assign the position
               #Parent the armature to the ledge object, removing parent to collision mesh in the process
               #(the climb is animated entirely through an action, so armature should be fixed in place)                          
               sce.objects[C.Armature].setParent(ledgeRay[0], False, False) 
            
            #Transform ledgeVelcity into player local space, and apply to player's local linear velocity, so he moves with ledge
            ledgeVelocity = ledgeVelocity * own.worldOrientation       
            Xspeed = ledgeVelocity[0]            
            Yspeed += ledgeVelocity[1]            
            Zspeed += ledgeVelocity[2]
            
            #If current offset is greater than or equal to than previous offset, something must be in the way, so we bail out of the climb
            bailout = False
            if own['PrevOffset'] != None and offset.length >= own['PrevOffset'].length:
                    bailout = True             
            
            #If the climb is finished (either properly or by bailout)...
            if inPosition or bailout:
               ###MID-CODE STATE CHANGE!!!###  
               state = 'idle'
               own['PrevOffset'] = None #reset 'PrevOffset' to None
               #Set armature position to collision mesh position, and re-parent it to collision mesh
               sce.objects[C.Armature].worldPosition = own.worldPosition
               sce.objects[C.Armature].setParent(own, False, False)
               #Transition into idle animation must happen immediately, because the climbing animation offsets the entire skeleton
               noIdleBlendin = True
            
            #Assign current offset to 'PrevOffset' to use next frame (only if still in climb state)   
            if state == 'climb': own['PrevOffset'] = offset
        
        #Movement while hanging    
        if state == 'hanging':
            #Update the ray hit positions based on the ledge velocity
            ledgeRay[1] += ledgeVelocity/60
            wallRay[1] += ledgeVelocity/60
            
            #Update (a copy of) player position based on ledge velocity
            pos = Vector(pos) + ledgeVelocity/60            
            #Calculate the difference vector between player position and target hanging position
            offset = wallRay[1] - pos + C.HangDistance*-axisY + C.HangHeight *-axisZ
            
            #If offset is greater than o equal to offset from last frame (e.g. something's in the way), and offset is greater than
            #tolerance, cancel the hand and go into fall state.
            if offset.length >= own['PrevOffset'].length and offset.length > C.GrabTolerance:
                ###MID-CODE STATE CHANGE!!!###
                state = 'fall' 
                own['NoMoreGrab'] = True
                own['PrevOffset'] = None #Reset PrevOffset to None        
            
            #if still in hang state, set PrevOffset to offset to be used next frame.
            if state == 'hanging': own['PrevOffset'] = offset
            
            #Transform ledge velocity to player-local space and apply it to player velocity.
            ledgeVelocity = ledgeVelocity * own.worldOrientation       
            Xspeed, Yspeed, Zspeed = ledgeVelocity
            
        #Movement while grabbing a ledge    
        elif state == 'grab':
            
            ###Parts of this are extremely similar to the 'climb' state section above. Look there for more comments.
            inPosition = True
            ledgeRay[1] += ledgeVelocity/60
            wallRay[1] += ledgeVelocity/60
            
            pos = Vector(pos) + ledgeVelocity/60  
            
            normal = Vector(ledgeRay[2])
            hitPoint = Vector(ledgeRay[1])
            
            #Get the difference vector between current position target hang position
            offset = hitPoint - (pos + axisZ * C.HangHeight)
            
            minSpeed = C.MinGrabSpeed 
            
            #Transform ledge velocity to player local space.
            ledgeVelocity = ledgeVelocity * own.worldOrientation  
            #Get player Z velocity relaive to ledge velocity
            currentSpeed = own.getLinearVelocity(1)[2] - ledgeVelocity[2]
            
            #Set speed to abs(currentSpeed) unless current speed is less than minSpeed, in which case use minspeed. 
            if abs(currentSpeed) > abs(minSpeed): speed = abs(currentSpeed)
            else: speed = minSpeed     
            
            #Move closer to target along Z axis
            Zoffs = axisZ.dot(offset)
            onTarget, Zspeed = moveCloser(Zoffs, speed)
            inPosition = (onTarget and inPosition)
            ###
            
            #Get the normal of the ledge wall
            wallNorm = wallRay[2]
            #Align player Y axis with wall normal
            axisY = -TMath.VecToPlane(wallNorm, axisX, axisY).normalized()
            
            offset = wallRay[1] - pos + C.HangDistance*-axisY + C.HangHeight *-axisZ
            
            #bge.render.drawLine(pos, Vector(pos)+offset, [0,1,1])  
            
            HGS = C.HorizontalGrabSpeed
            
            #Move closer to target along X axis
            Xoffs = axisX.dot(offset)
            onTarget, Xspeed = moveCloser(Xoffs, HGS) 
            inPosition = (onTarget and inPosition)
            
            #And Y axis
            Yoffs = axisY.dot(offset)
            onTarget, Yspeed = moveCloser(Yoffs, HGS) 
            inPosition = (onTarget and inPosition)                             
            
            #Add ledge velocity to player velocity.    
            Xspeed += ledgeVelocity[0]
            Yspeed += ledgeVelocity[1]
            Zspeed += ledgeVelocity[2]
            
            ###MID-CODE STATE CHANGE!!!###    
            #If player is at target hang position, switch to hang state
            if inPosition == True:
               state = 'hanging'
               
            if own['PrevOffset'] != None:
                #If current offset is >= to previous (e.g. something is in the way)...
                if offset.length >= own['PrevOffset'].length:
                    #If current offset is not within the range of tolerance, cancel the grab and switch to fall state
                    if offset.length > C.GrabTolerance:
                        state = 'fall'
                        own['NoMoreGrab'] = True
                        Xspeed, Yspeed = 0,0 
                        own['PrevOffset'] = None          
                    #If current offset is within tolerance, just go to hang state. 
                    else:
                        state = 'hanging'      
            
            #Set PrevOffset to offset, to be used next frame (but NOT if state has been changed to fall)     
            if state == 'grab' or state == 'hanging': own['PrevOffset'] = offset
            
    #if not in grab state...    
    else:
        ##Air Control and Falling##
        if state == 'fall' or state == 'jump' or state == 'spring':
            #Get the velocities from last frame
            Xspeed, Yspeed, Zspeed = own.getLinearVelocity(1)
            #If human player is inputting a direction...
            if isMoving == True:
              #Project the input vector onto player's Y-axis to get local Y component of input
              Yair = directionVec.dot(axisY)
              #Apply acceleration in appropriate direction, ONLY IF Yspeed is below the maximum
              #for forward or backwards movement
              if Yair >= 0 and Yspeed < C.AirMaxFront:
                  Yspeed += Yair * C.AirAccelFront
              elif Yair < 0 and Yspeed > -C.AirMaxFront:
                  Yspeed += Yair * C.AirAccelBack
              #Do the same for X axis, but since there is only one max speed for sideways movement,
              #only one check is needed.   
              Xair = directionVec.dot(axisX)
              if (Xair >= 0 and Xspeed < C.AirMaxSide) or (Xair < 0 and Xspeed > -C.AirMaxSide):
                  Xspeed += Xair * C.AirAccelSide  
            
            gravity = C.Gravity #Get gravity
            #If in jump state, and jump button is not held down, multiply gravity by short jump factor
            if state == 'jump' and heldJump == False:
                gravity /= C.ShortJump
                  
            #Falling: apply gravity, then if abs Zspeed exceeds terminal velocity, set it to terminal velocity.
            Zspeed -= gravity
            if Zspeed < -C.TerminalVelocity:
                Zspeed = -C.TerminalVelocity
                
        else:                
          ##Calculating the target speed                      
            #Normal of the ground surface that the ray hit.
            groundNormal = ray[2]
            
            if groundNormal.dot(axisZ) < 0:
               groundNormal *= -1
                        
            #The angle between the player's local Y-axis and the ground normal
            angle = axisY.angle(groundNormal) 
            #The sine of that angle
            sine = math.sin(angle)
            
            factorUp = C.UphillSlopeFac
            factorDown = C.DownhillSlopeFac
            
          ##Calculate the slope factor(that will modulate the player's speed on slopes) 
            #If the player is going uphill...           
            if angle > math.pi/2:  
                #This algorithm is complex, but isn't based on real physics, I just wanted something that 'felt right'
                
                #Ground normal flattened onto plane defined by player's local horizontal axes
                flatNormal = TMath.VecToPlane(groundNormal, axisX, axisY)
                #Try to find angle between local Y (forward) axis and flatNormal. If it fails, go with 90 degrees.
                try: flatAngle = axisY.angle(flatNormal)
                except: flatAngle = math.pi/2
                #Sine and cosine of this angle
                flatSine = math.sin(flatAngle)
                flatCosine = math.cos(flatAngle)
                #The absolute angle of the slope
                slopeAngle = axisZ.angle(groundNormal)
                #Don't quite remember how this part works...
                interp = (slopeAngle/(math.pi/2))**(1/(factorUp+.0000001))
                thisLimit = 1-interp
                
                ratio = max(min(thisLimit / abs(flatCosine),1),0)                        
                slopeFactor = ratio
            #If the player is going downhill...
            else:
                #Another algorithm created through trial-and-error...
                slopeFactor = (sine+factorDown*(1-sine))/sine                   
            
            #Since the player's speed is always applied along his forward y-axis(not along the slope direction), 
            #he would end up going faster when on any slope... This factor corrects for that.
            correctionFactor = sine
            
            #Get the speed modifier of the ground object
            try: speedMod = ray[0]['SpeedModifier']
            except: speedMod = 1
            
            #The final target speed       
            targetSpd = maxSpd * inputVec.length * correctionFactor * slopeFactor * speedMod
            ################################
            
            ###Now to change the player's direction and Yspeed###
            #Subtract the Y platform velocity from the player's total velocity to get the Y velocity RELATIVE to the platform
            #All velocities are LOCAL to the player's orientation
            Yspeed = own.getLinearVelocity(1)[1] - platformVelocity[1]
            
            if isMoving == True:
                #compensate for turning lag when original and new direction vectors are opposite(or close to it)
                if (axisY + directionVec).length <= 0.1:
                    axisY += axisX * 0.1
                #blend old and new vectors according to smoothness factor(thus smoothing the turning)
                axisY = (1 - smooth) * directionVec + smooth * axisY
                axisY.normalize()    
                #increase speed according to acceleration
                Yspeed = Yspeed + maxSpd * C.Acceleration
                if Yspeed > targetSpd:
                    Yspeed = targetSpd
            else:
                #decrease speed according to deceleration
                Yspeed = Yspeed - maxSpd * C.Deceleration
                if Yspeed < 0:
                    Yspeed = 0 
            #Set X velocity to 0 (we only want him moving forward               
            Xspeed =  0   
        
        ###Latching Onto Ground, Jumping###
           
        #If a jump has just been activated, push the player upwards
        if justJumped == True:
            if state == 'spring':
                Zspeed += ray[0]['Spring']
            else:
                Zspeed += C.Jump            
        
        #If player is not in the air, snap the player onto the ground and set Z velocity to 0
        if state != 'fall' and state != 'jump' and state != 'spring':
            #Find the position the player should be snapped to
            rayHitPos = ray[1]        
            rayHitPos = [rayHitPos[i] + C.Height * axisZ[i] for i in range(3)]
            #Get the current-frame velocity of the platform the player's standing on, and transform it to PLAYER LOCAL space
            platformVelocity = list(mathutils.Vector(ray[0].getLinearVelocity(0)) * own.worldOrientation )
            #When the ground is flat, smoothly blend instead of snap (to allow smooth movement on stairs)
            if sine >= 0.9999:
                stepSmooth = C.StepSmoothing
                if stepSmooth < 0.01: 
                    stepSmooth = .01            
                oldPosition = mathutils.Vector(own.worldPosition)
                positionalDif = mathutils.Vector(rayHitPos)-oldPosition
                if positionalDif.length > (1.1/(60*stepSmooth))*abs(Yspeed):
                    own.worldPosition = list(oldPosition + (1.1/(60*stepSmooth))*positionalDif.normalized()*abs(Yspeed))
                else: own.worldPosition = rayHitPos
            #When the ground is sloped, snap to it
            else:
                own.worldPosition = rayHitPos
            #Set the player's Z velocity to the platform's Z velocity
            Zspeed = platformVelocity[2]
            #Add the platform's XY velocities to the player's relative velocities to get the player's absolute (Local) XY velocities
            Yspeed += platformVelocity[1]
            Xspeed += platformVelocity[0]
        
        
    ###Setting Animations###
    
    #Get the armature
    arm = sce.objects[C.Armature]
    
    #Grab some functions from the animation helper module (See Animation.py module for documentation)
    #This function sets an animation to play for a given armature, on a given layer
    setAnim = AnimationHelper.setLayerAnim
    #This function gets the last animation playing for a given armature, on a given layer 
    getAnim = AnimationHelper.getLayerAnim
    
    #NOTE: "animations" are objects that contain an action to play, and a list of playing properties, such as speed, 
    #last frame, etc. They have no methods, they are just bags of properties.
	#See the comments in the AnimationHelper.py module for documentation on the Animation class
    
    #Get all animations from config file 
    animations = [C.DeathAnim, C.ClimbAnim, C.HangAnim, C.FallAnim, C.RunAnim, C.WalkAnim, C.IdleAnim]
    #Here I make copies of all the animations, so I can change their properties without permanently changing the settings 
    #in the config file
    deathA,climbA,hangA,fallA,runA,walkA,idleA = [copy.copy(i) for i in animations]
    
    #Set animation properties
    if state == 'dead':
        if playDeathAnim == True:
            setAnim(arm, 0, deathA) #Set animation
    elif state == 'climb':
        #Set the climb animation entry frame to the one determined eariler in climb section.
        climbA.entryFrame = climbStartFrame
        setAnim(arm, 0, climbA)
    elif state == 'hanging' or state == 'grab':
        setAnim(arm, 0, hangA)
    elif state == 'fall' or state == 'jump' or state == 'spring':
        #If fall blendin is disabled, set fall animation blendin to zero (only used when respawning)
        if noFallBlendin: 
            fallA.blendin = 0 
        setAnim(arm, 0, fallA)
    else:    
        if state == 'walk':
            #If speed is greater than walk speed (e.g. player is running)...
            if Yspeed > walkSpd*1.001:
                #If the currently playing anim is the walk anim...
                if getAnim(arm, 0).name == C.WalkAnim.name:
                    #Set the run anim entry frame to the walk anim current frame, for continuity between animations
                    runA.entryFrame = arm.getActionFrame(0)
                #Set playspeed to RunAnim.playspeed times ratio of current speed to max speed.
                runA.playSpeed = C.RunAnim.playSpeed*Yspeed/maxSpd
                setAnim(arm, 0, runA)
            #If player is walking...
            else:            
                #Similar to run anim
                if getAnim(arm, 0).name == C.RunAnim.name:
                    walkA.entryFrame = arm.getActionFrame(0) 
                walkA.playSpeed = C.WalkAnim.playSpeed*Yspeed/walkSpd          
                setAnim(arm, 0, walkA)
                        
        elif state == 'idle': 
            #If idle blendin is disabled, set idle anim blendin to zero (used after climbing ledge)          
            if noIdleBlendin:
                idleA.blendin = 0
            setAnim(arm, 0, idleA)    
    
    
    AnimationHelper.manageAnims(arm)  #Once again, see AnimationHelper.py for documentation
    
    ###Final Stuff###
    #Make sure the X axis is orthogonal to the other two
    axisX = axisY.cross(axisZ)  
    own.worldOrientation = TMath.MakeMatrix(axisX,axisY,axisZ)
    own.setLinearVelocity([Xspeed,Yspeed,Zspeed], 1)
    own['State'] = state
    #Update the platform velocity variable
    own['PlatformVelocity'] = platformVelocity
    #Negate global gravity   
    own.applyForce(-sce.gravity * own.mass)