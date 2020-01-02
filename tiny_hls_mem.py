class LinearExpr:

    def __init__(self):
        self.coeffs = {}
        self.d = 0

    def __repr__(self):
        clist = []
        for c in self.coeffs:
            clist.append(str(self.coeffs[c]) + ' * ' + c)
        return sep_list('', '', ' * ', clist) + ' + ' + str(self.d)

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

class Tree(object):
    def __init__(self, data):
        self.data = data
        self.children = []

    def add_child(self, obj):
        self.children.append(obj)

class HWProgram:

    def __init__(self, name):
        self.name = name
        self.instances = {}
        self.loop_root = Tree(("root", Interval(0, 0)))
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
        self.loop_root.children.append((name, Interval(m, e)))

    def sched_expr(self, iis, d):
        li = LinearExpr()
        for ci in iis:
            li.coeffs[ci[1]] = ci[0]
        li.d = d
        return li

    def synthesize_control_path(self):
        return

    def print_verilog(self):
        # Q: How do we generate the control path for this circuit?
        # Q: How are enables produced?
        # A: Collect all write timings, and generate a name
        #    for each write and a control path for each write?
        #    return the result as a module?
        event_map = {}
        name_map = {}
        wr_num = 0
        for wr in self.writes:
            name_map[wr] = 'write_' + str(wr_num)
            event_map['write_' + str(wr_num)] = wr.time
            wr_num += 1
        print('All events that need an enable...')
        for m in event_map:
            print('\t', m, ':', event_map[m])
        ports = []
        world = self.instances["world"]
        for pt in world.ports:
            ports.append(pt_verilog(reverse_pt(pt)))
        print('module', self.name, sep_list('(', ')', ', ', ports), ';\n')

        for inst in self.instances:
            if inst != "world":
                mod = self.instances[inst]
                print('\t', mod.name, inst, '();')

            all_writes = []
            for rd in self.writes:
                if rd.inst == inst:
                    all_writes.append(rd)
            print('\t', len(all_writes), 'writes to this instance')

            all_reads = []
            for rd in self.reads:
                if rd.inst == inst:
                    all_reads.append(rd)
            print('\t', len(all_reads), 'reads from this instance')
        print('endmodule\n')

def pt_verilog(pt):
    return ("output" if pt[1] else "input") + " " + pt[0]

def reverse_pt(pt):
    return (pt[0], not pt[1], pt[2])

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

wire_read_time = p.sched_expr([(2, "x")], 0)
read_in = p.read("world", "in", wire_read_time)
reg_write = p.write("data", {"q", read_in}, "en", wire_read_time)

wire_write_time = p.sched_expr([(2, "x")], 1)
reg_val = p.read("data", "out", wire_write_time)
out_write = p.write("world", {"res", reg_val}, "", wire_write_time)

p.synthesize_control_path()

print('Verilog...')
p.print_verilog()

print('Done.')
