"""
Sverchok scripted node for simple 2D maze generation
elfnor.com 2015

maze library by Sami Salkosuo
https://gist.github.com/samisalkosuo/77bd95f605fc41dc7366

following "Mazes for Programmers" 
https://pragprog.com/book/jbmaze/mazes-for-programmers
"""
import mathutils as mu
from sverchok.data_structure import Matrix_listing

import maze_3d

from math import pi

pathDict = {'north': (pi, 5, 0.0, 1),
            'east': (pi/2.0, 5, pi/2.0, 1), 
            'south': (0.0, 5, 0.0, 1), 
            'west' : (3.0*pi/2.0, 5, 3.0 * pi/2.0, 1),
            'northUp': (pi, 6, pi, 2), 
            'eastUp' : (pi/2.0, 6, pi/2.0, 2), 
            'southUp': (0.0, 6, 0.0, 2),
            'westUp': (3.0*pi/2.0, 6, 3.0*pi/2.0, 2),
            'northDown': (pi, 7, 0.0, 2),
            'eastDown': (pi/2.0, 7, 3.0*pi/2.0, 2 ), 
            'southDown': (0.0, 7, pi, 2), 
            'westDown' : (3.0*pi/2.0, 7, pi/2.0, 2 )}

class SvGrid(maze_3d.Grid3dDiag):
    
    def pathMatrices(self):
        """
        outputs: list of mathutils Matrix mats
                 list of integers mask
             
        mats: location and orientation of maze path tiles
        mask: which type of path tile to place    
        """
        mats = []
        mask = []
        # platform matrices
        for cell in self.eachCell():
            m = mu.Matrix.Identity(4)
            m[0][3] = cell.row
            m[1][3] = cell.column
            m[2][3] = cell.level
            mats.append(m)
            mask.append(0)
            
        # links matrices
        for cell, dirn, typeID  in self.eachEdge():
            # need a lookup table for all combinations of dirn and type ID
            if typeID == 2:
                #edge
                zrot = pathDict[dirn][0]
                m = mu.Matrix.Rotation(zrot, 4, 'Z')
                m[0][3] = cell.row
                m[1][3] = cell.column
                m[2][3] = cell.level
                mats.append(m)
                mask.append(pathDict[dirn][1])
            else:
                #internal path or gap
                zrot = pathDict[dirn][2]
                m = mu.Matrix.Rotation(zrot, 4, 'Z')
                m[0][3] = cell.row + 0.5 * cell.neighborDirns[dirn][1]
                m[1][3] = cell.column + 0.5 * cell.neighborDirns[dirn][2]
                m[2][3] = cell.level + 0.5 * cell.neighborDirns[dirn][0]
                mats.append(m)
                if typeID == 0:
                    mask.append(pathDict[dirn][3]) 
                else:
                    mask.append(pathDict[dirn][3] + 2) 
                
            
        return mats, mask
                
def sv_main(rseed=21, sizeX=4, sizeY=4, sizeZ=4, scaleXY=1.0, scaleZ=1.0, braid = 0.0):
    
    in_sockets = [['s', 'rseed', rseed],
                  ['s', 'size X', sizeX],
                  ['s', 'size Y', sizeY],
                  ['s', 'size Z', sizeZ],  
                  ['s', 'scale XY', scaleXY],
                  ['s', 'scale Z', scaleZ],
                  ['s', 'braid', braid]]

    maze_3d.random.seed(rseed)    
    grid=SvGrid(sizeZ, sizeX, sizeY)
    grid=maze_3d.initRecursiveBacktrackerMaze(grid)
    grid.braid(braid)

    #print(grid)
    
    mats, mask = grid.pathMatrices()
    
    #scale locations
    for m in mats:
        for i in range(2):
           m[i][3] = m[i][3] * scaleXY
        m[2][3] = m[2][3] * scaleZ
    
    mat_out =  Matrix_listing(mats)
    
    out_sockets = [
        ['m', 'matrices', mat_out],
        ['s', 'mask', [mask]]      
    ]

    return in_sockets, out_sockets 
