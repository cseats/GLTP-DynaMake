
var m = Model.Select("");

var dbpcMat = new Material(m, 2, "205_P");
dbpcMat.SetPropertyByName("RO", 1000);
dbpcMat.SetPropertyByName("STIFF", 1e7);
dbpcMat.SetPropertyByName("FRIC", 0.5);
dbpcMat.SetPropertyByName("DAMP", 0.5);
dbpcMat.SetPropertyByName("DMXPZ", 1.0);
dbpcMat.SetPropertyByName("DMXPX", 1.0);
dbpcMat.SetPropertyByName("DMXNX", 1.0);
dbpcMat.SetPropertyByName("DMXPY", 1.0);
dbpcMat.SetPropertyByName("DMXNY", 1.0);
dbpcMat.SetPropertyByName("KROTZ", 1000);

function createRestraints() {
    var f = new File("csys.csv", File.READ);
    var line;
    var splitLine;
    var condition;
    var conditions = {
        "Y": Array(0, 0, 1, 0, 0, 0),
        "GUI_Y": Array(0, 1, 1, 0, 0, 0),
        "ANC": Array(1, 1, 1, 1, 1, 1),
        "+Y": Array(0, 0, 1, 0, 0, 0)
    };

    line = f.ReadLine();
    while ( (line = f.ReadLongLine()) != undefined ) {
        splitLine = line.split(",");
        condition = splitLine[splitLine.length - 1];
        if (condition == "+Y") {
            var x = [Number(splitLine[1]), Number(splitLine[2]), Number(splitLine[3])];
            var v = [Number(splitLine[4]), Number(splitLine[5]), Number(splitLine[6])];
            var z = [x[1]*v[2]-x[2]*v[1], x[2]*v[0]-x[0]*v[2], x[0]*v[1]-x[1]*v[0]];
            var n2 = Node.GetFromID(m, Number(splitLine[0]));
            var n1 = new Node(m, Node.NextFreeLabel(m), n2.x-z[0], n2.y-z[1], n2.z - z[2]);
            var csys = new CoordinateSystem(m, CoordinateSystem.VECTOR, CoordinateSystem.NextFreeLabel(m), x[0], x[1], x[2], v[0], v[1], v[2], n1.nid);
            new Spc(m, n1.nid, csys.cid, ...conditions[condition], Spc.NODE);

            var sect = new Section(m, Section.NextFreeLabel(m), Section.BEAM);
            sect.elform = 6;
            sect.vol = 2e-4;
            sect.iner = 0.01;
            sect.cid = csys.cid;
            sect.scoor = -1;
            var part = new Part(m, Part.NextFreeLabel(m), sect.secid, dbpcMat.mid);
            new Beam(m, Beam.NextFreeLabel(m), part.pid, n1.nid, n2.nid);
        } else {
            var csys = new CoordinateSystem(m, CoordinateSystem.VECTOR, CoordinateSystem.NextFreeLabel(m), Number(splitLine[1]), Number(splitLine[2]), Number(splitLine[3]), Number(splitLine[4]), Number(splitLine[5]), Number(splitLine[6]), Number(splitLine[0]));
            Spc(m, Number(splitLine[0]), csys.cid, ...conditions[condition], Spc.NODE);
        }
    }
}

createRestraints();
