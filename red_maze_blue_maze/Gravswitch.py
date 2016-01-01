from bge import logic

def main():
    own = logic.getCurrentController().owner
    scene = logic.getCurrentScene()
    player = scene.objects[own['PlayerName']]    
    player.alignAxisToVect(own.worldOrientation.col[2])