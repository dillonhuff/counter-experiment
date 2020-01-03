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

    def __repr__(self):
        s = ''
        s += 'module {0}'.format(self.name) + ' ' + sep_list('(', ')', ', ', self.ports) + ';\n' + self.body + '\nendmodule\n';
        return s

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

def build_control_path(event_map):
    pts = [inpt("clk"), inpt('rst'), inpt("valid")]
    for e in event_map:
        pts.append(outpt(e))

    print('event map: ', e)
    ptstrings = []
    for pt in pts:
        ptstrings.append(pt_verilog(pt))

    body = ""
    body += '\treg [31:0] n_valids;\n'
    decls = []
    for pt in event_map:
        for var_name in event_map[pt].coeffs:
            if not var_name in decls:
                decls.append(var_name)

    for d in decls:
        body += '\treg [31:0] {0};\n'.format(d)
    # for d in decls:
        # body += '\tassign ' + d[0] + ' = ' + d[1] + ';\n'
    body += "\talways @(posedge clk) begin\n"
    body += '\t\tif (rst) begin\n'
    body += '\t\t\tn_valids <= 0;\n'
    for d in decls:
        body += '\t\t\t{0} <= 0;\n'.format(d)
    body += '\t\tend else if (valid) begin\n'
    body += '\t\t\tn_valids <= n_valids + 1;\n'
    body += '\t\tend\n'
    body += "\tend";

    return Module('control_path', ptstrings, body)

class HWProgram:

    def __init__(self, name):
        self.name = name
        self.instances = {}
        self.loop_root = Tree(("root", Interval(0, 0)))
        self.reads = []
        self.writes = []
        self.iis = {}

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

    def set_ii(self, name, ii):
        self.iis[name] = ii

    def sched_expr(self, loops, d):
        li = LinearExpr()
        for ci in loops:
            li.coeffs[ci] = self.iis[ci]
        li.d = d
        return li

    def synthesize_control_path(self):
        event_map = {}
        name_map = {}
        wr_num = 0
        for wr in self.writes:
            if wr.pred != "":
                name_map[wr] = 'write_' + str(wr_num) + '_en'
                event_map['write_' + str(wr_num) + '_en'] = wr.time
                wr_num += 1
        print('All events that need an enable...')
        for m in event_map:
            print('\t', m, ':', event_map[m])
        cp_mod = build_control_path(event_map)
        self.add_inst("control_path", cp_mod)
        print('Control path...')
        print(cp_mod)

        return

    def print_verilog(self):
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
p.set_ii("x", 2)

wire_read_time = p.sched_expr(["x"], 0)
read_in = p.read("world", "in", wire_read_time)
reg_write = p.write("data", {"q", read_in}, "en", wire_read_time)

wire_write_time = p.sched_expr(["x"], 1)
reg_val = p.read("data", "out", wire_write_time)
out_write = p.write("world", {"res", reg_val}, "", wire_write_time)

p.synthesize_control_path()

print('Verilog...')
p.print_verilog()

print('Done.')
