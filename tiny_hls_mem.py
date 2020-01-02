class LinearExpr:

    def __init__(self):
        self.coeffs = {}
        self.d = 0

class Interval:

    def __init__(self, s, e):
        self.s = s
        self.e = e

class EventTrigger:

    def __init__(self):
        self.sched = LinearExpr()
        self.variableBounds = {}

class ControlPath:

    def __init__(self, name, triggers):
        self.name = name
        self.eventTriggers = triggers;

class Module:

    def __init__(self, name, ports, body):
        self.name = name;
        self.ports = ports
        self.body = body

class HWVal:

    def __init__(self, instName, portName):
        self.instName = instName
        self.portName = portName

class SWVal:

    def __init__(self, name, hwLoc, time):
        self.name = name
        self.hwLoc = hwLoc
        self.time = time

class HWInstr:

    def __init__(self, name, instance, operands):
        self.name = name
        self.instance = instance
        self.operands = operands

class HWRead:

    def __init__(self, inst, port, time):
        self.inst = inst
        self.port = port
        self.time = time

class HWWrite:

    def __init__(self, inst, ports, pred, time):
        self.inst = inst
        self.ports = ports
        self.pred = pred
        self.time = time

def sep_list(ld, rd, sep, strings):
    return ld + sep.join(strings) + rd

class HWProgram:

    def __init__(self, name):
        self.name = name
        self.instances = {}
        self.loops = {}
        self.reads = []
        self.writes = []

    def add_inst(self, name, mod):
        self.instances[name] = mod

    def read(self, inst, pt, time):
        self.reads.append(HWRead(inst, pt, time))

    def write(self, inst, ports, pred, time):
        self.writes.append(HWWrite(inst, ports, pred, time))

    def add_instr(self, instr):
        self.instructions.append(instr)

    def add_loop(self, name, m, e):
        self.loops[name] = Interval(m, e)

    def sched_expr(self, iis, d):
        li = LinearExpr()
        for ci in iis:
            li.coeffs[ci[1]] = ci[0]
        li.d = d
        return li

    def print_verilog(self):
        ports = []
        world = self.instances["world"]
        for pt in world.ports:
            ports.append(pt_verilog(pt))
        print('module', self.name, sep_list('(', ')', ', ', ports), ';\n')
        print('endmodule\n')

def pt_verilog(pt):
    return ("output" if pt[1] else "input") + " " + pt[0]

def outpt(name):
    return (name, True, 1)

def inpt(name):
    return (name, False, 1)

p = HWProgram('reg_read_10');
world = Module("_world_", [outpt("clk"), outpt("rst"), outpt("valid"), inpt("res"), outpt("in")], "")
p.add_inst("world", world)

reg = Module("reg_1", [inpt("clk"), inpt("rst"), inpt("en"), inpt("d"), outpt("q")], "")
p.add_inst("data", reg)

p.add_loop("x", 0, 10)

# Maybe read_port should create hw values at a given time?
# Q: How to handle efficient predication of operations based on time?
# A:  1. No predication, 1 setter: connect ports statically regardless of time
#     2. Predication, 1 setter: connect all non-pred ports statically and connect control enable to pred port
#     3. No pred, many set: mux based on control path enables, fail if any are not exclusive
#     4. pred, many set: mux based on control path enables, and or together control predicates
# Q: How to generate HWValues for loop index variables generated in the control path?
# A: Just as usual with a control path value?
# set Instructions should set ports to swvalues
# and read instructions should produce hwvalues (and reads generate swvalues?)
wire_read_time = p.sched_expr([(1, "x")], 0)
read_in = p.read("world", "in", wire_read_time)
reg_write = p.write("data", {"q", read_in}, "en", wire_read_time)

wire_write_time = p.sched_expr([(1, "x")], 1)
reg_val = p.read("data", "out", wire_write_time)
out_write = p.write("world", {"res", reg_val}, "", wire_write_time)

print('Verilog...')

p.print_verilog()

print('Done.')
