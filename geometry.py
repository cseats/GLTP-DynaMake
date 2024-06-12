import numpy as np
import math

# Standard basis X, Y, Z vectors
X = np.array([1, 0, 0])
Y = np.array([0, 1, 0])
Z = np.array([0, 0, 1])

def twoVectorAngle(vec1, vec2):
    """Function to calculate the relative angle between two vectors"""
    return np.arccos( np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)) )

def unitVector(vec):
    """Function to calculate a unit vector with the same orientation as a given vector"""
    return vec / np.linalg.norm(vec)

def calcRZ(alpha):
    """Calculate the Rotational Z operator for a given angle alpha (in radians)"""
    return np.array([   [ np.cos(alpha), -np.sin(alpha), 0 ],
                        [ np.sin(alpha),  np.cos(alpha), 0 ],
                        [             0,              0, 1 ] ])

def calcRY(beta):
    """Calculate the Rotational Y operator for a given angle beta (in radians)"""
    return np.array([   [  np.cos(beta), 0, np.sin(beta) ],
                        [             0, 1,            0 ],
                        [ -np.sin(beta), 0, np.cos(beta) ] ])

def findTransformedBasis(vec):
    """Calculate the planar rotation angle (thetaZ, measured around the untransformed Z axis)
        and planar inclination angle (thetaInc, measured around the transformed Y' axis)
        to align the X axis to a given vector"""
    
    if all([i == 0 for i in vec]): # if input is null vector (i.e. [0, 0, 0])
        return (0, 0)
    elif (vec[0] == 0 and vec[1] == 0 and vec[2] != 0): # if input is parallel to Z axis (i.e. [0, 0, !0])
        return (0, math.pi/2)
    
    if vec[0] == 0 and vec[1] > 0:      # if input is parallel to Y axis with positive Y component (i.e. [0, >0, any])
        thetaZ = math.pi/2
    elif vec[0] == 0 and vec[1] < 0:    # if input is parallel to Y axis with negative Y component (i.e. [0, <0, any])
        thetaZ = 1.5*math.pi
    else:                               # if input is any other vector (i.e. [any, any, any])
        thetaZ = np.arctan(vec[1]/vec[0])

    # Calculate the RZ operator for thetaZ and transform X -> X' axis
    RZ = calcRZ(thetaZ) 
    xPrime = np.matmul(RZ, X) 

    if xPrime[2] == vec[2]: # if input is in XY-plane, return rotated by non-inclined tranformation
        return (thetaZ, 0)
    else:                   # if input is any other vector
        correctionFactor = (vec[2] - xPrime[2])/abs(vec[2] - xPrime[2]) # calculate right-hand rule sign correction
        thetaInc = -twoVectorAngle(xPrime, vec) * correctionFactor # calculate the planar inclination angle
        return (thetaZ, thetaInc)

def transformBasis(theta, inclination):
    """Function to calculate the transformed basis vectors for given planar rotation and planar inclination angles"""

    RZ = calcRZ(theta)          # RZ operator, planar rotation
    RY = calcRY(inclination)    # RY operator, planar inclination
    R = np.matmul(RY, RZ)       # Combined R operator (RY * RZ)
    x = np.matmul(R, X)         # new X' basis vector
    v = np.matmul(R, Y)         # new Y' basis vector

    return (x, v)