import data
import utils.dynaCon as dyna
import utils.dynaUtil as util

import os
import Oasys.PRIMER





def createNode(m, dfNode,nodes,nType):
    
    x = dfNode[f'{nType}_NODE_X']*.0254
    y = dfNode[f'{nType}_NODE_Y']*.0254
    z = dfNode[f'{nType}_NODE_Z']*.0254
    id = dfNode[f'{nType}_NODE']
    Oasys.PRIMER.Node(m,int(id),x,y,z,0)
    
    nodes[id] = [x,y,z]   
    return nodes


def createBeam(m, id,n1,n2,part):
    
    b = Oasys.PRIMER.Beam(m, id, part, n1, n2 )#, 3)
    pass

def createRestraint():
    pass

def createSection():
    pass

def createMaterial():
    pass

def createPart():
    pass



def main():
    curDir = os.path.abspath(os.path.dirname(__file__))
    dataDir = os.path.join(curDir,'inputs')
    outDir = os.path.join(curDir,'output')
    
    nodePath = os.path.join(dataDir,'INPUT_NODAL_COORDINATES.csv')
    restraintPath = os.path.join(dataDir,'INPUT_RESTRAINTS.csv')
    
    
    dfNode,dfRest = data.getData(nodePath,restraintPath)
    
    connection = dyna.connect2Primer()
    
    m = Oasys.PRIMER.Model()
    
    # createSection()
    # createMaterial()
    # createPart()
    
    nodes = {}
    for indx,row in dfNode.iterrows():
        # print(indx)
        # print(type(indx))
        # print('---------------')
        n1 = int(row['FROM_NODE'])
        n2 = int(row['TO_NODE'])
        
        if not n1 in nodes:
            nodes = createNode(m,row,nodes,"FROM")
        if not n2 in nodes:
            nodes = createNode(m,row,nodes,"TO")
            
        createBeam(m, n1=n1, n2=n2, id=indx+1,part=10)
    
    util.saveModel(os.path.join(outDir,'pipe.key'),m)


main()