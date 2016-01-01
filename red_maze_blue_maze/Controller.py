import Input
import bge

def main():
    
    logic = bge.logic
    cont = logic.getCurrentController()
    own = cont.owner 
    if own['Control Scheme'] == 1:
        Input.controlScheme = 'ArrowKeys/WASD'
    if own['Control Scheme'] == 2:
        Input.controlScheme = 'WASD/Mouse'
    if own['Control Scheme'] == 3 and Input.controlScheme != 'Gamepad':
        status = Input.compatibleGamepadFound()
        if status == 'FOUND_AND_COMPATIBLE':
            Input.controlScheme = 'Gamepad'
        elif status == 'NOT_FOUND':
            print('Could not find gamepad. Reverting to previous control scheme')
        elif status == 'INCOMPATIBLE':
            print('Gamepad is incompatible. Reverting to previous control scheme')
    