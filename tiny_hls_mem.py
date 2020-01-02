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

class HWProgram:

    def __init__(self):
        self.instances = {}
        self.loops = {}
        self.instructions = []

    def add_inst(self, name, mod):
        self.instances[name] = mod

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

def outpt(name):
    return (name, True, 1)

def inpt(name):
    return (name, False, 1)

p = HWProgram();
world = Module("_world_", [outpt("clk"), outpt("rst"), outpt("valid"), inpt("res"), outpt("in")], "")
p.add_inst("world", world)

reg = Module("reg_1", [inpt("clk"), inpt("rst"), inpt("d"), outpt("q")], "")
p.add_inst("data", reg)

p.add_loop("x", 0, 10)

# Create a time for the operation, then create a swvalue from the port value we are reading
# and the operation time, then create an instruction that uses that and the reg?
wire_read_time = p.sched_expr([(1, "x")], 0)
in_wire = HWVal("world", "in")
in_val = SWVal("wire_val", in_wire, wire_read_time)

write_reg = HWInstr("write", "data", [in_wire])

p.add_instr(write_reg)

out_set_time = p.sched_expr([(1, "x")], 1)
out_wire = HWVal("world", "res")
read_reg = HWInstr("read", "data", [])

write_out = HWInstr("write_pt_res", "world", [read_reg])

print('Done.')



