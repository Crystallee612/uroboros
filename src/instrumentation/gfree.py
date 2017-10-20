import os
import time
import random
from disasm import Types
from struct import pack, unpack
from instrumentation import inlining
from utils.ail_utils import ELF_utils, get_loc, Opcode_utils


class GfreeInstrumentation:

    def __init__(self, instrs, funcs):
        self.instrs = instrs
        self.funcs = {f.func_begin_addr: f for f in funcs}.values()
        self.funcs.sort(key=lambda f: f.func_begin_addr)
        self.rets = {f.func_begin_addr: list() for f in self.funcs}
        self.indcalls = {f.func_begin_addr: list() for f in self.funcs}
        self.fIDset = set()
        self.avoid = set()
        if os.path.isfile('pic_thunk.info'):
            with open('pic_thunk.info') as f:
                self.avoid = set(map(lambda l: int(l, 16), f))

    @staticmethod
    def perform(instrs, funcs):
        gfree = GfreeInstrumentation(instrs, funcs)
        gfree.findfreebranches()
        gfree.indirectprotection()
        gfree.returnprotection()
        return gfree.instrs

    badbytes = set(('\xc2', '\xc3', '\xca', '\xcb', '\xff'))
    def generatefuncID(self):
        while True:
            fid = pack('<I', random.getrandbits(32))
            if not fid in self.fIDset:
                if not ELF_utils.elf_arm() and \
                   next((b for b in fid if b in GfreeInstrumentation.badbytes), None) is not None:
                    continue
                self.fIDset.add(fid)
                return unpack('<HH', fid) if ELF_utils.elf_arm() \
                       else unpack('<i', fid)[0]

    def findfreebranches(self):
        j = 0; curr_func = self.funcs[0]
        for ins in self.instrs:
            loc_addr = get_loc(ins).loc_addr
            if loc_addr >= self.funcs[j].func_end_addr and j < len(self.funcs) - 1:
                j += 1
                curr_func = self.funcs[j]
            if Opcode_utils.is_indirect(ins[1]):
                self.indcalls[curr_func.func_begin_addr].append(loc_addr)
            elif Opcode_utils.is_ret(ins):
                self.rets[curr_func.func_begin_addr].append(loc_addr)
            elif Opcode_utils.is_any_jump(ins[0]):
                if (isinstance(ins[1], Types.Label) \
                    and (not ins[1].startswith('S_0') \
                    or int(ins[1].lstrip('S_'), 16) in self.rets)) \
                  or Opcode_utils.is_func(ins[1]):
                    self.rets[curr_func.func_begin_addr].append(loc_addr)

        # Logging
        with open('exitpoints.info', 'w') as f:
            f.writelines(str(hex(e)) + ': ' + str(map(hex, self.rets[e])) + '\n' for e in self.rets if len(self.rets[e]) > 0)
        with open('indcalls.info', 'w') as f:
            f.writelines(str(hex(e)) + ': ' + str(map(hex, self.indcalls[e])) + '\n' for e in self.indcalls if len(self.indcalls[e]) > 0)


    def addxorcanary(self, i, func):
        if func.func_begin_addr in self.avoid: return i + 1
        if len(self.indcalls[func.func_begin_addr]) == 0:
            header = inlining.get_returnenc(self.instrs[i])
            self.instrs[i:i+1] = header
            i += len(header) - 1
            popcookie = False
        else: popcookie = True
        for t in self.rets[func.func_begin_addr]:
            while get_loc(self.instrs[i]).loc_addr != t: i += 1
            if ELF_utils.elf_arm() and self.instrs[i][0][-2:] in Types.CondSuff:
                # Handle somehow IT blocks
                itlen = 0
                while not self.instrs[i-itlen][0].upper().startswith('IT') and itlen < 5: itlen += 1
                if itlen < 5:
                    i -= itlen
                    j = len(self.instrs[i][0].strip()) + 1
                    self.instrs[i:i+j] = inlining.translate_it_block(self.instrs[i:i+j])
                    while get_loc(self.instrs[i]).loc_addr != t: i += 1
            footer = inlining.get_returnenc(self.instrs[i], popcookie)
            self.instrs[i:i+1] = footer
            i += len(footer)
        return i

    def addframecookie(self, i, func):
        if len(self.rets[func.func_begin_addr]) == 0: return i + 1
        fID = self.generatefuncID()
        header = inlining.get_framecookiehead(self.instrs[i], fID)
        self.instrs[i:i+1] = header
        i += len(header) - 1
        for t in self.indcalls[func.func_begin_addr]:
            while get_loc(self.instrs[i]).loc_addr != t: i += 1
            check = inlining.get_framecookiecheck(self.instrs[i], fID)
            self.instrs[i:i+1] = check
            i += len(check)
        return i

    def addinlining(self, locations, instrumenter):
        i = 0; j = 0
        while i < len(self.instrs):
            loc_addr = get_loc(self.instrs[i]).loc_addr
            if loc_addr >= self.funcs[j].func_end_addr and j < len(self.funcs) - 1: j += 1
            if loc_addr == self.funcs[j].func_begin_addr and len(locations[loc_addr]) > 0:
                i = instrumenter(i, self.funcs[j])
            else: i += 1

    def returnprotection(self):
        self.addinlining(self.rets, self.addxorcanary)

    def indirectprotection(self):
        random.seed(time.time())
        self.addinlining(self.indcalls, self.addframecookie)

