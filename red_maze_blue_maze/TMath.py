#This module just contains some convenient 3D geometric math functions.
#Why did I call it TMath? Well, it started off as a bunch of functions to perform vector 
#math operations on tuples (t for tuple). Then I discovered mathutils Vector class. 
#I kept the name for the historical significance.

import math
import mathutils

#Project(flatten) 3D vector 'a' onto the plane containing vectors 'x' and 'y' (normalizes the result)
def VecToPlane(a,x,y):
    n = x.cross(y)
    n.normalize()
    final = a - (a.dot(n) * n)
    final.normalize()
    return final

#Compose an orientation matrix from X, Y, and Z axes
def MakeMatrix(x,y,z):
    final = [[],[],[]]
    for i in range(len(final)):
        final[i] = [x[i], y[i], z[i]]
    return final

#Interpolate rotation matrices 'a' and 'b' according to factor 'c'
#This method will interpolate from one orientation to another using the LEAST ROTATION possible
#Did I cheat by using the mathutils quaternion class? :)
def MatrixLerp(a,b,c):
    a = a.to_quaternion()
    b = b.to_quaternion()    
    a = a.slerp(b,c)
    a = a.to_matrix()
    return a
    
#Spherically interpolate 3D vectors 'a' and 'b' by factor 'c'(not fully tested)
def VecSlerp(a,b,c):
    angle = c * a.angle(b,0)
    axis = b.cross(a)
    if a.cross(axis).dot(b) < 0:
        angle = -angle
    rotmat = mathutils.Matrix.Rotation(angle, 3, axis)
    a = a * rotmat
    return a

#Given two vectors, 'a' and 'b',  generate a rotation matrix that maps 'a' onto 'b'(not thoroughly tested for all cases- may have errors)
def VecToVecMatrix(a,b):
    angle = a.angle(b)
    perp = a.cross(b)
    if a.cross(perp).dot(b) < 0:
        angle = -angle
    rotmat = mathutils.Matrix.Rotation(angle, 3, perp)
    return rotmat
