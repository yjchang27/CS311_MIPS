#!/usr/bin/env python3
# -*- coding: utf-8 -*-

print()
print("ASSEMBLER")
print("---------\n")

# initialize
from collections import namedtuple
symbols = dict()
data = []
labels = dict()
instrs = []

# file open
fname = "example2.s"
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
            instrs.append(tuple(tokens))
            pc += 1
            if tokens[0] == 'la':
                tokens[0] = 'la2'
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
### END DEBUG

# second pass
f = open(fname[:-2]+'.my.o', 'w')
###
# initialization
# instruction types
InstrR = namedtuple('R', 'op rs rt rd shamt funct')
InstrI = namedtuple('I', 'op rs rt immediate')
InstrJ = namedtuple('J', 'op address')
# encoding
def encode(instr):
    if type(instr) == InstrR:
        return "{0.op:06b}{0.rs:05b}{0.rt:05b}{0.rd:05b}{0.shamt:05b}{0.funct:06b}".format(instr)
    elif type(instr) == InstrI:
        # !!! should consider two's complement
        if instr.immediate < 0:
            return "{0.op:06b}{0.rs:05b}{0.rt:05b}{1:016b}".format(instr, (2<<15) + instr.immediate)
        return "{0.op:06b}{0.rs:05b}{0.rt:05b}{0.immediate:016b}".format(instr)
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
for instr in instrs:
    if instr[0] in instr_refs:
        print(instr_refs[instr[0]])
    else:
        print(instr[0])
###
# data
for datum in data:
    if datum[0] == ".word":
        f.write("{:032b}".format(int(datum[1],0)))
