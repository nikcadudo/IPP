#!/usr/bin/python3
import sys
import argparse
import xml.etree.ElementTree as et
import re

#flags for LF and TF
tf_created = False
lf_created = False

#definiton of custom default value for all variables
var_default_value = "EMPTY"

#dictionary for variables
global_frame = {}
local_frame = {}
temp_frame = {}

#stacks
call_stack = []
frame_stack = []
data_stack = []

#dictionary of used label names and their instruction indexes
labels = {}
#dictionary of already interpreted instructions
instructions = {}
current_instruction_order = 1
instr_order = []
#max instruction order 
MAX_ORDER = 0

#handling script arguments
def parseArgs():
    argc = len(sys.argv)
    if argc < 2 or argc > 3:
        sys.stderr.write("ERROR: Invalid number of parameters")
        sys.exit(10)
    if argc == 2 and "--help" in sys.argv:
        print("HELP")
        sys.exit(0)
    elif argc == 3 and "--help" in sys.argv:
        sys.stderr.write("ERROR: Invalid combination of parameters")
        sys.exit(10)
    elif argc == 2 and ("--source" in sys.argv[1] or "--input" in sys.argv[1]):
        tmp = argparse.ArgumentParser()  
        tmp.add_argument('--source')
        tmp.add_argument('--input')
        args = tmp.parse_args()
    elif argc == 3 and ("--source" in sys.argv[1] or "--source" in sys.argv[2]) and ("--input" in sys.argv[1] or "--input" in sys.argv[2]):
        tmp = argparse.ArgumentParser()  
        tmp.add_argument('--source')
        tmp.add_argument('--input')
        args = tmp.parse_args()
    else:
        sys.stderr.write("ERROR: Invalid parameters")
        sys.exit(10)
    return [args.source, args.input]

def isInstruction(i):
    return re.search("^(MOVE|CREATEFRAME|PUSHFRAME|POPFRAME|DEFVAR|CALL|RETURN|PUSHS|POPS|ADD|SUB|MUL|IDIV|LT|GT|EQ|AND|OR|NOT|INT2CHAR|STRI2INT|READ|WRITE|CONCAT|STRLEN|GETCHAR|SETCHAR|TYPE|LABEL|JUMP|JUMPIFEQ|JUMPIFNEQ|EXIT|DPRINT|BREAK)$", str(i).upper())

def createInstructionClass(i):
    name = str(i.attrib['opcode']).upper()
    if(name == "MOVE"):
        return move(i)
    elif(name == "CREATEFRAME"):
        return createFrame(i)
    elif(name == "PUSHFRAME"):
        return pushFrame(i)
    elif(name == "POPFRAME"):
        return popFrame(i)
    elif(name == "DEFVAR"):
        return defVar(i)
    elif(name == "CALL"):
        return call(i)
    elif(name == "RETURN"):
        return returnInstr(i)
    elif(name == "PUSHS"):
        return pushs(i)
    elif(name == "POPS"):
        return pops(i)
    elif(name == "ADD"):
        return add(i)
    elif(name == "SUB"):
        return sub(i)
    elif(name == "MUL"):
        return mul(i)
    elif(name == "IDIV"):
        return idiv(i)
    elif(name == "LT"):
        return lt(i)
    elif(name == "GT"):
        return gt(i)
    elif(name == "EQ"):
        return eq(i)
    elif(name== "AND"):
        return andInstr(i)
    elif(name == "OR"):
        return orInstr(i)
    elif(name == "NOT"):
        return notInstr(i)
    elif(name == "INT2CHAR"):
        return int2char(i)
    elif(name == "STRI2INT"):
        return stri2int(i)
    elif(name == "READ"):
        return read(i)
    elif(name == "WRITE"):
        return write(i)
    elif(name == "CONCAT"):
        return concat(i)
    elif(name == "STRLEN"):
        return strlen(i)
    elif(name == "GETCHAR"):
        return getChar(i)
    elif(name == "SETCHAR"):
        return setChar(i)
    elif(name == "TYPE"):
        return typeInstr(i)
    elif(name == "LABEL"):
        return label(i)
    elif(name == "JUMP"):
        return jump(i)
    elif(name == "JUMPIFEQ"):
        return jumpIfEq(i)
    elif(name == "JUMPIFNEQ"):
        return jumpIfNeq(i)
    elif(name == "EXIT"):
        return exitInstr(i)
    elif(name == "DPRINT"):
        return dprint(i)
    elif(name == "BREAK"):
        return breakInstr(i)
    else:
        sys.stderr.write("ERROR: Source XML has a bad root element")
        sys.exit(32)

def readSource():
    global MAX_ORDER
    global current_instruction_order
    try:
        tree = et.parse(sourceFile)
    except:
        sys.stderr.write("ERROR: Source file is not parsable")
        sys.exit(31)
    root = tree.getroot()
    if root.tag != "program" or root.attrib['language'].upper() != "IPPCODE20":
        sys.stderr.write("ERROR: Source XML has a bad root element")
        sys.exit(32)
    for instruction in root:
        if instruction.tag != "instruction":
            sys.stderr.write("ERROR: Invalid element")
            sys.exit(32)
        if "opcode" not in instruction.attrib:
            sys.stderr.write("ERROR: Missing opcode")
            sys.exit(32)
        if not isInstruction(instruction.attrib["opcode"].upper()):
            sys.stderr.write("ERROR: Unknown instruction")
            sys.exit(32)
        if "order" not in instruction.attrib:
            sys.stderr.write("ERROR: Missing order")
            sys.exit(32)
        try:
            order = int(instruction.attrib["order"])
        except:
            sys.stderr.write("ERROR: Invalid order")
            sys.exit(32)
        if order < 1:
            sys.stderr.write("ERROR: Invalid order")
            sys.exit(32)
        if str(order) in instructions:
            sys.stderr.write("ERROR: Duplicit instruction order")
            sys.exit(32)
        if order > MAX_ORDER:
            MAX_ORDER = order        
        instr_order.append(order)
    instr_order.sort()
    for i in instr_order:
        current_instruction_order = i
        for o in root.findall('instruction'):
            if o.get('order') == str(i):
                instructions[str(i)] = createInstructionClass(o)

def isVar(arg):
    if re.search("^(GF|LF|TF)@([a-zA-Z]|-|[_\$&%*!?])(\w|-|[_\$&%*!?])*$", str(arg)):
        return True
    else:
        return False

def isConst(arg):
    if re.search("^(true|false)$", str(arg).lower()):
        return True
    elif re.search("^nil$", str(arg)):
        return True
    elif re.search("^(\w|[^(\s)]|\d|\\\\([0-9]{3}))*$", str(arg)):
        return True
    elif re.search("^[+-]?(\d)*$", str(arg)):
        return True
    else:
        return False

def isLabel(arg):
    if re.search("^(([a-zA-Z]|-|[_$&%*!?])([a-zA-Z]|-|[_$&%*!?]|[0-9])*)$", arg):
        return True
    else:
        return False

def isType(arg):
    if re.search("^(int|string|bool|nil)$", arg):
        return True
    else:
        return False

def isInFrame(var):
    var_name = var.split("@", 1)[1]
    var_frame = var.split("@", 1)[0]
    if var_frame == "GF":
        if var_name not in global_frame:
            sys.stderr.write("ERROR: Variable does not exist!")
            sys.exit(54)
    elif var_frame == "LF":
        if not lf_created:
            sys.stderr.write("ERROR: Frame is not created!")
            sys.exit(55)
        if var_name not in local_frame:
            sys.stderr.write("ERROR: Variable does not exist!")
            sys.exit(54)
    elif var_frame == "TF":
        if not tf_created:
            sys.stderr.write("ERROR: Frame is not created!")
            sys.exit(55)
        if var_name not in temp_frame:
            sys.stderr.write("ERROR: Variable does not exist!")
            sys.exit(54)
    return True

def getFrameByName(n):
    if n == "GF":
        return global_frame
    elif n == "LF" and lf_created:
        return local_frame
    elif n == "TF" and tf_created:
        return temp_frame
    else:
        return None

def checkTag(i, count):
    for a in i:
        if a.tag == "arg1":
            tmp = i[0]
            tmp_index = list(i).index(a)
            i[0] = a 
            i[tmp_index] = tmp
        if a.tag == "arg2":
            tmp = i[1]
            tmp_index = list(i).index(a)
            i[1] = a 
            i[tmp_index] = tmp
        if a.tag == "arg3":
            tmp = i[2]
            tmp_index = list(i).index(a)
            i[2] = a 
            i[tmp_index] = tmp
    if count > 0:
        if i[0].tag != "arg1":
            sys.stderr.write("ERROR: Invalid argument tag")
            sys.exit(32)
    if count > 1:
        if i[1].tag != "arg2":
            sys.stderr.write("ERROR: Invalid argument tag")
            sys.exit(32)
    if count > 2:
        if i[2].tag != "arg3":
            sys.stderr.write("ERROR: Invalid argument tag")
            sys.exit(32)
    return i

def changeFrame(oldframe, newframename):
    for i in oldframe:
        i.setFrame(newframename)

#Operands classes
class variable():
    def __init__(self, var):
        #example <arg1 type="var">GF@counter</arg1>
        if var.attrib['type'] == "var":
            self.var_type = "nil"
        else:
            self.var_type = var.attrib['type']
        self.var_name = var.text.split("@", 1)[1] #counter
        self.var_frame = var.text.split("@", 1)[0] #GF
        self.var_value = var_default_value

    def getType(self):
        return self.var_type

    def getName(self):
        return self.var_name

    def getFrame(self):
        return self.var_frame

    def getValue(self):
        return self.var_value

    def setFrame(self, f):
        self.var_frame = f

    def setValue(self, val):
        if val == None:
            self.var_value = ""
        elif val == "true":
            self.var_value = True
        elif val == "false":
            self.var_value = False
        else:
            self.var_value = val

    def setType(self, t):
        self.var_type = t
        if self.var_type == "string":
            matches = re.findall("\\\\[0-9]{3}", self.var_value)
            if matches != None:
                for m in matches:
                    index = self.var_value.index(m)
                    offset = len(m)
                    self.var_value = self.var_value[:index] + chr(int(m[2:])) + self.var_value[(index+offset):]
            self.var_value = str(self.var_value)
        elif self.var_type == "int":
            try:
                self.var_value = int(self.var_value)
            except:
                sys.stderr.write("ERROR: Value is not int")
                sys.exit(32)
        elif self.var_type == "bool":
            try:
                self.var_value = bool(self.var_value)
            except:
                sys.stderr.write("ERROR: Value is not bool")
                sys.exit(32)

class constant():
    def __init__(self, const):
        self.var_type = const.attrib['type']
        if const.text == None:
            self.var_value = ""
        elif const.text == "true":
            self.var_value = True
        elif const.text == "false":
            self.var_value = False
        else:
            self.var_value = const.text
        if self.var_type == "string":
            matches = re.findall("\\\\[0-9]{3}", self.var_value)
            if matches != None:
                for m in matches:
                    index = self.var_value.index(m)
                    offset = len(m)
                    self.var_value = self.var_value[:index] + chr(int(m[2:])) + self.var_value[(index+offset):]
        elif self.var_type == "int":
            try:
                self.var_value = int(self.var_value)
            except:
                sys.stderr.write("ERROR: Value is not int")
                sys.exit(32)
        elif self.var_type == "bool":
            try:
                self.var_value = bool(self.var_value)
            except:
                sys.stderr.write("ERROR: Value is not bool")
                sys.exit(32)

    def getType(self):
        return self.var_type

    def getValue(self):
        return self.var_value

class labelOp():
    def __init__(self, l):
        self.label_name = l
        self.label_index = current_instruction_order
        labels[l] = current_instruction_order

    def getName(self):
        return self.label_name

    def getIndex(self):
        return self.label_index

#INSTRUCTION CLASSES
class move():
    def __init__(self, i):
        self.args = {}
        if i.__len__() != 2:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)

    def run(self):
        val = self.args['arg2'].getValue()
        self.args['arg1'].setValue(val)
        var_type = self.args['arg2'].getType()
        self.args['arg1'].setType(var_type)

class createFrame():
    def __init__(self, i):
        global tf_created
        global temp_frame
        if i.__len__() != 0:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)        
        tf_created = True
        temp_frame = {}

    def run(self):
        return

class pushFrame():
    def __init__(self, i):
        global local_frame
        global tf_created
        global temp_frame
        global lf_created
        if i.__len__() != 0:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        if not tf_created:
            sys.stderr.write("ERROR: Temporary frame is not defined!")
            sys.exit(55)      
        local_frame = temp_frame
        for i in local_frame:
            local_frame[i].setFrame("LF")  
        frame_stack.append(temp_frame)
        lf_created = True
        tf_created = False
        temp_frame = {}
    def run(self):
        return

class popFrame():
    def __init__(self, i):
        if i.__len__() != 0:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)    
        global tf_created
        global temp_frame
        if frame_stack != None:
            if len(frame_stack) > 0:
                temp_frame = frame_stack.pop(-1)
                for i in temp_frame:
                    temp_frame[i].setFrame("TF")
                tf_created = True
            else:
                sys.stderr.write("ERROR: Empty frame stack")
                sys.exit(55)
        else:
            sys.stderr.write("ERROR: No local frame is available!")
            sys.exit(55)

    def run(self):
        return

class defVar():
    def __init__(self, i):
        if i.__len__() != 1:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.name = i[0].text.split("@",1)[1]
        frame = getFrameByName(i[0].text.split("@",1)[0])
        if frame is None:
            sys.stderr.write("ERROR: Frame doesn't exist")
            sys.exit(55)
        if self.name in frame:
            sys.stderr.write("ERROR: Variable name already exists in this frame")
            sys.exit(52)
        else:
            frame[self.name] = variable(i[0])

    def run(self):
        return

class call():
    def __init__(self, i):
        if i.__len__() != 1:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.label_name = i[0].text
        if i[0].text not in labels:
            sys.stderr.write("ERROR: Label does not exist")
            sys.exit(52)
    def run(self):
        global current_instruction_order
        call_stack.append(current_instruction_order+1)
        current_instruction_order = labels[self.label_name] + 1

class returnInstr():
    def __init__(self, i):
        if i.__len__() != 0:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        return
    def run(self):
        global current_instruction_order
        if len(call_stack) > 0:
            current_instruction_order = call_stack.pop(-1)
        else:
            sys.stderr.write("ERROR: No index was stored for return in the call stack")
            sys.exit(56)

class pushs():
    def __init__(self, i):
        if i.__len__() != 1:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        elif isConst(i[0].text):
            self.args['arg1'] = constant(i[0])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
    def run(self):
        data_stack.append(self.args['arg1'])

class pops():
    def __init__(self, i):
        if i.__len__() != 1:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
    def run(self):
        if len(data_stack) > 0:
            item = data_stack.pop(-1)
            self.args['arg1'].setValue(item.getValue())
            self.args['arg1'].setType(item.getType())
        else:
            sys.stderr.write("ERROR: Data stack empty")
            sys.exit(56)

class add():
    def __init__(self, i):
        if i.__len__() != 3:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
        if isVar(i[2].text) and isInFrame(i[2].text):
            tmp = getFrameByName(i[2].text.split("@", 1)[0])
            self.args['arg3'] = tmp[i[2].text.split("@", 1)[1]]
        elif isConst(i[2].text):
            self.args['arg3'] = constant(i[2])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
            
    def run(self):
        if self.args['arg2'].getType() == "int" and self.args['arg3'].getType() == "int":
            val = int(self.args['arg2'].getValue()) + int(self.args['arg3'].getValue())
            self.args['arg1'].setValue(val)
            self.args['arg1'].setType("int")
        else:
            sys.stderr.write("ERROR: Values are not integers")
            sys.exit(53)

class sub():
    def __init__(self, i):
        if i.__len__() != 3:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
        if isVar(i[2].text) and isInFrame(i[2].text):
            tmp = getFrameByName(i[2].text.split("@", 1)[0])
            self.args['arg3'] = tmp[i[2].text.split("@", 1)[1]]
        elif isConst(i[2].text):
            self.args['arg3'] = constant(i[2])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)

    def run(self):
        if self.args['arg2'].getType() == "int" and self.args['arg3'].getType() == "int":
            val = int(self.args['arg2'].getValue()) - int(self.args['arg3'].getValue())
            self.args['arg1'].setValue(val)
            self.args['arg1'].setType("int")
        else:
            sys.stderr.write("ERROR: Values are not integers")
            sys.exit(53)

class mul():
    def __init__(self, i):
        if i.__len__() != 3:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
        if isVar(i[2].text) and isInFrame(i[2].text):
            tmp = getFrameByName(i[2].text.split("@", 1)[0])
            self.args['arg3'] = tmp[i[2].text.split("@", 1)[1]]
        elif isConst(i[2].text):
            self.args['arg3'] = constant(i[2])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)

    def run(self):
        if self.args['arg2'].getType() == "int" and self.args['arg3'].getType() == "int":
            val = int(self.args['arg2'].getValue()) * int(self.args['arg3'].getValue())
            self.args['arg1'].setValue(val)
            self.args['arg1'].setType("int")
        else:
            sys.stderr.write("ERROR: Values are not integers")
            sys.exit(53)

class idiv():
    def __init__(self, i):
        if i.__len__() != 3:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
        if isVar(i[2].text) and isInFrame(i[2].text):
            tmp = getFrameByName(i[2].text.split("@", 1)[0])
            self.args['arg3'] = tmp[i[2].text.split("@", 1)[1]]
        elif isConst(i[2].text):
            self.args['arg3'] = constant(i[2])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)

    def run(self):
        if self.args['arg2'].getType() == "int" and self.args['arg3'].getType() == "int":
            arg3_val = int(self.args['arg3'].getValue())
            if arg3_val == 0:
                sys.stderr.write("ERROR: Division by zero")
                sys.exit(57)
            val = int(self.args['arg2'].getValue()) // arg3_val
            self.args['arg1'].setValue(val)
            self.args['arg1'].setType("int")
        else:
            sys.stderr.write("ERROR: Values are not integers")
            sys.exit(53)

class lt():
    def __init__(self, i):
        if i.__len__() != 3:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
        if isVar(i[2].text) and isInFrame(i[2].text):
            tmp = getFrameByName(i[2].text.split("@", 1)[0])
            self.args['arg3'] = tmp[i[2].text.split("@", 1)[1]]
        elif isConst(i[2].text):
            self.args['arg3'] = constant(i[2])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
    def run(self):
        if self.args['arg2'].getType() == "nil" or self.args['arg3'].getType() == "nil":
            sys.stderr.write("ERROR: Cannot compare a nil like that")
            sys.exit(53)
        elif self.args['arg2'].getType() == self.args['arg3'].getType():
            if self.args['arg2'].getValue() < self.args['arg3'].getValue():
                self.args['arg1'].setValue(True)
                self.args['arg1'].setType("bool")
            else:
                self.args['arg1'].setValue(False)
                self.args['arg1'].setType("bool")
        else:
            sys.stderr.write("ERROR: Values are not the same type")
            sys.exit(53)

class gt():
    def __init__(self, i):
        if i.__len__() != 3:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
        if isVar(i[2].text) and isInFrame(i[2].text):
            tmp = getFrameByName(i[2].text.split("@", 1)[0])
            self.args['arg3'] = tmp[i[2].text.split("@", 1)[1]]
        elif isConst(i[2].text):
            self.args['arg3'] = constant(i[2])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
    def run(self):
        if self.args['arg2'].getType() == "nil" or self.args['arg3'].getType() == "nil":
            sys.stderr.write("ERROR: Cannot compare a nil like that")
            sys.exit(53)
        elif self.args['arg2'].getType() == self.args['arg3'].getType():
            if self.args['arg2'].getValue() > self.args['arg3'].getValue():
                self.args['arg1'].setValue(True)
                self.args['arg1'].setType("bool")
            else:
                self.args['arg1'].setValue(False)
                self.args['arg1'].setType("bool")
        else:
            sys.stderr.write("ERROR: Values are not the same type")
            sys.exit(53)

class eq():
    def __init__(self, i):
        if i.__len__() != 3:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
        if isVar(i[2].text) and isInFrame(i[2].text):
            tmp = getFrameByName(i[2].text.split("@", 1)[0])
            self.args['arg3'] = tmp[i[2].text.split("@", 1)[1]]
        elif isConst(i[2].text):
            self.args['arg3'] = constant(i[2])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
    def run(self):
        if self.args['arg2'].getType() == "nil" or self.args['arg3'].getType() == "nil":
            if self.args['arg2'].getValue() == self.args['arg3'].getValue():
                self.args['arg1'].setValue(True)
                self.args['arg1'].setType("bool")
            else:
                self.args['arg1'].setValue(False)
                self.args['arg1'].setType("bool")
        elif self.args['arg2'].getType() == self.args['arg3'].getType():
            if self.args['arg2'].getValue() == self.args['arg3'].getValue():
                self.args['arg1'].setValue(True)
                self.args['arg1'].setType("bool")
            else:
                self.args['arg1'].setValue(False)
                self.args['arg1'].setType("bool")
        else:
            sys.stderr.write("ERROR: Values are not the same type")
            sys.exit(53)

class andInstr():
    def __init__(self, i):
        if i.__len__() != 3:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
        if isVar(i[2].text) and isInFrame(i[2].text):
            tmp = getFrameByName(i[2].text.split("@", 1)[0])
            self.args['arg3'] = tmp[i[2].text.split("@", 1)[1]]
        elif isConst(i[2].text):
            self.args['arg3'] = constant(i[2])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
    def run(self):
        if self.args['arg2'].getType() == "bool" and self.args['arg3'].getType() == "bool":
            val = bool(self.args['arg2'].getValue()) and bool(self.args['arg3'].getValue())
            self.args['arg1'].setValue(val)
            self.args['arg1'].setType("bool")
        else:
            sys.stderr.write("ERROR: Values are not boolean")
            sys.exit(53)

class orInstr():
    def __init__(self, i):
        if i.__len__() != 3:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
        if isVar(i[2].text) and isInFrame(i[2].text):
            tmp = getFrameByName(i[2].text.split("@", 1)[0])
            self.args['arg3'] = tmp[i[2].text.split("@", 1)[1]]
        elif isConst(i[2].text):
            self.args['arg3'] = constant(i[2])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
    def run(self):
        if self.args['arg2'].getType() == "bool" and self.args['arg3'].getType() == "bool":
            val = bool(self.args['arg2'].getValue()) or bool(self.args['arg3'].getValue())
            self.args['arg1'].setValue(val)
            self.args['arg1'].setType("bool")
        else:
            sys.stderr.write("ERROR: Values are not boolean")
            sys.exit(53)

class notInstr():
    def __init__(self, i):
        if i.__len__() != 2:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
    def run(self):
        if self.args['arg2'].getType() == "bool":
            val = not bool(self.args['arg2'].getValue())
            self.args['arg1'].setValue(val)
            self.args['arg1'].setType("bool")
        else:
            sys.stderr.write("ERROR: Values are not boolean")
            sys.exit(53)

class int2char():
    def __init__(self, i):
        if i.__len__() != 2:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)

    def run(self):
        if self.args['arg2'].getType() == "string" or self.args['arg2'].getType() == "int":
            try:
                uni = int(self.args['arg2'].getValue())
            except:
                sys.stderr.write("ERROR: Symbol is not convertible to integer")
                sys.exit(58)
            try:
                val = chr(uni)
            except:
                sys.stderr.write("ERROR: Index out of range")
                sys.exit(58)
            self.args['arg1'].setValue(val)
            self.args['arg1'].setType("string")
        else:
            sys.stderr.write("ERROR: Symbol is not a correct type")
            sys.exit(53)

class stri2int():
    def __init__(self, i):
        if i.__len__() != 3:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
        if isVar(i[2].text) and isInFrame(i[2].text):
            tmp = getFrameByName(i[2].text.split("@", 1)[0])
            self.args['arg3'] = tmp[i[2].text.split("@", 1)[1]]
        elif isConst(i[2].text):
            self.args['arg3'] = constant(i[2])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
    def run(self):
        try:
            index = int(self.args['arg3'].getValue())
        except:
            sys.stderr.write("ERROR: Value is not integer")
            sys.exit(53)
        string = str(self.args['arg2'].getValue())
        if index < len(string):
            val = string[index]
            self.args['arg1'].setValue(ord(val))
            self.args['arg1'].setType("int")
        else:
            sys.stderr.write("ERROR: Index out of range")
            sys.exit(58)

class read():
    def __init__(self, i):
        if i.__len__() != 2:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isType(i[1].text):
            self.args['arg2'] = i[1].text
        else: 
            sys.stderr.write("ERROR: Unknown type")
            sys.exit(57)
    def run(self):
        if script_args[1] == None:
            try:
                read_input = input().encode('utf8')
            except:
                sys.stderr.write("ERROR: Input error")
                sys.exit(90)
        else:
            try:
                read_input = inputFile.readline()
            except:
                sys.stderr.write("ERROR: Input file error")
                sys.exit(90)
        if self.args['arg2'] == "int":
            try:
                converted = int(read_input)
                self.args['arg1'].setValue(converted)
                self.args['arg1'].setType("int")
            except:
                self.args['arg1'].setValue("nil")
                self.args['arg1'].setType("nil")
        elif self.args['arg2'] == "string":
            try:
                converted = str(read_input.replace('\n', ''))
                self.args['arg1'].setValue(converted)
                self.args['arg1'].setType("string")
            except:
                self.args['arg1'].setValue("nil")
                self.args['arg1'].setType("nil")
        elif self.args['arg2'] == "bool":
            try:
                if str(read_input).upper() == "TRUE":
                    self.args['arg1'].setValue(True)
                    self.args['arg1'].setType("bool")
                else:
                    self.args['arg1'].setValue(False)
                    self.args['arg1'].setType("bool")
            except:
                self.args['arg1'].setValue("nil")
                self.args['arg1'].setType("nil")
        else:
            self.args['arg1'].setValue("nil")
            self.args['arg1'].setType("nil")

class write():
    def __init__(self, i):
        if i.__len__() != 1:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        elif isConst(i[0].text):
            self.args['arg1'] = constant(i[0])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
    def run(self):
        if self.args['arg1'].getType() == "int":
            print(self.args['arg1'].getValue(), end='')
        elif self.args['arg1'].getType() == "string":
            print(self.args['arg1'].getValue(), end='')
        elif self.args['arg1'].getType() == "bool":
            if self.args['arg1'].getValue() == True:
                print("true", end='')
            elif self.args['arg1'].getValue() == False:
                print("false", end='')
        elif self.args['arg1'].getType() == "nil":
            print("", end='')

class concat():
    def __init__(self, i):
        if i.__len__() != 2:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
        if isVar(i[2].text) and isInFrame(i[2].text):
            tmp = getFrameByName(i[2].text.split("@", 1)[0])
            self.args['arg3'] = tmp[i[2].text.split("@", 1)[1]]
        elif isConst(i[2].text):
            self.args['arg3'] = constant(i[2])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
    def run(self):
        if self.args['arg2'].getType() == "string" and self.args['arg3'].getType() == "string":
            val = str(self.args['arg2'].getValue()) + str(self.args['arg3'].getValue())
            self.args['arg1'].setValue(val)
            self.args['arg1'].setType("string")
        else:
            sys.stderr.write("ERROR: Values are not strings")
            sys.exit(53)

class strlen():
    def __init__(self, i):
        if i.__len__() != 2:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)

    def run(self):
        if self.args['arg2'].getType() == "string":
            val = len(str(self.args['arg2'].getValue()))
            self.args['arg1'].setValue(int(val))
            self.args['arg1'].setType("int")
        else:
            sys.stderr.write("ERROR: Value is not string")
            sys.exit(53)

class getChar():
    def __init__(self, i):
        if i.__len__() != 3:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
        if isVar(i[2].text) and isInFrame(i[2].text):
            tmp = getFrameByName(i[2].text.split("@", 1)[0])
            self.args['arg3'] = tmp[i[2].text.split("@", 1)[1]]
        elif isConst(i[2].text):
            self.args['arg3'] = constant(i[2])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)

    def run(self):
        if self.args['arg2'].getType() == "string" and self.args['arg3'].getType() == "int":
            index = int(self.args['arg3'].getValue())
            string = str(self.args['arg2'].getValue())
            if index < 0 or index >= len(string):
                sys.stderr.write("ERROR: Index out of range")
                sys.exit(58)
            else:
                val = string[index]
                self.args['arg1'].setValue(val)
                self.args['arg1'].setType("string")
        else:
            sys.stderr.write("ERROR: Types of arguments are not correct")
            sys.exit(53)

class setChar():
    def __init__(self, i):
        if i.__len__() != 3:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
        if isVar(i[2].text) and isInFrame(i[2].text):
            tmp = getFrameByName(i[2].text.split("@", 1)[0])
            self.args['arg3'] = tmp[i[2].text.split("@", 1)[1]]
        elif isConst(i[2].text):
            self.args['arg3'] = constant(i[2])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)

    def run(self):
        if self.args['arg2'].getType() == "int" and self.args['arg3'].getType() == "string":
            string = str(self.args['arg1'].getValue())            
            index = int(self.args['arg2'].getValue())
            char = str(self.args['arg3'].getValue())
            if index < 0 or index >= len(string):
                sys.stderr.write("ERROR: Index out of range")
                sys.exit(58)
            else:
                tmp = string[:index] + char[0] + string[(index+1):]
                self.args['arg1'].setValue(tmp)
                self.args['arg1'].setType("string")
        else:
            sys.stderr.write("ERROR: Types of arguments are not correct")
            sys.exit(53)

class typeInstr():
    def __init__(self, i):
        if i.__len__() != 2:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        else:
            sys.stderr.write("ERROR: Invalid variable value")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)

    def run(self):
        if self.args['arg2'].getValue() == var_default_value:
            self.args['arg1'].setValue("")
            self.args['arg1'].setType("string")
        elif self.args['arg2'].getType() == "int":
            self.args['arg1'].setValue("int")
            self.args['arg1'].setType("string")
        elif self.args['arg2'].getType() == "bool":
            self.args['arg1'].setValue("bool")
            self.args['arg1'].setType("string")
        elif self.args['arg2'].getType() == "string":
            self.args['arg1'].setValue("string")
            self.args['arg1'].setType("string")
        elif self.args['arg2'].getType() == "nil":
            self.args['arg1'].setValue("nil")
            self.args['arg1'].setType("string")            
        else:
            sys.stderr.write("ERROR: Unknown type of variable")
            sys.exit(53)

class label():
    def __init__(self, i):
        if i.__len__() != 1:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isLabel(i[0].text):
            if i[0].text in labels:
                sys.stderr.write("ERROR: Label already declared")
                sys.exit(52)
            else:
                self.args['arg1'] = i[0].text
                labels[i[0].text] = current_instruction_order
        else:
            sys.stderr.write("ERROR: Invalid label name")
            sys.exit(57)        

    def run(self):
        return

class jump():
    def __init__(self, i):
        if i.__len__() != 1:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isLabel(i[0].text):
            self.args['arg1'] = i[0].text
        else:
            sys.stderr.write("ERROR: Invalid label name")
            sys.exit(57)
            
    def run(self):
        global current_instruction_order
        if self.args['arg1'] not in labels:
            sys.stderr.write("ERROR: Label does not exist")
            sys.exit(52)
        else:
            current_instruction_order = labels[self.args['arg1']]

class jumpIfEq():
    def __init__(self, i):
        if i.__len__() != 3:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isLabel(i[0].text):
            self.args['arg1'] = i[0].text
        else:
            sys.stderr.write("ERROR: Invalid label name")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
        if isVar(i[2].text) and isInFrame(i[2].text):
            tmp = getFrameByName(i[2].text.split("@", 1)[0])
            self.args['arg3'] = tmp[i[2].text.split("@", 1)[1]]
        elif isConst(i[2].text):
            self.args['arg3'] = constant(i[2])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
    def run(self):
        global current_instruction_order
        if self.args['arg1'] not in labels:
            sys.stderr.write("ERROR: Label does not exist")
            sys.exit(52)
        if (self.args['arg2']).getType() == "nil" or self.args['arg3'].getType() == "nil":
            if self.args['arg2'].getValue() == self.args['arg3'].getValue():
                current_instruction_order = labels[self.args['arg1']]
            else:
                return
        elif self.args['arg2'].getType() == self.args['arg3'].getType():
            if self.args['arg2'].getValue() == self.args['arg3'].getValue():
                current_instruction_order = labels[self.args['arg1']]
            else:
                return
        else:
            sys.stderr.write("ERROR: Values are not the same type")
            sys.exit(53)

class jumpIfNeq():
    def __init__(self, i):
        if i.__len__() != 3:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isLabel(i[0].text):
            self.args['arg1'] = i[0].text
        else:
            sys.stderr.write("ERROR: Invalid label name")
            sys.exit(57)
        if isVar(i[1].text) and isInFrame(i[1].text):
            tmp = getFrameByName(i[1].text.split("@", 1)[0])
            self.args['arg2'] = tmp[i[1].text.split("@", 1)[1]]
        elif isConst(i[1].text):
            self.args['arg2'] = constant(i[1])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
        if isVar(i[2].text) and isInFrame(i[2].text):
            tmp = getFrameByName(i[2].text.split("@", 1)[0])
            self.args['arg3'] = tmp[i[2].text.split("@", 1)[1]]
        elif isConst(i[2].text):
            self.args['arg3'] = constant(i[2])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
    def run(self):
        global current_instruction_order
        if self.args['arg1'] not in labels:
            sys.stderr.write("ERROR: Label does not exist")
            sys.exit(52)
        if (self.args['arg2']).getType() == "nil" or self.args['arg3'].getType() == "nil":
            if self.args['arg2'].getValue() != self.args['arg3'].getValue():
                current_instruction_order = labels[self.args['arg1']]
            else:
                return
        elif self.args['arg2'].getType() == self.args['arg3'].getType():
            if self.args['arg2'].getValue() != self.args['arg3'].getValue():
                current_instruction_order = labels[self.args['arg1']]
            else:
                return
        else:
            sys.stderr.write("ERROR: Values are not the same type")
            sys.exit(53)

class exitInstr():
    def __init__(self, i):
        if i.__len__() != 1:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        elif isConst(i[0].text):
            self.args['arg1'] = constant(i[0])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
    def run(self):
        if self.args['arg1'].getType() != "int":
            sys.stderr.write("ERROR: Exit value is not integer")
            sys.exit(57)
        if int(self.args['arg1'].getValue()) >= 0 and int(self.args['arg1'].getValue()) <= 49:
            exit(self.args['arg1'].getValue())
        else:
            sys.stderr.write("ERROR: Exit value out of range")
            sys.exit(57)

class dprint():
    def __init__(self, i):
        if i.__len__() != 1:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        i = checkTag(i, i.__len__())
        self.args = {}
        if isVar(i[0].text) and isInFrame(i[0].text):
            tmp = getFrameByName(i[0].text.split("@", 1)[0])
            self.args['arg1'] = tmp[i[0].text.split("@", 1)[1]]
        elif isConst(i[0].text):
            self.args['arg1'] = constant(i[0])
        else: 
            sys.stderr.write("ERROR: Invalid symbol value")
            sys.exit(57)
    def run(self):
        sys.stderr.write(str(self.args['arg1'].getValue()))

class breakInstr():
    def __init__(self, i):
        if i.__len__() != 0:
            sys.stderr.write("ERROR: Invalid number of arguments")
            sys.exit(32)
        return
    def run(self):
        sys.stderr.write("GLOBAL FRAME\n")
        for g in global_frame:
            sys.stderr.write(global_frame[g].getName() + ": " + global_frame[g].getValue() +"\n")
        sys.stderr.write("LOCAL FRAME\n")
        if not lf_created:
            sys.stderr.write("not initialized\n")
        else:
            for l in local_frame:
                sys.stderr.write(local_frame[l].getName() + ": " + local_frame[l].getValue() +"\n")
        sys.stderr.write("TEMPORARY FRAME\n")
        if not tf_created:
            sys.stderr.write("not initialized\n")
        else:
            for t in temp_frame:
                sys.stderr.write(temp_frame[t].getName() + ": " + temp_frame[t].getValue() + "\n")
        sys.stderr.write("CURRENT INSTRUCTION ORDER: " + str(instr_order[current_instruction_order]) + "\n")
        sys.stderr.write("INSTRUCTIONS DONE: " + str(current_instruction_order + 1) + "\n")

# MAIN 
script_args = parseArgs()
if script_args[0] != None:
    try:
        sourceFile = open(script_args[0], 'r', encoding='utf8')
    except:
        sys.stderr.write("ERROR: Cannot open source file")
        sys.exit(11)
else:
    try:
        sourceFile = open(0, encoding='utf8')
    except:
        sys.stderr.write("ERROR: Cannot read from stdin")
        sys.exit(11)
if script_args[1] != None:
    try:
        inputFile = open(script_args[1], 'r', encoding='utf8')
    except:
        sys.stderr.write("ERROR: Cannot open input file")
        sys.exit(11)
readSource()
index = 0
current_instruction_order = instr_order[index]
while (MAX_ORDER >= current_instruction_order): 
    tmp = current_instruction_order   
    instructions[str(current_instruction_order)].run()
    if tmp == current_instruction_order:
        index = instr_order.index(current_instruction_order) + 1
        if index >= len(instr_order):
            current_instruction_order = MAX_ORDER + 1
        else:
            current_instruction_order = instr_order[index]
exit(0)