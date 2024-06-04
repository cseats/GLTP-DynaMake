
var m = Model.Select("");

var flag = AllocateFlag();
m.ClearFlag(flag);

let ns = Set.GetFromID(m, 1, Set.NODE);
ns.SetFlag(flag);
m.PropagateFlag(flag);
let nodes = Node.GetFlagged(m, flag);
m.ClearFlag(flag);

function beamPlanarOrientation(m, beam) {
    let n1 = Node.GetFromID(m, beam.n1);
    let n2 = Node.GetFromID(m, beam.n2);
    let vec = [n2.x-n1.x, n2.y-n1.y, n2.z-n1.z];
    if (vec[0] == 0 && vec[1] == 0) {
        return null;
    }
    return Math.atan(vec[1]/vec[0]);
}

for (var i=0; i<nodes.length; i++) {
    let beams = Array();
    let xrefs = nodes[i].Xrefs();
    for (var j=0; j<xrefs.numtypes; j++) {
        let t = xrefs.GetType(j);
        let num = xrefs.GetTotal(t);
        for (var k=0; k<num; k++) {
            beams.push(xrefs.GetItemID(t, k));
        }
    }

    for (var j=0; j<beams.length; j++) {
        beams[j] = Beam.GetFromID(m, beams[j]);
    }

    let orientations = Array();
    for (var j=0; j<beams.length; j++) {
        let orientation = beamPlanarOrientation(m, beams[j]);
        orientations.push(orientation);
    }
    orientations = orientations.filter(x => x);
    let avg_theta;
    if (orientations.length == 0) avg_theta = 0;
    else avg_theta = orientations.reduce((a, b) => a + b )/orientations.length;

    Message(avg_theta);

    let xVec = [
        Math.cos(avg_theta),
        Math.sin(avg_theta),
        0
    ];
    let yVec = [
        -Math.sin(avg_theta),
        Math.cos(avg_theta),
        0
    ];
    Message(xVec, yVec);
    let csys = CoordinateSystem(m, CoordinateSystem.VECTOR, CoordinateSystem.NextFreeLabel(m), xVec[0], xVec[1], xVec[2], yVec[0], yVec[1], yVec[2], nodes[i].nid);
    Spc(m, nodes[i].nid, csys.cid, 0, 1, 1, 0, 0, 0, Spc.NODE);
}