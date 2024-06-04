import data
import utils.dynaCon as dyna
import utils.dynaUtil as util

import os
import numpy as np
import math
import Oasys.PRIMER

CONVERT_FACTOR = 0.0254
NODE_SETS = {"GUI": 1, "Y": 2, "+Y": 3, "ANC": 4}

def initializePart(m):
    mat = Oasys.PRIMER.Material(m, 1, "001")
    mat.SetPropertyByName("RO", 7850)
    mat.SetPropertyByName("E", 2e11)
    mat.SetPropertyByName("PR", 0.3)
    section = Oasys.PRIMER.Section(m, 1, Oasys.PRIMER.Section.BEAM)
    section.elform = 1
    section.cst = 1.0
    section.ts1 = 0.762
    section.ts2 = 0.762
    section.tt1 = 0.73025
    section.tt2 = 0.73025
    Oasys.PRIMER.Part(m, 1, section.secid, mat.mid)

def createGeometry(m, dfNode):
    nodes_created = []
    for row in dfNode.itertuples():
        n1 = int(row.FROM_NODE)
        n2 = int(row.TO_NODE)
        if not n1 in nodes_created: Oasys.PRIMER.Node(m, n1, int(row.FROM_NODE_X)*CONVERT_FACTOR, int(row.FROM_NODE_Y)*CONVERT_FACTOR, int(row.FROM_NODE_Z)*CONVERT_FACTOR, 0)
        if not n2 in nodes_created: Oasys.PRIMER.Node(m, n2, int(row.TO_NODE_X)*CONVERT_FACTOR, int(row.TO_NODE_Y)*CONVERT_FACTOR, int(row.TO_NODE_Z)*CONVERT_FACTOR, 0)
        nodes_created.extend([n1, n2])
        Oasys.PRIMER.Beam(m, Oasys.PRIMER.Beam.NextFreeLabel(m), 1, n1, n2)

def createNodeSets(m, dfRest, nodeSets):
    for row in dfRest.itertuples():
        nid = int(row.NODE_NUM)
        if row.TYPE == "+Y" and dfRest[(dfRest["NODE_NUM"]==row.NODE_NUM) & (dfRest["TYPE"] == "GUI")].shape[0] >= 1:
            nodeSets["Y"].Add(nid)
        else:
            nodeSets[row.TYPE].Add(nid)
    
    return nodeSets

def createRestraints(m, nodeSets):
    Oasys.PRIMER.Spc(m, NODE_SETS["Y"], 0, 0, 0, 1, 0, 0, 0, Oasys.PRIMER.Spc.SET) # Set vertical SPC (Y)
    Oasys.PRIMER.Spc(m, NODE_SETS["ANC"], 0, 1, 1, 1, 1, 1, 1, Oasys.PRIMER.Spc.SET) # Set fully anchored (ANC)
    # nodeSets = createRestraintGUI(m, nodeSets)
    nodeSets = createRestraintPY(m, nodeSets)
    
    return nodeSets

def createRestraintPY(m, nodeSets):
    mat = Oasys.PRIMER.Material(m, Oasys.PRIMER.Material.NextFreeLabel(m), "205_P")
    mat.SetPropertyByName("RO", 1000)
    mat.SetPropertyByName("STIFF", 1e7)
    mat.SetPropertyByName("FRIC", 0.3)
    mat.SetPropertyByName("DAMP", 0.5)
    [mat.SetPropertyByName(param, 1.0) for param in ["DMXPZ", "DMXPX", "DMXNX", "DMXPY", "DMXNY"]]
    mat.SetPropertyByName("KROTZ", 1000)
    section = Oasys.PRIMER.Section(m, Oasys.PRIMER.Section.NextFreeLabel(m), Oasys.PRIMER.Section.BEAM)
    section.elform = 6
    section.scoor = -1
    section.vol = 2e-4
    section.iner = 0.01
    part = Oasys.PRIMER.Part(m, Oasys.PRIMER.Part.NextFreeLabel(m), section.secid, mat.mid)
    flag = Oasys.PRIMER.AllocateFlag()
    m.ClearFlag(flag)
    nodeSets["+Y"].SetFlag(flag)
    m.PropagateFlag(flag)
    nodes = Oasys.PRIMER.Node.GetFlagged(m, flag)
    m.ClearFlag(flag)
    
    nodeSets["+Y"].Empty()
    for node in nodes:
        n1 = Oasys.PRIMER.Node(m, Oasys.PRIMER.Node.NextFreeLabel(m), node.x, node.y, node.z-0.04)
        nodeSets["+Y"].Add(n1.nid)
        Oasys.PRIMER.Beam(m, Oasys.PRIMER.Beam.NextFreeLabel(m), part.pid, n1.nid, node.nid)

    Oasys.PRIMER.Spc(m, NODE_SETS["+Y"], 0, 1, 1, 1, 1, 1, 1, Oasys.PRIMER.Spc.SET)

    return nodeSets

def createRestraintGUI(m, nodeSets):
    # Flag nodes in GUI node set
    flag = Oasys.PRIMER.AllocateFlag()
    m.ClearFlag(flag)
    nodeSets["GUI"].SetFlag(flag)
    m.PropagateFlag(flag)
    nodes = Oasys.PRIMER.Node.GetFlagged(m, flag)
    m.ClearFlag(flag)

    # Loop through nodes
    for node in nodes:

        # Collect beams which use the node
        beams = []
        xrefs = node.Xrefs()
        for t in range(xrefs.numtypes):
            ref_type = xrefs.GetType(t)
            if ref_type == "BEAM":
                num = xrefs.GetTotal(ref_type)
                for ref in range(num):
                    beams.append(xrefs.GetItemID(ref_type, ref))

        # Compute the average planar orientation of the collected beams
        beams = [Oasys.PRIMER.Beam.GetFromID(m, id) for id in beams]
        orientations = [beamPlanarOrientation(m, beam) for beam in beams]
        if all([o is None for o in orientations]):  theta_avg = 0
        else:                                       theta_avg = np.mean([o for o in orientations if o is not None])

        # Transform local axes to average beam orientation
        A = np.array([[math.cos(theta_avg), -math.sin(theta_avg), 0],
                      [math.sin(theta_avg),  math.cos(theta_avg), 0],
                      [                  0,                    0, 1]])
        x_vec = np.matmul(A, np.array([1, 0, 0]))
        y_vec = np.matmul(A, np.array([0, 1, 0]))
        # print(theta_avg, list(x_vec), list(y_vec))

        # Build coordinate system and SPC
        details = {
            "cid": int(Oasys.PRIMER.CoordinateSystem.NextFreeLabel(m)),
            # "cid": 1,
            # "cx": [1, 0, 0],
            # "cv": [0,1,0],
            "cv": list(y_vec),
            "cx": list(x_vec),
            # "nid": 1,
            "heading": f"Node {node.nid} CSYS",
            "nid": int(node.nid),
            "option": int(Oasys.PRIMER.CoordinateSystem.VECTOR),
        }
        
        # csys = Oasys.PRIMER.CoordinateSystem(m, details)
        # Oasys.PRIMER.Spc(m, node.nid, csys.cid, 0, 1, 0, 0, 0, 0, Oasys.PRIMER.Spc.NODE)

        Oasys.PRIMER.Spc(m, node.nid, 1, 0, 1, 0, 0, 0, 0, Oasys.PRIMER.Spc.NODE)

    return nodeSets

def beamPlanarOrientation(m, beam):
    n1 = Oasys.PRIMER.Node.GetFromID(m, beam.n1)
    n2 = Oasys.PRIMER.Node.GetFromID(m, beam.n2)
    vec = [n2.x-n1.x, n2.y-n1.y, n2.z-n1.z]
    if vec[0:2] == [0,0]:
        return None
    return math.atan(vec[1]/vec[0])

def main():
    curDir = os.path.abspath(os.path.dirname(__file__))
    dataDir = os.path.join(curDir, 'inputs')
    outDir = os.path.join(curDir, 'output')
    nodePath = os.path.join(dataDir, 'INPUT_NODAL_COORDINATES.csv')
    restraintPath = os.path.join(dataDir, 'INPUT_RESTRAINTS.csv')
    
    dfNode, dfRest = data.getData(nodePath, restraintPath)
    
    dyna.connect2Primer()
    
    m = Oasys.PRIMER.Model()
    # c = Oasys.PRIMER.CoordinateSystem(m, {'option': Oasys.PRIMER.CoordinateSystem.VECTOR, 'cid': 400, 'cx': [50, 50, 0], 'cv': [10, -20, 0], 'nid': 10003, 'heading': 'Test csys vector'})
    
    nodeSets = { key: Oasys.PRIMER.Set(m, value, Oasys.PRIMER.Set.NODE, f"NODE RESTRAINT: {key}") for key, value in {"GUI": 1, "Y": 2, "+Y": 3, "ANC": 4}.items() }
    
    initializePart(m)
    createGeometry(m, dfNode)
    nodeSets = createNodeSets(m, dfRest, nodeSets)
    nodeSets = createRestraints(m, nodeSets)

    util.saveModel(os.path.join(outDir, 'pipe.key'), m)


if __name__ == '__main__':
    main()
    # curDir = os.path.abspath(os.path.dirname(__file__))
    # dataDir = os.path.join(curDir, 'inputs')
    # outDir = os.path.join(curDir, 'output')
    # nodePath = os.path.join(dataDir, 'INPUT_NODAL_COORDINATES.csv')
    # restraintPath = os.path.join(dataDir, 'INPUT_RESTRAINTS.csv')
    
    # dfNode, dfRest = data.getData(nodePath, restraintPath)

    # df = dfRest[dfRest["TYPE"] == "+Y"]
    # overlap = dfRest[(dfRest["NODE_NUM"].isin(df["NODE_NUM"])) & (dfRest["TYPE"] == "GUI")]
    # print(overlap.shape)