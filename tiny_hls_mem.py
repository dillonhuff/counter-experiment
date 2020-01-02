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
        self.instructions = []

    def add_inst(self, name, mod):
        self.instances[name] = mod

    def add_instruction(self, instr):
        self.actions.append(instr)

def outpt(name):
    return (name, True, 1)

def inpt(name):
    return (name, False, 1)

p = HWProgram();
world = Module("_world_", [outpt("clk"), outpt("rst"), outpt("valid"), inpt("res"), outpt("in")], "")

### What do I want to do?
###  - Create a HWProgram
###  - Create a register module inside of it
###  - Create an action that reads the module in a loop
###  - Create an action that writes the module in a loop
###  - Test the output 
###  - Later: Test a wide single port SRAM
###  - Much later: Test aggregator + wide SRAM + swizzle
