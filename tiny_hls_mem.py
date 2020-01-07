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

    def __init__(self, name, ports, body=""):
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

def synch_display_blk(display_str):
    return '\talways @(posedge clk) begin $display({0}); end\n'.format(display_str)

def assert_str(ind, cond):
    return tab(ind) + 'if (!({0})) begin $display("Assertion FAILED: {0}"); $finish(1); end\n'.format(cond)


def instantiate_mod(mod_name, inst_name, ports):
    port_strings = []
    for pt in ports:
        port_strings.append('.' + pt + '(' + ports[pt] + ')')
    port_binding = sep_list('(', ')', ', ', port_strings)
    return '{0} {1}{2};'.format(mod_name, inst_name, port_binding)

def build_control_path(event_tree, var_bounds, iis, delays):
    print('iis: ', iis)
    predecessors = {}
    nodes = all_nodes(event_tree)
    print(nodes)
    for n in nodes:
        for c in n.children:
            predecessors[c.data[0]] = n

    print('Predecessors:', predecessors)
    print('Delays:', delays)

    pts = [inpt("clk"), inpt('rst'), inpt("en")]
    body = '\n\t// Per-Event Control Logic\n'
    for n in nodes:
        data = n.data
        name = data[0]
        assert(name in delays)
        
        pts.append(outpt(data[0]))
        body += '\tlogic {0}_happening;\n'.format(name)
        body += '\tassign {0} = {0}_happening;\n'.format(n.data[0])

        delay_v = delays[name]
        delay_unit = delay_v.unit
        delay = delay_v.magnitude

        if name == "root":
            assert(delay == 1)

            modstr = instantiate_mod('signal_seen_first', 'seen_en_fst', {"clk" : "clk", "rst" : "rst", "signal" : "en", "seen" : "{0}_happening".format(name)})
            body += tab(1) + modstr + '\n'
        else:
            pred = predecessors[name]
            pred_name = pred.data[0]
            pred_happened = '{0}_happening'.format(pred_name)
           
            body += '\twire {0}_to_{1}_delay_sr_out;\n'.format(pred_happened, name)
            en_signal = delay_unit if delay_unit != "clk" else "1'b1"
            new_pred_happened = '{0}_to_{1}_delay_sr_out'.format(pred_happened, name)
            modstr = instantiate_mod('delay_n_ens #(.W(1), .N({0}))'.format(delay),
                    '{0}_to_{1}_delay_sr'.format(pred_name, name),
                    {'clk' : 'clk', 'rst' : 'rst', 'en' : en_signal, 'in' : pred_happened, "out" : new_pred_happened})
            pred_happened = new_pred_happened
            body += '\t{0}\n'.format(modstr)

            iiv = iis[name]
            ii = iiv.magnitude
            ii_unit = iiv.unit
            trip_count = n.data[1].e - n.data[1].s + 1;
           
            if trip_count == 1:
                body += '\tassign {0}_happening = {1};\n'.format(name, pred_happened)
            else:
                ii_en_signal = ii_unit if ii_unit != "clk" else "1'b1"
                modstr = instantiate_mod('count_every_ii_signals #(.N({0}), .II({1}))'.format(trip_count, ii),
                        '{0}_ii_cycles'.format(name),
                        {"clk" : "clk", "rst" : "rst", "start" : pred_happened, "signal" : ii_en_signal,
                            "out" : "{0}_happening".format(name)})

                body += '\t' + modstr + '\n'
        body += '\n'
    body += '\n'

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
        self.extra_verilog = ""

    def assign(self, lhs, rhs):
        self.extra_verilog += '\tassign {0} = {1};\n'.format(lhs, rhs)

    def set_delay(self, event_name, value):
        self.delays[event_name] = value

    def add_inst(self, name, mod):
        self.instances[name] = mod

    def comb_read(self, inst, pt):
        time = "1'b1"
        return read(self, inst, pt, time)

    def read(self, inst, pt, time):
        mod = self.instances[inst]
        found_pt = False
        for other_pt in mod.ports:
            if other_pt[0] == pt:
                found_pt = True
                break
        assert(found_pt)
        self.reads.append(HWRead(inst, pt, time))
        return self.reads[-1]

    def write(self, inst, ports, pred, time):
        self.writes.append(HWWrite(inst, ports, pred, time))
        return self.writes[-1]

    def add_instr(self, instr):
        self.instructions.append(instr)

    def add_sub_event(self, predecessor, name):
        m = 0
        e = 0
        nodes = all_nodes(self.loop_root)
        found = False
        for n in nodes:
            if n.data[0] == predecessor:
                n.children.append(Tree((name, Interval(m, e))))
                self.set_delay(name, quant(0, 'en'))
                found = True
                break;
        assert(found)
        self.set_ii(name, quant(1, 'en'))

    def add_sub_loop(self, predecessor, name, m, e):
        nodes = all_nodes(self.loop_root)
        found = False
        for n in nodes:
            if n.data[0] == predecessor:
                n.children.append(Tree((name, Interval(m, e))))
                self.set_delay(name, quant(0, 'en'))
                self.set_ii(name, quant(1, 'clk'))
                found = True
                break;
        assert(found)

    def add_loop(self, name, m, e):
        self.loop_root.children.append(Tree((name, Interval(m, e))))
        self.set_delay(name, quant(0, 'en'))
        self.set_ii(name, quant(1, 'clk'))

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
        cp_mod = build_control_path(self.loop_root, self.loop_bounds(), self.iis, self.delays)
        self.add_inst("control_path", cp_mod)
        print(cp_mod)

        return

    def whole_module(self):
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
        ports = []
        world = self.instances["world"]
        for pt in world.ports:
            ports.append(reverse_pt(pt))
            # pt_verilog(reverse_pt(pt)))

        # istr += 'module {0} {1};\n'.format(self.name, sep_list('(', ')', ', ', ports))

        for inst in self.instances:
            if inst != "world":
                connect_strs = []
                for pt in self.instances[inst].ports:
                    pt_width = pt[2]
                    istr += '\tlogic [{1} - 1 : 0] {0};\n'.format(pt_name(inst, pt), pt_width)
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
                istr += '\tassign {0} = {1};\n'.format(pred_pt_name, pt_underscore_str('control_path', writes[0].time))
                # self.name_map[writes[0]]))
            else:
                print('Error: More than one write uses predicate: {0}'.format(pred_pt))
                assert(False)

        istr += '\t// Writes\n'
        for w in ports_to_writes:
            # TODO: or the predicates for writes
            print('w: ', ports_to_writes)
            writes = ports_to_writes[w]
            if len(writes) == 1:
                trigger = writes[0][0]
                istr += '\tassign {0} = {1};\n'.format(pt_underscore_str(w[0], w[1]), pt_underscore_str(trigger.inst, trigger.port));
            else:
                istr += '\talways @(*) begin\n'
                for wr in writes:
                    trigger = wr[0]
                    istr += tab(2) + 'if ({0}) begin\n'.format(pt_underscore_str('control_path', trigger.time))
                    istr += tab(3) + '{0} = {1};\n'.format(pt_underscore_str(w[0], w[1]), pt_underscore_str(trigger.inst, trigger.port));
                    istr += tab(2) + 'end\n'
                istr += '\tend\n'
        # istr += 'endmodule\n'

        this_mod = Module(self.name, ports, istr + '\n\t// Extra verilog...\n' + self.extra_verilog)
        return this_mod

    def print_verilog(self):

        out = open(self.name + '.v', 'w')
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

        out.write(istr)
        this_mod = self.whole_module()
        out.write(str(this_mod))
        # out.write(istr)
        out.close()

def pt_verilog(pt):
    return ("output" if pt[1] else "input") + " [{0} - 1 : 0] ".format(pt[2]) + pt[0]

def reverse_pt(pt):
    return (pt[0], not pt[1], pt[2])

def outpt(name, width=1):
    return (name, True, width)

def is_out_pt(pt):
    return pt[1]

def pt_name(inst, pt):
    return inst + '_' + pt[0]

def is_in_pt(pt):
    return not pt[1]

def inpt(name, width=1):
    return (name, False, width)

def run_test(mname):
    main_name = "{0}_tb.cpp".format(mname)
    v_command = "verilator -Wno-DECLFILENAME --cc " + mname + ".v builtins.v --exe " + main_name + " --top-module " + mname + " -CFLAGS -std=c++14 -CFLAGS -march=native"
    run_cmd(v_command)

    m_command = "make -C obj_dir -j -f V" + mname + ".mk V" + mname 
    run_cmd(m_command)

    run_cmd('./obj_dir/V' + mname)

def write_reg(p, inst, value, time):
    p.write(inst, {"d" : value}, "en", time)

def read_reg(p, inst, time):
    return p.read(inst, "q", time)

def add_event_counter(prog, loop_name):
    bounds = prog.loop_bounds()
    trip_count = bounds[loop_name].e - bounds[loop_name].s + 1
    reg = Module("counter #(.MIN(0), .MAX({0}))".format(trip_count - 1),
            [inpt("clk"), inpt("rst"), inpt("en"), inpt("clear"), outpt("out", 32)])
    prog.add_inst(loop_name + '_counter', reg)
    prog.write(loop_name + '_counter', {}, "en", loop_name)
    prog.extra_verilog += '\tassign {0}_clear = ({1} == {2}) & {3};\n'.format(loop_name + '_counter', loop_name + '_counter_out', trip_count - 1, 'control_path_' + loop_name)

def add_reg(prog, name, width):
    reg = Module("register_s #(.WIDTH({0}))".format(width),
            [inpt("clk"), inpt("rst"), inpt("en"), inpt("d", width), outpt("q", width)], "")
    prog.add_inst(name, reg)

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

# Upsample with a delay between the upsampled outputs 

mod_name = "two_II_upsample"

p = HWProgram(mod_name);
world = Module("_world_", [outpt("clk"), outpt("rst"), outpt("en"), inpt("valid"), inpt("res"), inpt("x_valid"), outpt("in")], "")
p.add_inst("world", world)

p.add_loop("x", 0, 9)
p.set_ii("x", quant(1, "en"))

p.add_sub_loop("x", "up_sample", 0, 1)
p.set_ii("up_sample", quant(2, "clk"))

read_in = p.read("world", "in", "x")

out_write = p.write("world", {"res" : read_in}, "valid", "up_sample")
out_write = p.write("world", {}, "x_valid", "x")

p.synthesize_control_path()

print('// Verilog...')
p.print_verilog()

run_test(mod_name)

def register_vectorize_test():
    mod_name = "register_vectorize"

    p = HWProgram(mod_name);
    world = Module("_world_", [outpt("clk"), outpt("rst"), outpt("en"), inpt("valid"), inpt("res_pt", 32), inpt("res_reg", 32), inpt("x_valid"), outpt("in", 32)], "")
    p.add_inst("world", world)

    data = Module("register_32 ", [inpt("clk"), inpt("rst"), inpt("en"), inpt("d", 32), outpt("q", 32)], "")
    p.add_inst("data", data)

    in_pixels = 10
    outer_loops = (in_pixels // 2) - 1
    num_out_vaids = outer_loops

    p.add_loop("x", 0, outer_loops)
    p.set_ii("x", quant(2, "en"))

    p.add_sub_loop("x", "write_to_reg", 0, 0)
    p.set_delay("write_to_reg", quant(0, "en"))
    p.set_ii("write_to_reg", quant(1, "en"))

    p.add_sub_loop("x", "write_to_out", 0, 0)
    p.set_delay("write_to_out", quant(1, "en"))
    p.set_ii("write_to_out", quant(1, "en"))

    read_for_reg = p.read("world", "in", "write_to_reg")

    read_for_out = p.read("world", "in", "write_to_out")
    read_for_reg_val = p.read("data", "q", "write_to_out")

    out_write = p.write("world", {"res_reg" : read_for_reg_val}, "valid", "write_to_out")
    out_write = p.write("world", {"res_pt" : read_for_out}, "", "write_to_out")

    out_write = p.write("world", {}, "x_valid", "x")
    # Set register value
    p.write("data", {"d" : read_for_reg}, "en", "write_to_reg")

    p.synthesize_control_path()

    print('// Verilog...')
    p.print_verilog()

    run_test(mod_name)
    return


def sram_loop_test():

    mod_name = "sram_loop"

    p = HWProgram(mod_name);
    world = Module("_world_", [outpt("clk"), outpt("rst"), outpt("en"), inpt("valid"), inpt("out", 64), inpt("x_valid"), outpt("in", 64), outpt("in_addr", 7)], "")
    p.add_inst("world", world)

    addr_width = 7
    ram = Module("single_port_sram #(.WIDTH(64), .DEPTH(128))", [inpt("clk"), inpt("rst"), inpt("ren"), inpt("wen"), inpt("addr", addr_width), inpt("d", 64), outpt("q", 64)], "")
    p.add_inst("mem", ram)

    add_reg(p, "addr_reg", addr_width)

    p.add_sub_event("root", "write_ram")

    p.add_sub_event("write_ram", "read_ram")
    p.set_delay("read_ram", quant(1, "clk"))

    p.add_sub_event("read_ram", "write_output")
    p.set_delay("write_output", quant(1, "clk"))

    # Read in address and data and write it to the ram 
    read_for_reg = p.read("world", "in", "write_ram")
    read_addr = p.read("world", "in_addr", "write_ram")
    p.write("mem", {"addr" : read_addr, "d" : read_for_reg}, "wen", "write_ram")
    write_reg(p, "addr_reg", read_addr, "write_ram")

    # Start to read the written value from the RAM
    # Note: the address must be saved from the initial value?
    old_addr = read_reg(p, "addr_reg", "read_ram")
    p.write("mem", {"addr" : old_addr}, "ren", "read_ram")

    # Finish by writing the data from the ram to the module output
    mem_output = p.read("mem", "q", "write_output")
    p.write("world", {"out" : mem_output}, "valid", "write_output")

    p.synthesize_control_path()

    print('// Verilog...')
    p.print_verilog()

    run_test(mod_name)
    return

def conv_1_3_vec_test():
    mod_name = "conv_1_3_vec"

    p = HWProgram(mod_name);
    world = Module("_world_",
            [outpt("clk"), outpt("rst"),
                outpt("en"), inpt("valid"), inpt("out", 16*3), outpt("in", 16),
                inpt("producer_r_count", 32), inpt("producer_c_outer_count", 32), inpt("producer_c_inner_count", 32), inpt("producer_r_v"), inpt("producer_c_inner_v"), inpt("producer_c_outer_v"),
                inpt("agg_output_valid"),
                inpt("agg_output_data", 16*4)])
    p.add_inst("world", world)

    addr_width = 7
    ram = Module("single_port_sram #(.WIDTH(64), .DEPTH(128))", [inpt("clk"), inpt("rst"), inpt("ren"), inpt("wen"), inpt("addr", addr_width), inpt("d", 64), outpt("q", 64)])
    p.add_inst("mem", ram)

    agg = Module('serial_to_parallel_rf #(.WIDTH(16), .N_OUTS(4))',
            [inpt("clk"), inpt("rst"), inpt("en"), inpt("in", 16), outpt("out", 64)])
    p.add_inst('aggregator', agg)

    sb = Module('shift_buffer #(.WIDTH(16), .N_ELEMS(4))',
            [inpt("clk"), inpt("rst"), inpt("shift_dir"), inpt("shift_amount", 32),
                inpt("en"), inpt("in", 64), outpt("out", 64)])
    p.add_inst('swizzler', sb)

    # Aggregator input loops
    vec_width = 4
    n_rows = 5
    n_cols_in = 6
    n_cols_outer = n_cols_in // vec_width + 1
    
    p.add_loop("producer_r", 0, n_rows - 1)
    p.set_ii("producer_r", quant(vec_width*n_cols_outer, 'en'))
    
    p.add_sub_loop("producer_r", "producer_c_outer", 0, n_cols_outer - 1)
    p.set_ii("producer_c_outer", quant(vec_width, 'en'))
 
    p.add_sub_loop("producer_c_outer", "producer_c_inner", 0, vec_width - 1)
    p.set_ii("producer_c_inner", quant(1, 'en'))

    p.add_sub_event("producer_c_inner", "read_aggregator_base");
    p.set_delay("read_aggregator_base", quant(vec_width, "en"))

    # 1 clk after the last iteration of producer_c_inner starts
    p.add_sub_event("read_aggregator_base", "read_agg");
    p.set_delay("read_agg", quant(1, "clk"))

    add_event_counter(p, "producer_r")
    add_event_counter(p, "producer_c_outer")
    add_event_counter(p, "producer_c_inner")

    p.assign('producer_r_count', 'producer_r_counter_out')
    p.assign('producer_c_outer_count', 'producer_c_outer_counter_out')
    p.assign('producer_c_inner_count', 'producer_c_inner_counter_out')

    p.assign('producer_r_v', 'control_path_producer_r')
    p.assign('producer_c_outer_v', 'control_path_producer_c_outer')
    p.assign('producer_c_inner_v', 'control_path_producer_c_inner')
    p.assign('agg_output_valid', 'control_path_read_agg')
    p.assign('agg_output_data', 'aggregator_out')

    # Now: Need to write to the aggregate buffer on each valid
    read_input = p.read('world', 'in', 'producer_c_inner')
    p.write('aggregator', {'in' : read_input}, 'en', 'producer_c_inner')

    p.synthesize_control_path()

    print('// Verilog...')
    p.print_verilog()

    run_test(mod_name)
    return

register_vectorize_test()
sram_loop_test()
conv_1_3_vec_test()

