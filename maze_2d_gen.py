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


class SvGrid(maze_3d.Grid):
    
    def pathMatrices(self):
        """
        outputs: list of mathutils Matrix mats
                 list of integers mask
             
        mats: location and orientation of maze path tiles
        mask: which type of path tile to place    
        """
        mats = []
        mask = []
        for row in self.eachRow():
            for cell in row:                    
                ngh_ID = cell.linkedID() 
                tile_type, Rmat = tiles[ngh_ID]

                Tmat = mu.Matrix.Translation(mu.Vector((cell.row, cell.column, 0.0)))
                mats.append(Tmat * Rmat)
                mask.append(tile_type)                

        return mats, mask


I = mu.Matrix.Identity(4)
R90 = mu.Matrix.Rotation(pi/2.0, 4, 'Z')
R180 = mu.Matrix.Rotation(pi, 4, 'Z')
R270 = mu.Matrix.Rotation(1.5*pi, 4, 'Z')

# The tiles dictionary stores info about which tile to 
# place and what orientation to place it in based on the
# neighbours of each path tile.
# neighbours ID: (tile type, tile rotation matrix)
# the neighbours ID can be found for a path tile by adding up the values
#        2 
#       4#1
#        8
# for those neighbours that are linked 

# the tile types:
# 0 : four way junction
# 1 : three way junction
# 2 : bend
# 3 : straight
# 4 : dead end

tiles = {1: (4, R180),
         2: (4, R90),
         3: (2, R90), 
         4: (4, I),
         5: (3, I),
         6: (2, I),
         7: (1, I),
         8: (4, R270),
         9: (2, R180),
         10: (3, R90),
         11: (1, R90),
         12: (2, R270),
         13: (1, R180),
         14: (1, R270),
         15: (0, I)}

                
def sv_main(rseed=21, width=21, height=11, scale=1.0, braid = 0.0):
    
    in_sockets = [['s', 'rseed', rseed],
                  ['s', 'width', width],
                  ['s', 'height', height],
                  ['s', 'scale', scale],
                  ['s', 'braid', braid]]

    maze_3d.random.seed(rseed)    
    grid=SvGrid(width, height)
    grid=maze_3d.initRecursiveBacktrackerMaze(grid)
    grid.braid(braid)

    print(grid)
    
    mats, mask = grid.pathMatrices()
    
    #scale locations
    for m in mats:
        for i in range(3):
           m[i][3] = m[i][3] * scale
    
    mat_out =  Matrix_listing(mats)
    
    out_sockets = [
        ['m', 'matrices', mat_out],
        ['s', 'mask', [mask]]      
    ]

    return in_sockets, out_sockets 
