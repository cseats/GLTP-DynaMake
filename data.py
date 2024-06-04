import os
import pandas as pd

def getData(nodePath, restraintPath):
    nodesDF = pd.read_csv(nodePath)
    restraintDF = pd.read_csv(restraintPath)

    return [nodesDF, restraintDF]