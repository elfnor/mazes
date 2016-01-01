def main():    
    import bge
    import math
    import mathutils
    import TMath
    import Input
    import Config as C
    logic = bge.logic
    
    cont = logic.getCurrentController()
    own = cont.owner
    sce = logic.getCurrentScene()
    
    #get the camera's target player object
    player = sce.objects[C.Follow]
    #get the camera's and player's orientations
    pOrient = player.worldOrientation
    cOrient = own.worldOrientation
    
    #get the input vector for manual camera control  
    input = Input.camInput()
    inputVec = input[0]
    #this variable tells the script whether to use auto or manual mode
    manual = (not input[1])
    
    #create a manual angle variable if there is none (to store the manually adjusted vertical angle of cam)
    #Initialize it to the value of the 'Angle' property
    if not 'ManualAngle' in own:
        own['ManualAngle'] = C.Angle
        
    mAngle = own['ManualAngle']
    prevAngle = mAngle
    
    #Toggle between auto and manual mode
    if not manual:
        #set manual angle equal to 'Angle' property in auto mode(in which case it isn't really manual)
        mAngle = C.Angle
    
    #player adjustment of the vertical angle in manual mode
    if manual == True:
        #modify the manual angle based on the vertical axis of the camera input vector    
        mAngle += C.ManualTurnSpeed * inputVec[1]   
        
        #Clamp the angle to within the defined range, to stop the user from doing crazy camera inversions.
        if mAngle > C.AngleLimitUp:
            mAngle = C.AngleLimitUp
        if mAngle < C.AngleLimitDown:
            mAngle = C.AngleLimitDown  
        
        #This stores the difference between the current and previous vertical angles (to be used later)
        #The .9 multiplier just makes the camera's movements a bit more stable
        differenceAngle =  .9 * (mAngle - prevAngle)
    
    #Store the manual angle in the 'ManualAngle' property
    own['ManualAngle'] = mAngle 
      
    
    ###Setting The Cam's Orientation### 
        
    #Rotate player orientation by 90 degrees (around X) plus the manual angle to create a target orientation
    #that is later interpolated with the current oreintation
    rotmat = mathutils.Matrix.Rotation(math.pi*0.5 - mAngle, 3, 'X')
    #target orientation
    tOrient = pOrient * rotmat
    
    if manual == True:
        #When manual control is active, this stops the camera from matching the player's z-axis rotation.
        #This means the cam won't automatically follow behind-the-back anymore.
        #However, the cool thing is that, if the player actually tilts sideways (due to gravity-bending madness),
        #or if the camera gets thrown off-kilter, it will right itself to be rightside-up relative to the player.
        #This is kind of hackish. It'd be better to only follow the x and y-axis rotations in the first place (but hard and tedious to code!)
        tVec = TMath.VecToPlane(tOrient.col[2],pOrient.col[0],pOrient.col[1])
        cVec = TMath.VecToPlane(cOrient.col[2],pOrient.col[0],pOrient.col[1])
        rotmat2 = TMath.VecToVecMatrix(cVec,tVec)    
          
        tOrient = rotmat2 * tOrient
    
    #Generate turn speed factor to stop turning when player is facing towards camera, among other things
    #The factor is just 1(meaning no modification to the turn speed) when manual mode is on
    Fac = 1   
    #when manual mode is off, the factor is determined like so
    if manual == False:    
        CamProj = TMath.VecToPlane(cOrient.col[2], pOrient.col[0], pOrient.col[1])
        TargetProj = TMath.VecToPlane(tOrient.col[2], pOrient.col[0], pOrient.col[1])
        
        Fac = CamProj.dot(TargetProj)
        if Fac >= 0:
            Fac = 1
        else:
            Fac += 1    
        if Fac < 0:
            Fac = 0
        Fac *= 8
        if Fac > 1:
            Fac = 1                   
    
    ##Interpolate between old and new cam orientation##
    
    #In manual mode...
    if manual == True:
        
        #Rotate the camera's orientation by the vertical difference angle from earlier.
        #Although the target orientation has already had the manual vertical angle applied to it,
        #and the camera's orientation will slowly adopt that angle through interpolation,
        #this speeds up the process so you don't have to wait for the camera's orientation to catch up
        #with the target orientation, therefore there will be no lag in manually adjusting the
        #camera's vertical angle.
        verticalAngleRotmat = mathutils.Matrix.Rotation(-differenceAngle,3,tOrient.col[0])
        cOrient = verticalAngleRotmat * cOrient
        
        #Generate the matrix for the manual horizontal rotation
        manualHorizontalRotmat = mathutils.Matrix.Rotation(C.ManualTurnSpeed * inputVec[0], 3, pOrient.col[2])
        
        #Perform the interpolation between the camera's current orientation and the target orientation (faster than in auto mode)
        cOrient = TMath.MatrixLerp(cOrient, tOrient, 1 - .97*(1 - C.TurnSpeed*Fac))
        
        #Apply the manual horizontal rotation
        cOrient = manualHorizontalRotmat * cOrient
    
    #In auto mode, just do the interpolation step
    else:
        cOrient = TMath.MatrixLerp(cOrient, tOrient, C.TurnSpeed * Fac)        
   
    
    ###Set the camera's distance, raycast to check for obstacles###    
    
    #If there is no current distance variable, make one, set it to 'Distance' property(which is the max distance)
    if not 'CurrentDist' in own:
        own['CurrentDist'] = C.Distance
            
    pos = player.worldPosition
    pos2 = own.worldPosition
    ray = own.rayCast(pos2, pos, C.Distance, 'CamBlock', 0, 1) #Do raycast
   
    dist = own['CurrentDist']
    
    #If the raycast hit something...
    if ray[0] != None: 
        #If the hit distance is closer than the current distance, zoom in to the hit distance
        if(player.worldPosition-ray[1]).length < dist:
            dist = (player.worldPosition-ray[1]).length
        #Otherwise, blend between the current distance and hit distance (to zoom out gradually)
        else:
            dist = 0.95*dist+0.05*(player.worldPosition-ray[1]).length
    #Otherwise, blend between the current distance and the 'Distance' property
    else:
        dist = 0.95*dist+0.05*C.Distance
    
    own['CurrentDist'] = dist
      
    
    ###Computing The Cam's Position### 
       
    #This section computes the cam's new position, with an added delay(using a "delay list")
    #The positional delay makes the camera look ahead of the player when he turns
    
    #create offset list, if it doesn't already exist    
    if not 'CamOffsList' in own: 
        own['CamOffsList'] = []  
        
    own['CamOffsList'].append(cOrient.col[2]) #add new offset vector to end of list(based on the current cam orientation)
    while len(own['CamOffsList']) > (C.LookAheadAmt /C.LookAheadSpd) + 1: #if list gets too long...
        own['CamOffsList'].pop(0) #remove the first element, push everything up to take it's place
    
    #If manual mode is on, and the offset list is longer than 1, shrink the offset list by two elements (one if there's only one).
    #This disables the offset during manual mode, but does so gradually
    if manual == True and len(own['CamOffsList']) > 1:
        own['CamOffsList'].pop(0)
    if manual == True and len(own['CamOffsList']) > 1:
        own['CamOffsList'].pop(0)
        
    #Get the first(oldest) offset vector stored in list, blend it with the newest offset vector
    CamOffs = own['CamOffsList'][0]*C.LookAheadSpd + cOrient.col[2]*(1-C.LookAheadSpd)
    #Normalize this new offset vector
    CamOffs.normalize()
    #Multiply the offset vector with the distance variable and add it to the player's location to get the camera's location
    cPos = player.worldPosition + CamOffs * dist
    cPos[2] +=  C.VerticalOffset #Add the vertical offset to the location
    
        
    #Set the final orientation and position
    own.worldOrientation = cOrient
    own.worldPosition = cPos