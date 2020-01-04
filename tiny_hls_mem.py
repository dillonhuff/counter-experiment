import os

class Tree(object):
    def __init__(self, data):
        self.data = data
        self.children = []

    def add_child(self, obj):
        self.children.append(obj)

# Control path must be?
class DimQuantity:

    def __init__(self, magnitude, unit):
        self.magnitude = magnitude
        self.unit = unit

    def __repr__(self):
        return str(self.magnitude) + ' ' + self.unit

def quant(mag, unit):
    return DimQuantity(mag, unit)

class ControlNode:

    def __init__(self, name, trip_count, delay_from_parent, ii):
        self.name = name
        self.trip_count = trip_count
        self.delay_from_parent = delay_from_parent
        self.ii = ii

def run_cmd(cmd):
    print('Running:', cmd)
    res = os.system(cmd)
    if (res != 0):
        print( 'ERROR: ' + cmd + ' failed' )
        assert(False)

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
        portstrings = []
        for pt in self.ports:
            portstrings.append(pt_verilog(pt))
        s += 'module {0}'.format(self.name) + ' ' + sep_list('(', ')', ', ', portstrings) + ';\n' + self.body + '\nendmodule\n';
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

    def __repr__(self):
        return 'wr: ' + self.inst + '.' + str(self.port) + '[' + str(self.time) + ']'

class HWWrite:

    def __init__(self, inst, ports, pred, time):
        self.inst = inst
        self.ports = ports
        self.pred = pred
        self.time = time

def sep_list(ld, rd, sep, strings):
    return ld + sep.join(strings) + rd

def build_control_path(event_map, var_bounds, iis):
    pts = [inpt("clk"), inpt('rst'), inpt("en")]
    for e in event_map:
        pts.append(outpt(e))

    ptstrings = []
    for pt in pts:
        ptstrings.append(pt_verilog(pt))

    body = ""
    body += '\treg [31:0] n_valids;\n'
    body += '\treg done;\n'
    decls = []
    for pt in event_map:
        for var_name in event_map[pt].coeffs:
            if not var_name in decls:
                decls.append(var_name)

    for e in event_map:
        body += '\twire {0}_happened;\n'.format(e)

    body += '\n'
    for d in decls:
        body += '\treg [31:0] {0};\n'.format(d)
        body += '\twire {0}_inc_happened;\n'.format(d)
        d_ii = iis[d].magnitude
        body += '\tassign {0}_inc_happened = ({0} * {1} == n_valids) & en & !done;\n'.format(d, d_ii)

    body += '\n'
    # for d in decls:
        # body += '\tassign ' + d[0] + ' = ' + d[1] + ';\n'
    for e in event_map:
        body += '\tassign {0} = {0}_happened;\n'.format(e)

    body += '\n'

    at_max_strings = []
    for d in decls:
        body += '\twire {0}_at_max;\n'.format(d)
        d_max = var_bounds[d].e
        body += '\tassign {0}_at_max = {0} == {1};\n'.format(d, d_max)
        at_max_strings.append('{0}_at_max'.format(d));


    body += '\twire done_this_cycle;\n'
    body += '\tassign done_this_cycle = {0};\n'.format(sep_list('', '', ' & ', at_max_strings))
    
    for e in event_map:
        do_vars = []
        for coeff in event_map[e].coeffs:
            do_vars.append(coeff + '_inc_happened')

        do_str = sep_list('(', ')', ' & ', do_vars)
        
        body += '\tassign {0}_happened = {1} & en & !done;\n'.format(e, do_str)
        # body += '\tassign {0}_happened = ({1} == n_valids) & en & !done;\n'.format(e, str(event_map[e]))
    body += '\n'
    body += "\talways @(posedge clk) begin\n"
    body += '\t\tif (rst) begin\n'
    body += '\t\t\tn_valids <= 0;\n'
    body += '\t\t\tdone <= 0;\n'
    for d in decls:
        body += '\t\t\t{0} <= 0;\n'.format(d)
    body += '\t\tend else if (en & !done) begin\n'
    body += '\t\t\tdone <= done_this_cycle;\n'
    body += '\t\t\tn_valids <= n_valids + 1;\n'
    body += '\t\t\t$display("{0} = %d", {0});\n'.format('n_valids')


    for d in decls:
        body += '\t\t\tif ({0}_inc_happened) begin\n'.format(d)
        body += '\t\t\t\t{0} <= {0} + 1;\n'.format(d)
        body += '\t\t\t\t$display("{0} = %d", {0});\n'.format(d)
        body += '\t\t\tend\n'

    body += '\t\tend\n'
    body += "\tend";

    return Module('control_path', pts, body)

def pt_underscore_str(inst, port):
    if inst == 'world':
        return port
    else:
        return inst + '_' + port
def pt_dot_str(inst, port):
    if inst == 'world':
        return port
    else:
        return inst + '.' + port

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
        return self.reads[-1]

    def write(self, inst, ports, pred, time):
        self.writes.append(HWWrite(inst, ports, pred, time))
        return self.writes[-1]

    def add_instr(self, instr):
        self.instructions.append(instr)

    def add_loop(self, name, m, e):
        self.loop_root.children.append(Tree((name, Interval(m, e))));

    def set_ii(self, name, ii):
        assert(isinstance(ii, DimQuantity))
        self.iis[name] = ii

    def sched_expr(self, loops, d):
        li = LinearExpr()
        for ci in loops:
            li.coeffs[ci] = self.iis[ci]
        li.d = d
        return li

    def loop_bounds(self):
        bounds = {}
        children = [self.loop_root]
        while len(children) > 0:
            print('children: ', children)
            next = children.pop()
            print('next: ', next)

            bounds[next.data[0]] = next.data[1]

            print('Next has', len(next.children), 'children')            
            for c in next.children:
                print('Adding child: ', c)
                children.append(c)
        return bounds

    def synthesize_control_path(self):
        self.event_map = {}
        self.name_map = {}
        wr_num = 0
        for wr in self.writes:
            if wr.pred != "":
                self.name_map[wr] = 'write_' + str(wr_num) + '_en'
                self.event_map['write_' + str(wr_num) + '_en'] = wr.time
                wr_num += 1
        print('name map: ', self.name_map)
        # print('All events that need an enable...')
        # for m in event_map:
            # print('\t', m, ':', event_map[m])
        cp_mod = build_control_path(self.event_map, self.loop_bounds(), self.iis)
        self.add_inst("control_path", cp_mod)
        # print('Control path...')
        print(cp_mod)

        return

    def print_verilog(self):

        # Need to map reads to operations and operations to reads
        ports_to_writes = {}
        for rd in self.writes:
            for pt in rd.ports:
                ports_to_writes[(rd.inst, pt)] = []
        for wr in self.writes:
            for pt in wr.ports:
                val = wr.ports[pt]
                ports_to_writes[(wr.inst, pt)].append((val, wr.time, wr.pred))
        print('All writes:', ports_to_writes)
        istr = ""
        a = []
        # Declare internally defined modules, such as the control path
        for inst in self.instances:
            if not self.instances[inst].name in a:
                if self.instances[inst].body != "":
                    istr += '//{0}\n\n'.format(self.instances[inst].name)
                    istr += str(self.instances[inst])
                    istr += '\n\n'
                    a.append(self.instances[inst].name)

        ports = []
        world = self.instances["world"]
        for pt in world.ports:
            ports.append(pt_verilog(reverse_pt(pt)))

        istr += 'module {0} {1};\n'.format(self.name, sep_list('(', ')', ', ', ports))

        for inst in self.instances:
            if inst != "world":
                connect_strs = []
                for pt in self.instances[inst].ports:
                    istr += '\tlogic {0};\n'.format(pt_name(inst, pt))
                    connect_strs.append('.{0}({1})'.format(pt[0], pt_name(inst, pt)))
                mod = self.instances[inst]
                istr += '\t' + mod.name + ' ' + inst + sep_list('(', ')', ', ', connect_strs) + ';\n'
                if inpt("clk") in mod.ports:
                    istr += '\tassign {0} = clk;\n'.format(pt_name(inst, inpt("clk")))
                if inpt("rst") in mod.ports:
                    istr += '\tassign {0} = rst;\n'.format(pt_name(inst, inpt("rst")))
                if inst == "control_path" and inpt("en") in mod.ports:
                    istr += '\tassign {0} = en;\n'.format(pt_name(inst, inpt("en")))
                istr += '\n'

            all_writes = []
            for rd in self.writes:
                if rd.inst == inst:
                    all_writes.append(rd)
            istr += '\t// ' + str(len(all_writes)) + ' writes to this instance\n'

            all_reads = []
            for rd in self.reads:
                if rd.inst == inst:
                    all_reads.append(rd)

        # Create predicates for writes
        pred_ports_to_writes = {}
        for w in self.writes:
            if w.pred != "":
                if w.pred in pred_ports_to_writes:
                    pred_ports_to_writes[(w.inst, w.pred)].append(w)
                else:
                    pred_ports_to_writes[(w.inst, w.pred)] = [w]

        istr += '\t// Predicates for writes\n'
        for pred_pt_i in pred_ports_to_writes:
            inst = pred_pt_i[0]
            pred_pt = pred_pt_i[1]
            writes = pred_ports_to_writes[pred_pt_i]
            if len(writes) == 1:
                pred_pt_name = pt_underscore_str(inst, pred_pt)
                istr += '\tassign {0} = {1};\n'.format(pred_pt_name, pt_underscore_str('control_path', self.name_map[writes[0]]))
            else:
                print('Error: More than one write uses predicate: {0}'.format(pred_pt))
                assert(False)

        istr += '\t// Writes\n'
        for w in ports_to_writes:
            # TODO: or the predicates for writes
            writes = ports_to_writes[w]
            if len(writes) == 1:
                trigger = writes[0][0]
                istr += '\tassign {0} = {1};\n'.format(pt_underscore_str(w[0], w[1]), pt_underscore_str(trigger.inst, trigger.port));
            else:
                print('Error: More than one write to mem, add multiplexing')
                assert(False)
        istr += 'endmodule\n'

        out = open(self.name + '.v', 'w')
        out.write(istr)
        out.close()

def pt_verilog(pt):
    return ("output" if pt[1] else "input") + " " + pt[0]

def reverse_pt(pt):
    return (pt[0], not pt[1], pt[2])

def outpt(name):
    return (name, True, 1)

def is_out_pt(pt):
    return pt[1]

def pt_name(inst, pt):
    return inst + '_' + pt[0]

def is_in_pt(pt):
    return not pt[1]

def inpt(name):
    return (name, False, 1)

def run_test(mname):
    main_name = "{0}_tb.cpp".format(mname)
    v_command = "verilator -Wno-DECLFILENAME --cc " + mname + ".v builtins.v --exe " + main_name + " --top-module " + mname + " -CFLAGS -std=c++14 -CFLAGS -march=native"
    run_cmd(v_command)

    m_command = "make -C obj_dir -j -f V" + mname + ".mk V" + mname 
    run_cmd(m_command)

    run_cmd('./obj_dir/V' + mname)

mod_name = "passthrough"
p = HWProgram(mod_name);
world = Module("_world_", [outpt("clk"), outpt("rst"), outpt("en"), inpt("valid"), inpt("res"), outpt("in")], "")
p.add_inst("world", world)

p.add_loop("x", 0, 9)
p.set_ii("x", quant(1, "valid"))

wire_read_time = p.sched_expr(["x"], 0)
read_in = p.read("world", "in", wire_read_time)

wire_write_time = p.sched_expr(["x"], 0)
out_write = p.write("world", {"res" : read_in}, "valid", wire_write_time)

p.synthesize_control_path()

print('// Verilog...')
p.print_verilog()

run_test(mod_name)

print('Done.')

mod_name = "downsample_passthrough"

p = HWProgram(mod_name);
world = Module("_world_", [outpt("clk"), outpt("rst"), outpt("en"), inpt("valid"), inpt("res"), outpt("in")], "")
p.add_inst("world", world)

p.add_loop("x", 0, 9)
p.set_ii("x", quant(2, "valid"))

wire_read_time = p.sched_expr(["x"], 0)
read_in = p.read("world", "in", wire_read_time)

wire_write_time = p.sched_expr(["x"], 0)
out_write = p.write("world", {"res" : read_in}, "valid", wire_write_time)

p.synthesize_control_path()

print('// Verilog...')
p.print_verilog()

run_test(mod_name)

# mod_name = "upsample_passthrough"

# p = HWProgram(mod_name);
# world = Module("_world_", [outpt("clk"), outpt("rst"), outpt("en"), inpt("valid"), inpt("res"), outpt("in")], "")
# p.add_inst("world", world)

# # How do we create an upsample?
# #  1. Need to have an outer loop which reads every input, and an inner loop which writes the input twice
# #  2. So maybe we need to have the inner loop with a fractional II?
# #  3. If we have a fractional II what does that mean for the value of the clock?
# p.add_loop("x", 0, 9)
# p.set_ii("x", 2)

# wire_read_time = p.sched_expr(["x"], 0)
# read_in = p.read("world", "in", wire_read_time)

# wire_write_time = p.sched_expr(["x"], 0)
# out_write = p.write("world", {"res" : read_in}, "valid", wire_write_time)

# p.synthesize_control_path()

# print('// Verilog...')
# p.print_verilog()

# run_test(mod_name)
