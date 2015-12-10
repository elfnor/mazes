#!/usr/bin/env python

# started as  gist from https://gist.github.com/samisalkosuo/77bd95f605fc41dc7366
# adapted for use in Blender Sverchok
# 3D diagonal classes added

#Some mazes classes translated from Ruby 
#from book "Mazes for Programmers" by Jamis Buck.
#https://pragprog.com/book/jbmaze/mazes-for-programmers

import random

class Cell:
    
    def __init__(self,row,column):
        self.row=row
        self.column=column
        self.neighborKeys = ('north', 'east', 'south', 'west')
        self.neighborDirns = dict(zip(self.neighborKeys, ((-1, 0), (0, 1), (1, 0), (0, -1))))
        self.neighborDict = dict.fromkeys(self.neighborKeys)
        self.links=dict()

    def link(self,cell,bidi=True):
        self.links[cell] = True
        if bidi==True:
            cell.link(self,False)
        return self

    def unlink(self,cell,bidi=True):
        try:
            del self.links[cell]
        except KeyError:
            pass
        if bidi==True:
            cell.unlink(self, False)
        return self

    def getLinks(self):
        return self.links.keys()
    
    def linked(self,cell):
        return cell in self.links

    def neighbors(self):
        """
        returns list of neighbors that exist
        """
        neighborList = [cell for k, cell in self.neighborDict.items() if cell]        
        return neighborList

    def getDistances(self):
        distances=Distances(self)
        frontier=[]
        frontier.append(self)
        while len(frontier)>0:
            newFrontier=[]
            for cell in frontier:
                for linked in cell.getLinks():
                    if distances.getDistanceTo(linked) is None:
                        dist=distances.getDistanceTo(cell)
                        distances.setDistanceTo(linked,dist+1)
                        newFrontier.append(linked)
            frontier=newFrontier
        return distances

    def linkedID(self):
        """
        returns an integer representing which neighbors are linked
        this is binary,  self.neighborKeys[0] is LSB
        self.neighborKeys[-1] is MSB
        """        
        ngh = [self.linked(self.neighborDict[dirn]) for dirn in self.neighborKeys ]   
        nghID = sum( 2**i*b for i, b in enumerate(ngh))
        return nghID
        
    def __str__(self):       
        nghID = self.linkedID()
        output="Cell[%d,%d], Linked neighbors ID:%d " % (self.row,self.column, nghID)
        return output

class Distances:

    def __init__(self,rootCell):
        self.rootCell=rootCell
        self.cells=dict()
        self.cells[self.rootCell]=0

    def getDistanceTo(self,cell):
        return self.cells.get(cell,None)

    def setDistanceTo(self,cell,distance):
        self.cells[cell]=distance

    def getCells(self):
        return self.cells.keys()

    def isPartOfPath(self,cell):
        return self.cells.has_key(cell)

    def __len__(self):
        return len(self.cells.keys())

    def pathTo(self,goal):
        current=goal
        breadcrumbs = Distances(self.rootCell)
        breadcrumbs.setDistanceTo(current,self.cells[current])

        while current is not self.rootCell:
            for neighbor in current.getLinks():
                if self.cells[neighbor] < self.cells[current]:
                    breadcrumbs.setDistanceTo(neighbor,self.cells[neighbor])
                    current=neighbor
                    break
        return breadcrumbs


class Grid:

    def __init__(self,rows,columns,cellClass=Cell):
        self.CellClass=cellClass
        self.rows=rows
        self.columns=columns
        self.grid=self.prepareGrid()
        self.distances=None
        self.configureCells()

    def prepareGrid(self):
        rowList=[]
        for i in range(self.rows):
            columnList=[]
            for j in range(self.columns):
                columnList.append(self.CellClass(i,j))
            rowList.append(columnList)
        return rowList

    def eachRow(self):
        for row in self.grid:
            yield row

    def eachCell(self):
        for row in self.grid:
            for cell in row:
                yield cell      

    def configureCells(self):
        for cell in self.eachCell():
           row=cell.row
           col=cell.column
           for dirn in cell.neighborDirns:
                cell.neighborDict[dirn] = self.getNeighbor(row + cell.neighborDirns[dirn][0],
                                            col + cell.neighborDirns[dirn][1])        
            
    def getCell(self,row,column):
        return self.grid[row][column]

    def getNeighbor(self,row,column):
        if not (0 <= row < self.rows):
            return None
        if not (0 <= column < self.columns):
            return None
        return self.grid[row][column]

    def size(self):
        return self.rows*self.columns

    def randomCell(self):
        row=random.randint(0, self.rows-1)
        column = random.randint(0, self.columns - 1)
        return self.grid[row][column]

    def contentsOf(self,cell):
        return "   "

    def __str__(self):
        return self.asciiStr()

    def unicodeStr(self):
        pass

    def asciiStr(self):
        output = "+" + "---+" * self.columns + "\n"
        for row in self.eachRow():
            top = "|"
            bottom = "+"
            for cell in row:
                if not cell:                
                    cell=Cell(-1,-1)
                body = "%s" % self.contentsOf(cell)
                if cell.linked(cell.neighborDict['east']):
                    east_boundary=" "
                else:
                    east_boundary="|"

                top = top+ body + east_boundary
                if cell.linked(cell.neighborDict['south']):
                    south_boundary="   "
                else:
                    south_boundary="---"
                corner = "+"
                bottom =bottom+ south_boundary+ corner
            
            output=output+top+"\n"
            output=output+bottom+"\n"
        return output

    def deadends(self):
        """
        returns a list of maze deadends
        """        
        ends = [cell for cell in self.eachCell() if len(cell.links) == 1 ]
        return ends
        
    def braid(self, p=1.0):
        """
        Add links between dead ends (only one neighbour) and a neighbouring cell
        p is the proportion (approx) of dead ends that are culled. Default p=1.0 removes 
        them all. 
        Linkind dead ends produces loops in the maze.
        Prefers to link to another dead end if possible
        """       
        
        random.shuffle(self.deadends())
        for cell in self.deadends():
            if (len(cell.links) == 1) and (random.random() < p):
                #its still a dead end, ignore some if p < 1
                # find neighbours not linked to cell
                unlinked = [ngh for ngh in cell.neighbors() if not(cell.linked(ngh))]
                #find unlinked neighbours that are also dead ends
                best = [ngh for ngh in unlinked if len(ngh.links) == 1]
                if len(best) == 0:
                    best = unlinked
                ngh = random.choice(best)    
                cell.link(ngh)
        
class DistanceGrid(Grid):

    #def __init__(self,rows,columns,cellClass=Cell):
    #    super(Grid, self).__init__(rows,columns,cellClass)

    def contentsOf(self,cell):

        if  self.distances.getDistanceTo(cell) is not None and self.distances.getDistanceTo(cell) is not None:
            n=self.distances.getDistanceTo(cell)
            return "%03d" % n
        else:
            return "   " #super(Grid, self).contentsOf(cell)

## 3D maze neighbours are defined as 
# 4 cells on same level, 
# 4 cells above
# 4 cells below

class Cell3dDiag(Cell):
    
    def __init__(self, level, row, column):
        self.level = level
        Cell.__init__(self, row, column)
        self.neighborKeys = ('north', 'east', 'south', 'west',
                             'northUp', 'eastUp', 'southUp', 'westUp',
                             'northDown', 'eastDown', 'southDown', 'westDown')
        self.neighborDirns = dict(zip(self.neighborKeys,
                                      ((0,-1, 0), (0, 0, 1), (0, 1, 0), (0, 0, -1),
                                       (1,-1, 0), (1, 0, 1), (1, 1, 0), (1, 0, -1),
                                       (-1,-1, 0), (-1, 0, 1), (-1, 1, 0), (-1, 0, -1) )))
                                       
        self.neighborDict = dict.fromkeys(self.neighborKeys)  

    def __str__(self):       
        nghID = self.linkedID()
        output="Cell[%d, %d, %d], Linked neighbors ID:%d " % (self.level, self.row,self.column, nghID)
        return output              
        
class Grid3dDiag(Grid):
    
    def __init__(self, levels, rows, columns):
        self.levels = levels
        Grid.__init__(self, rows, columns, cellClass = Cell3dDiag)
        
    def prepareGrid(self):
        """
        grid is a triple nested list of cells
        """
        levelList=[]
        for h in range(self.levels):
            rowList = []
            for i in range(self.rows):
                columnList=[]
                for j in range(self.columns):
                    columnList.append(self.CellClass(h, i, j))
                rowList.append(columnList)
            levelList.append(rowList)
        return levelList
     
    def eachLevel(self):
        for level in self,grid:
            yield level
    
    def eachRow(self):
        for level in self.grid:
            for row in level:
                yield row 
            
    def eachCell(self):
        for level in self.grid:
            for row in level:
                for cell in row:
                    yield cell 
    
    def getCell(self,level, row, column):
        return self.grid[level][row][column]

    def getNeighbor(self,level, row, column):
        """
        defines borders by returning None outside grid
        """
        if not (0 <= level < self.levels):
            return None        
        if not (0 <= row < self.rows):
            return None
        if not (0 <= column < self.columns):
            return None      
        return self.grid[level][row][column]    
        
    def configureCells(self):
        """
        set up neighbours, defines edges
        """
        for cell in self.eachCell():
           level = cell.level
           row=cell.row
           col=cell.column
           for dirn in cell.neighborDirns:
                cell.neighborDict[dirn] = self.getNeighbor(
                                            level + cell.neighborDirns[dirn][0],
                                            row + cell.neighborDirns[dirn][1],
                                            col + cell.neighborDirns[dirn][2])  

    def size(self):
        return self.columns * self.rows * self.columns

    def randomCell(self):
        level = random.randint(0, self.levels - 1)
        row = random.randint(0, self.rows - 1)
        column = random.randint(0, self.columns - 1)
        return self.grid[level][row][column] 
            
## carving functions

def initRecursiveBacktrackerMaze(grid):
    stack = [] 
    stack.append(grid.randomCell())

    while len(stack)>0: 
        current = stack[-1]
        neighbors=[]
        for n in current.neighbors():
            if len(n.getLinks())==0:
                neighbors.append(n)

        if len(neighbors)==0:
            stack.pop()
        else:
            neighbor = random.choice(neighbors)
            current.link(neighbor) 
            stack.append(neighbor) 

    return grid


if __name__ == "__main__": 

    grid=Grid3dDiag(4, 4, 4)
    #grid = Grid(10,10)
    grid=initRecursiveBacktrackerMaze(grid)

    print(grid.size())
    
    #print(grid)


