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

def descendants(event_tree):
    children = []
    for c in event_tree.children:
        children.append(c)
    nodes = []
    while len(children) > 0:
        # print('children: ', children)
        next = children.pop()
        nodes.append(next)
        # print('next: ', next)

        # print('Next has', len(next.children), 'children')            
        for c in next.children:
            # print('Adding child: ', c)
            children.append(c)
    return nodes 

def all_nodes(event_tree):
    children = [event_tree]
    nodes = []
    while len(children) > 0:
        # print('children: ', children)
        next = children.pop()
        nodes.append(next)
        # print('next: ', next)

        # print('Next has', len(next.children), 'children')            
        for c in next.children:
            # print('Adding child: ', c)
            children.append(c)
    return nodes 
def tab(i):
    str = ''
    for x in range(0, i):
        str += '\t'
    return str

def assert_str(ind, cond):
    return tab(ind) + 'if (!({0})) begin $display("Assertion FAILED: {0}"); $finish(1); end\n'.format(cond)


def instantiate_mod(mod_name, inst_name, ports):
    port_strings = []
    for pt in ports:
        port_strings.append('.' + pt + '(' + ports[pt] + ')')
    port_binding = sep_list('(', ')', ', ', port_strings)
    return '{0} {1}{2};'.format(mod_name, inst_name, port_binding)

# Add assertions?
def build_control_path(event_tree, event_map, var_bounds, iis, delays):
    print('iis: ', iis)
    predecessors = {}
    nodes = all_nodes(event_tree)
    print(nodes)
    for n in nodes:
        for c in n.children:
            predecessors[c.data[0]] = n

    print('Predecessors:', predecessors)
    print('Delays:', delays)
    # assert(False)

    edges = []
    for n in nodes:
        name = n.data[0]
        if name in iis:
            edges.append((name, name, iis[name]))
        if name in delays:
            if name in predecessors:
                edges.append((predecessors[name].data[0], name, delays[name]))
            else:
                assert(name == "root")
                edges.append(("rst", name, delays[name]))

    print('Edges: ', edges)
    # assert(False)

    pts = [inpt("clk"), inpt('rst'), inpt("en")]
    body = ""
    units = []
    for n in iis:
        val = iis[n]
        name = val.unit
        if name != "clk" and not name in units:
            units.append(name)

    body += '\t// Units of measurement\n'
    body += '\tlogic [31:0] {0}s_since_rst;\n'.format("clk")
    for u in units:
        body += '\tlogic [31:0] {0}s_since_rst;\n'.format(u)
        body += '\tlogic [31:0] {0}s_before_last_clock_edge;\n'.format(u)

    for u in units:
        body += '\tassign {0}s_since_rst = {0}s_before_last_clock_edge + {{31\'d0, ({0} == 1)}};\n'.format(u)

    body += '\n\t// Happening flags\n'
    for n in nodes:
        data = n.data
        name = data[0]
        pts.append(outpt(data[0]))
        body += '\tlogic [31:0] {0}_iter;\n'.format(name)
        body += '\tlogic {0}_happening;\n'.format(name)

        body += '\tlogic {0}_started;\n'.format(name)
        body += '\tlogic {0}_started_in_past_cycle;\n'.format(name)
        body += '\tlogic {0}_starting_this_cycle;\n'.format(name)

        body += '\tlogic {0}_done;\n'.format(name)
        body += '\tlogic {0}_done_this_cycle;\n'.format(name)

        body += '\tlogic {0}_at_trip_count;\n'.format(name)
        if name in delays:
            delay_unit = delays[name].unit
            body += '\tlogic [31:0] {1}s_elapsed_since_{0}_start;\n'.format(name, delay_unit)
            body += '\tlogic [31:0] {1}s_elapsed_between_{0}_start_and_last_clock_edge;\n'.format(name, delay_unit)

        if name in iis:
            delay_unit = iis[name].unit
            if delay_unit != delays[name].unit:
                body += '\tlogic [31:0] {1}s_elapsed_since_{0}_start;\n'.format(name, delay_unit)
                body += '\tlogic [31:0] {1}s_elapsed_between_{0}_start_and_last_clock_edge;\n'.format(name, delay_unit)
        body += '\n'
    
    for n in nodes:
        body += '\tassign {0}_at_trip_count = {0}_iter == {1};\n'.format(n.data[0], n.data[1].e)
        body += '\tassign {0}_started = {0}_starting_this_cycle | {0}_started_in_past_cycle;\n'.format(n.data[0])

        body += '\tassign {0} = {0}_happening;\n'.format(n.data[0])

        child_events = descendants(n)
        children_done_strings = ["1"]
        for c in child_events:
            children_done_strings.append(c.data[0] + '_done_this_cycle')
        body += '\tassign {0}_done_this_cycle = {0}_done | ({1} & {0}_at_trip_count & {0}_happening);\n'.format(n.data[0], sep_list('(', ')', ' & ', children_done_strings))
        name = n.data[0]
        if name == "root":
            body += '\twire seeing_fst_en;\n'
            modstr = instantiate_mod('signal_seen_first', 'seen_en_fst', {"clk" : "clk", "rst" : "rst", "signal" : "en", "seen" : "seeing_fst_en"})
            body += tab(1) + modstr + '\n'
            body += '\tassign {0}_happening = seeing_fst_en;\n'.format(name)
        else:
            pred = predecessors[name]
            pred_name = pred.data[0]
            pred_happened = '{0}_happening'.format(pred_name)

            iiv = iis[name]
            ii = iiv.magnitude
            ii_unit = iiv.unit
            elapsed = '{0}s_elapsed_between_{1}_start_and_last_clock_edge'.format(ii_unit, name)
            body += '\tassign {0}_starting_this_cycle = ({1}_happening);\n'.format(name, pred_name)
            
            if ii_unit == "clk":
                # this event was happening II cycles ago, and !x_at_trip_count
                # II cycles ago
                body += '\twire {0}_ii_done;\n'.format(name)
                modstr = instantiate_mod('n_clks_since_signal #({0})'.format(ii),
                        '{0}_ii_cycles'.format(name),
                        {"clk" : "clk", "rst" : "rst", "signal" : "{0}_happening".format(name),
                            "out" : "{0}_ii_done".format(name)})

                body += '\t' + modstr + '\n'
                # body += '\tassign {0}_happening = {1} | (!{0}_done & (({2} & {0}_iter <= {3})));\n'.format(name, pred_happened, '{0}_ii_done'.format(name), n.data[1].e)
                body += '\tassign {0}_happening = {1} | ((({2} & {0}_iter <= {3})));\n'.format(name, pred_happened, '{0}_ii_done'.format(name), n.data[1].e)
            else:
                body += '\tassign {0}_happening = {1} | (!{0}_done & {4} & ((({2} % {3} == 0) & {0}_started)));\n'.format(name, pred_happened, elapsed, ii, ii_unit)

                # body += '\talways @(*) begin\n'
                # body += '\t\t$display("### Combinational change... {0}");\n'.format(name)
                # body += '\t\t$display("{0}_started = %d", {0}_started);\n'.format(name)
                # body += '\t\t$display("{0}_done = %d", {0}_done);\n'.format(name)
                # body += '\t\t$display("predecessor: ({0}_happening) = %d", {0}_happening);\n'.format(pred_name)
                # body += '\t\t$display("{0}_happening = %d, {0}_started = %d", {0}_happening, {0}_started);\n'.format(name)
                # body += '\tend\n'
                

        body += '\n'


    body += '\n'
    body += "\talways @(posedge clk) begin\n"

    body += '\t\tif (rst) begin\n'
    for n in nodes:
        body += '\t\t\t{0}_iter <= 0;\n'.format(n.data[0])
        body += '\t\t\t{0}_done <= 0;\n'.format(n.data[0])
        body += '\t\t\t{0}_started_in_past_cycle <= 0;\n'.format(n.data[0])
        name = n.data[0]
        if name in iis:
            delay_unit = iis[name].unit
            body += '\t\t\t{1}s_elapsed_between_{0}_start_and_last_clock_edge <= 0;\n'.format(name, delay_unit)

    body += '\n'
    body += '\t\t\tclks_since_rst <= 0;\n'
    body += '\n'
    for u in units:
        body += '\t\t\t{0}s_before_last_clock_edge <= 0;\n'.format(u)
    body += '\t\tend begin\n'
    body += '\n'
    body += '\t\t\tclks_since_rst <= clks_since_rst + 1;\n'
    body += '\n'
    for u in units:
        body += '\t\t\tif ({0}) begin\n'.format(u)
        body += '\t\t\t\t{0}s_before_last_clock_edge <= {0}s_before_last_clock_edge + 1;\n'.format(u)
        body += '\n'
        for n in nodes:
            name = n.data[0]
            if name in iis:
                delay_unit = iis[name].unit
                if delay_unit == u:

                    body += '\t\t\t\tif ({0}_started) begin\n'.format(name)
                    body += '\t\t\t\t\t{1}s_elapsed_between_{0}_start_and_last_clock_edge <= {1}s_elapsed_between_{0}_start_and_last_clock_edge + 1;\n'.format(name, delay_unit)
                    body += '\t\t\t\tend\n'


        body += '\t\t\tend\n'
    body += '\n'
    for n in nodes:
        # body += '\t\t\t$display("{0} = %d", {0});\n'.format(n.data[0])
        # body += '\t\t\t$display("--- {0} Info");\n'.format(n.data[0])
        # body += '\t\t\t$display("{0}_iter      = %d", {0}_iter);\n'.format(n.data[0])
        # body += '\t\t\t$display("{0}_happening = %d", {0}_happening);\n'.format(n.data[0])
        # body += '\t\t\t$display("{0}_done      = %d", {0}_done);\n'.format(n.data[0])

        # body += assert_str(3, '{0}_iter <= {1}'.format(n.data[0], n.data[1].e))
        # body += assert_str(3, '!{0}_done_this_cycle | {0}_at_trip_count'.format(n.data[0]))
        body += '\t\t\tif ({0}_starting_this_cycle) begin\n'.format(n.data[0])
        body += '\t\t\t\t{0}_started_in_past_cycle <= 1;\n'.format(n.data[0])
        body += '\t\t\tend\n'
        body += '\n'
        body += '\t\t\tif ({0}_done_this_cycle) begin\n'.format(n.data[0])
        body += '\t\t\t\t{0}_done <= 1;\n'.format(n.data[0])
        body += '\t\t\tend\n'
        body += '\n'
        # body += '\t\t\tif ({0}_happening & !{0}_at_trip_count) begin\n'.format(n.data[0])
        body += '\t\t\tif ({0}_happening) begin\n'.format(n.data[0])
        body += '\t\t\t\t{0}_iter <= {0}_iter + 1;\n'.format(n.data[0])
        body += '\t\t\tend else if ({0}_starting_this_cycle) begin\n'.format(n.data[0])
        # When we re-start we must be at the trip count of the old loop
        # body += assert_str(4, '{0}_at_trip_count'.format(n.data[0]))
        body += '\t\t\t\t{0}_iter <= 0;\n'.format(n.data[0])
        body += '\t\t\t\t{0}_done <= 0;\n'.format(n.data[0])
        body += '\t\t\tend\n'
        body += '\n'

        body += '\n'

    body += '\n'
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
        self.delays = {}
        self.set_delay("root", quant(1, "en"))
        self.reads = []
        self.writes = []
        self.iis = {}
   
    def set_delay(self, event_name, value):
        self.delays[event_name] = value

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

    def add_sub_loop(self, predecessor, name, m, e):
        nodes = all_nodes(self.loop_root)
        found = False
        for n in nodes:
            if n.data[0] == predecessor:
                n.children.append(Tree((name, Interval(m, e))))
                self.set_delay(name, quant(0, 'en'))
                found = True
                break;
        assert(found)

    def add_loop(self, name, m, e):
        self.loop_root.children.append(Tree((name, Interval(m, e))))
        self.set_delay(name, quant(0, 'en'))

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
                self.name_map[wr] = wr.time
                # 'write_' + str(wr_num) + '_en'
                # self.event_map['write_' + str(wr_num) + '_en'] = wr.time
                self.event_map[wr.time] = wr.time
                wr_num += 1
        print('name map: ', self.name_map)
        # print('All events that need an enable...')
        # for m in event_map:
            # print('\t', m, ':', event_map[m])
        cp_mod = build_control_path(self.loop_root, self.event_map, self.loop_bounds(), self.iis, self.delays)
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
p.set_ii("x", quant(1, "en"))
p.set_delay("x", quant(0, "en"))

read_in = p.read("world", "in", "x")
out_write = p.write("world", {"res" : read_in}, "valid", "x")

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
p.set_ii("x", quant(2, "en"))
p.set_delay("x", quant(0, "en"))

read_in = p.read("world", "in", "x")

out_write = p.write("world", {"res" : read_in}, "valid", "x")

p.synthesize_control_path()

print('// Verilog...')
p.print_verilog()

run_test(mod_name)

mod_name = "upsample_passthrough"

p = HWProgram(mod_name);
world = Module("_world_", [outpt("clk"), outpt("rst"), outpt("en"), inpt("valid"), inpt("res"), inpt("x_valid"), outpt("in")], "")
p.add_inst("world", world)

# How do we create an upsample?
#  1. Need to have an outer loop which reads every input, and an inner loop which writes the input twice
#  2. So maybe we need to have the inner loop with a fractional II?
#  3. If we have a fractional II what does that mean for the value of the clock?
p.add_loop("x", 0, 9)
p.set_ii("x", quant(1, "en"))

p.add_sub_loop("x", "up_sample", 0, 1)
p.set_ii("up_sample", quant(1, "clk"))

read_in = p.read("world", "in", "x")

out_write = p.write("world", {"res" : read_in}, "valid", "up_sample")
out_write = p.write("world", {}, "x_valid", "x")

p.synthesize_control_path()

print('// Verilog...')
p.print_verilog()

run_test(mod_name)
