#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print()
print("ASSEMBLER")
print("---------\n")

# initialize
from collections import namedtuple
__TEXT__ = 0x400000
__DATA__ = 0x10000000
symbols = dict()
data = []
labels = dict()
instrs = []

# file open
import argparse, os
parser = argparse.ArgumentParser()
parser.add_argument("source", type=str,
                    help="MIPS instruction file")
parser.add_argument("-o", "--output", metavar="FILE", type=str,
                    help="write output to FILE")
args = parser.parse_args()
fname = args.source
print(fname)
f = open(fname, 'r')

# first pass
dc = 0
pc = 0
for line in f:
    # skip if blankline or comments
    if line.strip() == '': continue
    if line.strip()[0] == '#': continue

    # clean up instruction
    tokens = line.strip().split()
    for idx, tok in enumerate(tokens[1:-1]):
        tokens[idx+1] = tok.strip(',')

    # detect section
    if '.' == tokens[0][0] and len(tokens) == 1:
        section = tokens[0][1:]
        continue

    ###
    # .data section
    # detect symbol
    if section == 'data':
        if tokens[0][-1] == ':':
            symbols[tokens[0][:-1]] = dc
            data.append(tuple(tokens[1:]))
            dc += 1
        else:
            data.append(tuple(tokens))
            dc += 1
        continue

    ###
    # .text section
    if section == 'text':
        if tokens[0][-1] == ':':
            labels[tokens[0][:-1]] = pc
        else:
            if tokens[0] == 'la':
                # interprete data symbols
                addr = __DATA__ + symbols[tokens[2]] * 4
                print("addr: {0:08x}  {0:032b}".format(addr))
                upper = addr >> 16
                lower = addr % (1<<16)
                # lui upper
                tokens[0] = "lui"
                tokens[2] = str(upper)
                instrs.append(tuple(tokens))
                pc += 1
                # ori lower
                if lower != 0:
                    tokens[0] = "ori"
                    tokens[2] = tokens[1]
                    tokens.append(str(lower))
                    instrs.append(tuple(tokens))
                    pc += 1
            else:
                instrs.append(tuple(tokens))
                pc += 1
        continue
    # end for loop

f.close()
# end first pass

### DEBUG
print("### symbols")
for sym, pos in symbols.items():
    print("{0}\t{1}\t{2}".format(sym, pos, '\t'.join(data[pos])))
print('\n')

print("### data")
for ty, datum in data:
    print("{0}\t{1}".format(ty, datum))
print('\n')

print("### labels")
for lab, loc in labels.items():
    print("{0}\t{1}".format(lab, loc))
print('\n')

print("### instructions")
for instr in instrs:
    print('\t'.join(instr))
print('\n')

print("### total # of instructions = %d" % pc)
print('\n')
### END DEBUG

# second pass
if args.output:
    f = open(args.output, 'w')
else:
    base = os.path.basename(fname)
    fname2 = os.path.splitext(base)[0]
    f = open(fname2+'.o', 'w')
###
# initialization
# instruction types
InstrR = namedtuple('R', 'op rs rt rd shamt funct')
InstrI = namedtuple('I', 'op rs rt immediate')
InstrJ = namedtuple('J', 'op address')
# encoding
def encode(instr):
    if type(instr) == InstrR:
        # ??? should we consider two's complement of shamt?
        return "{0.op:06b}{0.rs:05b}{0.rt:05b}{0.rd:05b}{0.shamt:05b}{0.funct:06b}".format(instr)
    elif type(instr) == InstrI:
        # consider two's complement (immediate)
        if instr.immediate < 0:
            immediate = (1<<16) + instr.immediate
        else:
            immediate = instr.immediate
        return "{0.op:06b}{0.rs:05b}{0.rt:05b}{1:016b}".format(instr, immediate)
    elif type(instr) == InstrJ:
        return "{0.op:06b}{0.address:026b}".format(instr)
    return None
# reference setup
instr_refs = {
        "addiu" : InstrI(9,None,None,None),
        "addu"  : InstrR(0,None,None,None,0,0x21),
        "and"   : InstrR(0,None,None,None,0,0x24),
        "andi"  : InstrI(0xC,None,None,None),
        "beq"   : InstrI(4,None,None,None),
        "bne"   : InstrI(5,None,None,None),
        "j"     : InstrJ(2,None),
        "jal"   : InstrJ(3,None),
        "jr"    : InstrR(0,None,0,0,0,8),
        "lui"   : InstrI(0xF,0,None,None),
        "lw"    : InstrI(0x23,None,None,None),
        "nor"   : InstrR(0,None,None,None,0,0x27),
        "or"    : InstrR(0,None,None,None,0,0x25),
        "ori"   : InstrI(0xD,None,None,None),
        "sltiu" : InstrI(0xB,None,None,None),
        "sltu"  : InstrR(0,None,None,None,0,0x2B),
        "sll"   : InstrR(0,None,None,None,None,0),
        "srl"   : InstrR(0,None,None,None,None,2),
        "sw"    : InstrI(0x2B,None,None,None),
        "subu"  : InstrR(0,None,None,None,0,0x23),
         }
###
# header
f.write("{0:032b}".format(len(instrs)*4))
f.write("{0:032b}".format(len(data)*4))
###
# text
for pc, instr in enumerate(instrs):
    if instr[0] in instr_refs:
        ref = instr_refs[instr[0]]
        if type(ref) == InstrR:
            # instr $d, $s, $t
            # op rs rt rd shamt funct
            rd = int(instr[1][1:])
            # exception: sll srl
            if instr[0] == "sll" or instr[0] == "srl":
                rs = 0
                rt = int(instr[2][1:])
                shamt = int(instr[3])
            else:
                rs = int(instr[2][1:])
                rt = int(instr[3][1:])
                shamt = ref.shamt
            _instr = InstrR(ref.op, rs, rt, rd, shamt, ref.funct)
            print(encode(_instr) + '\t' + '\t'.join(instr))
            f.write(encode(_instr))
        elif type(ref) == InstrI:
            # instr $t, $s, C
            # op rs rt immediate
            rt = int(instr[1][1:])
            # exception: lui
            if instr[0] == "lui":
                rs = 0
                C = int(instr[2],0)
            else:
                rs = int(instr[2][1:])
                # exception: beq bne
                if instr[0] == "beq" or instr[0] == "bne":
                    rs, rt = rt, rs
                # immediate or offset
                if instr[3] in labels:
                    C = labels[instr[3]] - pc - 1
                else:
                    C = int(instr[3],0)
            _instr = InstrI(ref.op, rs, rt, C)
            print(encode(_instr) + '\t' + '\t'.join(instr))
            f.write(encode(_instr))
        else:
            # instr C
            # op address
            address = __TEXT__ + labels[instr[1]] * 4
            _instr = InstrJ(ref.op, (address>>2) % (1<<26))
            print(encode(_instr) + '\t' + '\t'.join(instr))
            f.write(encode(_instr))
    else:
        raise NotImplementedError("Unsupported instruction \"%s\"." % instr[0])
###
# data
for datum in data:
    if datum[0] == ".word":
        value = int(datum[1],0)
        if value < 0: value = (1<<32) - value
        f.write("{:032b}".format(value))

f.close()
