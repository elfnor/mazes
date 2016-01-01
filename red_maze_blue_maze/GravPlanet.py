from bge import logic

def main():
    own = logic.getCurrentController().owner
    scene = logic.getCurrentScene()
    player = scene.objects[own['PlayerName']]
    
    if 'InRange' not in own:
        own['InRange'] = False
    
    differenceVec = player.worldPosition - own.worldPosition
    dist = differenceVec.length
    
    if dist <= own['PullDist']:        
        player.alignAxisToVect(differenceVec)
        own['InRange'] = True
    elif dist >= own['ReleaseDist'] and own['InRange'] == True:
        ref = scene.objects[own['ReferenceObj']]
        player.alignAxisToVect(ref.worldOrientation[2])
        own['InRange'] = False