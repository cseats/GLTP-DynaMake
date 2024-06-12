import data
import utils.dynaCon as dyna
import utils.dynaUtil as util

import os
import numpy as np
import pandas as pd
import Oasys.PRIMER

from geometry import findTransformedBasis, transformBasis, unitVector

CONVERT_FACTOR = 0.0254
NODE_SETS = {"GUI": 1, "Y": 2, "+Y": 3, "ANC": 4}

def initializePart(m):
    """Function to initialize the matrial, section, and part for the input geometry"""

    # Elastic steel material
    mat = Oasys.PRIMER.Material(m, 1, "001")
    mat.SetPropertyByName("RO", 7850)
    mat.SetPropertyByName("E", 2e11)
    mat.SetPropertyByName("PR", 0.3)

    # Section for 762mm (30") outer diameter with 15.875mm (0.625") thickness
    section = Oasys.PRIMER.Section(m, 1, Oasys.PRIMER.Section.BEAM)
    section.elform = 1
    section.cst = 1.0
    section.ts1 = 0.762
    section.ts2 = 0.762
    section.tt1 = 0.73025
    section.tt2 = 0.73025

    Oasys.PRIMER.Part(m, 1, section.secid, mat.mid)

def createGeometry(m, dfNode):
    """Function to create the geometry (nodes/beams) and assign to created Part"""

    nodes_created = []
    # Loop through rows in DataFrame
    for row in dfNode.itertuples():
        # Extracting IDs for n1 and n2 of beams
        n1 = int(row.FROM_NODE) 
        n2 = int(row.TO_NODE)

        # Check that nodes have not already been created
        if not n1 in nodes_created: Oasys.PRIMER.Node(m, n1, int(row.FROM_NODE_X)*CONVERT_FACTOR, int(row.FROM_NODE_Y)*CONVERT_FACTOR, int(row.FROM_NODE_Z)*CONVERT_FACTOR)
        if not n2 in nodes_created: Oasys.PRIMER.Node(m, n2, int(row.TO_NODE_X)*CONVERT_FACTOR, int(row.TO_NODE_Y)*CONVERT_FACTOR, int(row.TO_NODE_Z)*CONVERT_FACTOR)

        # Add nodes to register, calculated third node location and create beam
        nodes_created.extend([n1, n2])
        n3 = calcThirdNode(m, n1, n2)
        Oasys.PRIMER.Beam(m, Oasys.PRIMER.Beam.NextFreeLabel(m), 1, n1, n2, n3.nid)

def calcThirdNode(m, n1, n2):
    """Function to create the third node based on a 10% beam length lever arm"""

    [n1, n2] = [Oasys.PRIMER.Node.GetFromID(m, n) for n in [n1, n2]]
    vec = [n2.x - n1.x, n2.y - n1.y, n2.z - n1.z]
    theta, inc = findTransformedBasis(vec)
    x, v = transformBasis(theta, inc)
    z = np.cross(x, v)
    n3 = [n1.x, n1.y, n1.z] + 0.1*np.linalg.norm(vec)*unitVector(z)
    return Oasys.PRIMER.Node(m, Oasys.PRIMER.Node.NextFreeLabel(m)+100000, n3[0], n3[1], n3[2])

def createNodeSets(m, dfRest):
    """Function to separate restraint types into unique sets, and add them to nodes sets"""

    # Find unique restraint type sets
    unique_nodes = dfRest["NODE_NUM"].unique()
    df = pd.DataFrame(columns=["type"], index=[int(n) for n in unique_nodes])
    for n in unique_nodes:
        sub_df = dfRest[dfRest["NODE_NUM"] == n]
        df.at[n, "type"] = "_".join(sorted(sub_df["TYPE"].to_list()))
    
    # Create node sets for the unique sets, replacing (GUI with +Y) with (GUI with Y)
    df = df.replace({"+Y_GUI": "GUI_Y", "GUI_+Y": "GUI_Y"})
    nodeSets = {}
    for i, t in enumerate(df["type"].unique()):
        sub_df = df[df["type"] == t]
        nodeSets[t] = Oasys.PRIMER.Set(m, i+1, Oasys.PRIMER.Set.NODE, f"NODE RESTRAINT: {t}")
        for node in sub_df.index:
            nodeSets[t].Add(int(node))
        
    return nodeSets

def getAttachedBeams(m, node):
    """Function to find the attached beams to a given node"""

    # Loop through XRefs and append Beam IDs to list
    beams = []
    xrefs = node.Xrefs()
    for i in range(xrefs.numtypes):
        t = xrefs.GetType(i)
        if t == "BEAM":
            num = xrefs.GetTotal(t)
            for j in range(num):
                beams.append(xrefs.GetItemID(t, j))
    
    # Return list of Beam Objects based on Beam IDs found in XRefs
    return [Oasys.PRIMER.Beam.GetFromID(m, i) for i in beams]

def calculateCoordinateSystems(m, nodeSets):
    """Function to calculated and create coordinate systems data (x, v) for the restraint types. 
    This is exported to CSV to be read by JavaScript due to bug in Python API which is preventing
    CoordinateSystem creation."""

    flag = Oasys.PRIMER.AllocateFlag()
    m.ClearFlag(flag)
    nodeCSYS = []

    # Loop through nodeSets
    for key, ns in nodeSets.items():
        ns.SetFlag(flag)
        m.PropagateFlag(flag)
        nodes = Oasys.PRIMER.Node.GetFlagged(m, flag)
        m.ClearFlag(flag)

        # Loop through nodes in nodeSet
        for node in nodes:
            beams = getAttachedBeams(m, node) # Find beams attached to 'node'
            thetas = []
            inclinations = []

            # Loop through beams to find their planar rotations (theta) and planar inclination (inc)
            for beam in beams:
                n1 = Oasys.PRIMER.Node.GetFromID(m, beam.n1)
                n2 = Oasys.PRIMER.Node.GetFromID(m, beam.n2)
                if n1.x < n2.x: beamVec = np.array([ n2.x-n1.x, n2.y-n1.y, n2.z-n1.z ])
                else:           beamVec = np.array([ n1.x-n2.x, n1.y-n2.y, n1.z-n2.z ])
                theta, inc = findTransformedBasis(beamVec)
                thetas.append(theta)
                inclinations.append(inc)

            # Average the list of beam thetas and inclinations
            avgTheta = np.mean(thetas)
            avgInclination = np.mean(inclinations)

            # Calculate the new basis vectors of the rotated coordinate system (aligns local X axis with beam longitudinal axis)
            x, v = transformBasis(avgTheta, avgInclination)

            # Create row specifying centroid node, rotated basis vectors, and restraint node set
            nodeCSYS.append({"nid": node.nid, "xx": x[0], "xy": x[1], "xz": x[2], "vx": v[0], "vy": v[1], "vz": v[2], "ns": key})

    # Create and save DataFrame to CSV for reading in JavaScript
    df = pd.DataFrame(nodeCSYS)
    df.to_csv("csys.csv", index=False)

def main():
    """Main function for building GLTP model"""

    # Build paths
    curDir = os.path.abspath(os.path.dirname(__file__))
    dataDir = os.path.join(curDir, 'inputs')
    outDir = os.path.join(curDir, 'output')
    nodePath = os.path.join(dataDir, 'INPUT_NODAL_COORDINATES.csv')
    restraintPath = os.path.join(dataDir, 'INPUT_RESTRAINTS.csv')
    
    # Load input data
    dfNode, dfRest = data.getData(nodePath, restraintPath)

    # Connect to Primer session and start new model
    dyna.connect2Primer()
    m = Oasys.PRIMER.Model()
         
    initializePart(m) # Create pipeline part
    createGeometry(m, dfNode) # Create the geometry for the pipeline
    nodeSets = createNodeSets(m, dfRest) # Create nodeSets for unique restraint conditions
    calculateCoordinateSystems(m, nodeSets) # Create and store the coordinate system data for restraint conditions

    Oasys.PRIMER.RunScript("createRestraints.js") # Run JavaScript for creating coordinate systems and applying nodal restraint conditions (DUE TO PYTHON BUG)

    util.saveModel(os.path.join(outDir, 'pipe.key'), m) # Save model to outputs directory

if __name__ == '__main__':
    main()
    