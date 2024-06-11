import numpy as np
import math

X = np.array([1, 0, 0])
Y = np.array([0, 1, 0])
Z = np.array([0, 0, 1])

def twoVectorAngle(vec1, vec2):
    return np.arccos( np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)) )

def unitVector(vec):
    return vec / np.linalg.norm(vec)

def calcRZ(alpha):
    return np.array([   [ np.cos(alpha), -np.sin(alpha), 0 ],
                        [ np.sin(alpha),  np.cos(alpha), 0 ],
                        [             0,              0, 1 ] ])

def calcRY(beta):
    return np.array([   [  np.cos(beta), 0, np.sin(beta) ],
                        [             0, 1,            0 ],
                        [ -np.sin(beta), 0, np.cos(beta) ] ])

# def calcRX(gamma): 
#     return np.array([   [  ],
#                         [  ], 
#                         [  ] ])

def findTransformedBasis(vec):
    if all([i == 0 for i in vec]):
        return (0, 0)
    elif (vec[0] == 0 and vec[1] == 0 and vec[2] != 0):
        return (0, math.pi/2)
    
    if vec[0] == 0 and vec[1] > 0:
        thetaZ = math.pi/2
    elif vec[0] == 0 and vec[1] < 0:
        thetaZ = 1.5*math.pi
    else: 
        thetaZ = np.arctan(vec[1]/vec[0])

    RZ = calcRZ(thetaZ)
    xPrime = np.matmul(RZ, X)
    if xPrime[2] == vec[2]:
        return (thetaZ, 0)
    else:
        thetaInc = -twoVectorAngle(xPrime, vec)*(vec[2] - xPrime[2])/abs(vec[2] - xPrime[2])
        return (thetaZ, thetaInc)

def transformBasis(theta, inclination):
    RZ = calcRZ(theta)
    RY = calcRY(inclination)
    R = np.matmul(RY, RZ)
    x = np.matmul(R, X)
    v = np.matmul(R, Y)

    return (x, v)