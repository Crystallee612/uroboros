import os
import config
import spliter
import export_data
import parse_init_array
from visit import ailVisitor
from share_lib_helper import lib32_helper
from disasm import Types, exception_process
from utils.ail_utils import get_loc, read_file, ELF_utils, dec_hex, set_loc,\
                            unify_int_list, bbn_byloc


def rev_map(f, l):
    return map(f, l)[::-1]

class ft(object):
    def __init__(self, fn, fbaddr, feaddr):
        self.fn = fn; self.fbaddr = fbaddr; self.feaddr = feaddr
    def __repr__(self):
        return self.fn + ('@0x%X-0x%X' % (self.fbaddr, self.feaddr))


class datahandler:

    def __init__(self, label):
        self.sec = []
        self.data = []
        self.rodata = []
        self.got = []
        self.bss = []

        self.text_mem_addrs = []
        self.label_mem_addrs = []

        self.data_labels = []
        self.data_labels_reloc = []
        self.text_labels = []
        self.text_labels_reloc = []

        self.label = label
        self.label_set = []

        self.data_list = []
        self.rodata_list = []
        self.got_list = []
        self.bss_list = []

        self.text_sec = (0, 0)
        self.locations = []

        self.in_jmptable = False

        self.text_mem_arr = [0]
        self.label_mem_arr = [0]
        self.func_begin_arr = [0]
        self.label_arr = [0]

        self.fl_sort = [ft('', 0, 0)]
        self.cur_func_name = ''
        self.assumption_two = False
        self.assumption_three = False

    def set_datas(self, funcs):
        self.section_collect()
        self.data_collect()

        self.data_list = self.data_trans(self.data)
        self.rodata_list = self.data_trans(self.rodata)
        self.got_list = self.data_trans(self.got)
        self.bss_list = self.data_trans(self.bss)
        self.locations = self.label_locate()

        self.label_set = set(map(lambda e: e[1], self.label))
        self.label_arr = sorted(self.label_set)

        fl = sorted(funcs, cmp=lambda f1,f2: f1.func_begin_addr - f2.func_begin_addr)
        self.fl_sort = map(lambda f: ft(f.func_name, f.func_begin_addr, f.func_end_addr), fl)

        self.text_mem_addrs = map(lambda a: int(a.strip().rstrip(':'), 16), read_file('text_mem.info'))
        self.text_mem_arr = self.text_mem_addrs

        self.label_mem_arr = sorted(self.label_mem_addrs)
        self.set_assumption_flag()

        self.begin_addrs = map(lambda f: f.func_begin_addr, funcs)
        if ELF_utils.elf_32(): self.data_refer_solve(funcs)
        else: self.data_refer_solve_64(funcs)

    def set_assumption_flag(self):
        with open('assumption_set.info') as f:
            l = f.readline()
            self.assumption_two = '2' in l
            self.assumption_three = '3' in l

    def get_textlabel(self):
        self.dump_d2c_labels(self.text_labels_reloc)
        return self.text_labels

    def text_sec_collect(self):
        with open('text_sec.info') as f:
            items = f.readline().split()
            self.text_sec = (int(items[1], 16), int(items[3], 16))

    def check_text(self, addr):
        if addr == 0xffff: return False
        b = self.text_sec[0]
        e = b + self.text_sec[1]
        return b <= addr < e and bbn_byloc(addr, self.text_mem_arr)

    def dump_c2d_labels(self, dl):
        with open('final_c2d_label.txt', 'a') as f:
            f.write('\n'.join(map(lambda e: e[0] + ' : ' + dec_hex(e[1]), dl)))
            f.write('\n')

    def dump_d2d_labels(self, dl):
        with open('final_d2d_label.txt', 'a') as f:
            f.write('\n'.join(map(dec_hex, dl)))
            f.write('\n')

    def dump_d2c_labels(self, dl):
        with open('final_d2c_label.txt', 'a') as f:
            f.write('\n'.join(map(dec_hex, dl)))
            f.write('\n')

    def traverse64(self, l, addr):
        i = 0
        while i < len(l) - 7:
            val = int(''.join(map(lambda e: e[1][8:10], reversed(l[i:i+8]))), 16)
            s = self.check_sec(val)
            if s is not None:
                if self.assumption_two:
                    self.in_jmptable = False
                else:
                    self.data_labels.insert(0, (s.sec_name, val))
                    self.data_labels_reloc.insert(0, addr)
                    l[i] = (l[i][0], '.quad S_0x%X' % val)
                    l[i+1:i+8] = [('', '')] * 7
            else:
                if self.check_text(val):
                    c = bbn_byloc(val, self.begin_addrs) if self.assumption_three else True
                    if (c and self.check_jmptable_1(l[i][0])) or self.check_jmptable(l[i][0], val):
                        self.in_jmptable = True
                        self.cur_func_name = self.fn_byloc(val)
                        self.text_labels.insert(0, val)
                        self.text_labels_reloc.insert(0, addr)
                        l[i] = (l[i][0], '.quad S_0x%X' % val)
                        l[i+1:i+8] = [('', '')] * 7
                    else: self.in_jmptable = False
                else: self.in_jmptable = False
            i += 8
            addr += 8

    def data_refer_solve_64(self, funcs):
        self.add_data_label()
        self.traverse64(self.data_list, 0x080500c4)
        self.traverse64(self.rodata_list, 0x0804cc60)
        self.traverse64(self.got_list, 0x0)

    def traverse32(self, l, addr):
        i = 0
        while i < len(l) - 3:
            val = int(''.join(map(lambda e: e[1][8:10], reversed(l[i:i+4]))), 16)
            s = self.check_sec(val)
            if s is not None:
                if self.assumption_two:
                    self.in_jmptable = False
                else:
                    self.data_labels.insert(0, (s.sec_name, val))
                    self.data_labels_reloc.insert(0, addr)
                    l[i] = (l[i][0], '.long S_0x%X' % val)
                    l[i+1:i+4] = [('', '')] * 3
            else:
                if self.check_text(val):
                    c = bbn_byloc(val, self.begin_addrs) if self.assumption_three else True
                    if (c and self.check_jmptable_1(val)) or self.check_jmptable(l[i][0], val):
                        self.in_jmptable = True
                        self.cur_func_name = self.fn_byloc(val)
                        self.text_labels.insert(0, val)
                        self.text_labels_reloc.insert(0, addr)
                        l[i] = (l[i][0], '.long S_0x%X' % val)
                        l[i+1:i+4] = [('', '')] * 3
                    else: self.in_jmptable = False
                else: self.in_jmptable = False
            i += 4
            addr += 4

    def data_refer_solve(self, funcs):
        self.add_data_label()
        self.traverse32(self.data_list, 0x082f3110)
        self.traverse32(self.rodata_list, 0x08288680)

    def check_jmptable_1(self, addrs):
        try: return int(addrs, 16) in self.label_set
        except: return False

    def fn_byloc(self, addr):
        l = 0; r = len(self.fl_sort)-1
        while l <= r:
            mid = l + (r - l) / 2
            fmid = self.fl_sort[mid]
            if fmid.fbaddr <= addr <= fmid.feaddr:
                return fmid.fn
            elif fmid.fbaddr < addr:
                l = mid + 1
            else: r = mid - 1
        raise Exception('failed to find funcname')

    def check_jmptable(self, addrs, v):
        if self.in_jmptable and self.fn_byloc(v) == self.cur_func_name:
            return True
        try:
            if bbn_byloc(int(addrs, 16), self.label_arr):
                self.in_jmptable = True
                return True
            return False
        except: return False

    def section_collect(self):
        with open('sections.info') as f:
            for l in f:
                items = l.split()
                addr = int(items[1], 16)
                size = int(items[3], 16)
                self.sec.insert(0, Types.Section(items[0], addr, size))

    def section_offset(self, name, addr):
        for h in self.sec:
            if h.sec_name == name:
                return addr - h.sec_begin_addr
        raise Exception('failed to find section offset')

    def section_addr(self, name):
        for h in self.sec:
            if h.sec_name == name:
                return h.sec_begin_addr
        raise Exception('failed to find section')

    def data_collect(self):
        spliter.main()
        self.data = self.collect('data_split.info')
        self.rodata = self.collect('rodata_split.info')
        # if not ELF_utils.elf_32():
        self.got = self.collect('got_split.info')
        self.bss = self.collect('bss.info')

    def sec_transform(self, s):
        if s == '.got': return '.got'
        elif s == 'bss': return '.bss'
        return '.rodata'

    def check_sec(self, addr):
        for h in self.sec:
            b = h.sec_begin_addr
            e = b + h.sec_size
            if b <= addr < e: return h
        return None

    def data_trans(self, data_list):
        return map(lambda l: ('', l), data_list)[::-1]

    def label_locate(self):
        return map(lambda l: (l[0], self.section_offset(l[0], l[1])), self.label)

    def add_data_label(self):
        dataoff = self.section_addr('.data')
        rodataoff = self.section_addr('.rodata')
        for e in self.locations:
            n, l = e
            if n == '.data':
                self.data_list[l] = (dec_hex(l+dataoff), self.data_list[l][1])
            elif n == '.rodata':
                self.rodata_list[l] = (dec_hex(l+rodataoff), self.rodata_list[l][1])

    def process(self, lbs, withoff=False):
        ds = {'.data': self.data_list, '.rodata': self.rodata_list,
              '.got': self.got_list, '.bss': self.bss_list}
        for i in xrange(len(lbs)):
            n, l = lbs[i]
            if n in ds:
                if withoff:
                    off = l - self.section_addr(n)
                else:
                    off = l
                    l += self.section_addr(n)
                ds[n][off] = ('S_' + dec_hex(l) + ': ', ds[n][off][1])

    def data_output(self):
        self.process(self.locations)
        self.process(self.data_labels, True)
        if len(self.rodata_list) != 0:
            l, s = self.rodata_list[0]
            self.rodata_list[0] = ('s_dummy:\n' + l, s)
        self.rodata_list.insert(0, ('.section .rodata', ''))
        self.got_list.insert(0, ('.section .got', ''))
        self.data_list.insert(0, ('.section .data', ''))
        self.bss_list.insert(0, ('.section .bss', ''))
        with open('final_data.s', 'a') as f:
            func = lambda e: e[0] + e[1]
            f.write('\n'.join(map(func, self.rodata_list)) + '\n')
            f.write('\n' + '\n'.join(map(func, self.data_list)) + '\n')
            f.write('\n' + '\n'.join(map(func, self.got_list)) + '\n')
            f.write('\n' + '\n'.join(map(func, self.bss_list)))

    def collect(self, name):
        if os.path.isfile(name):
            return map(str.strip, read_file(name))
        return []


class instrhandler(object):

    def __init__(self, instr_list, des):
        self.des = des
        self.locs = []
        # self.new_instrlist = []
        self.instr_list = instr_list

    def get_instr_list(self):
        return map(lambda e: set_loc(e[0],e[1]), zip(self.instr_list, self.locs))

    def set_instr_list(self):
        self.locs = map(get_loc, self.instr_list)

    def clean_sort(self, ll):
        ll = map(lambda l: int(l[3:] if '$' in l else l[2:], 16), ll)
        ll = filter(lambda e: e != 0, ll)
        return unify_int_list(ll)

    def process(self):
        # here dec_hex is 'S_' + dec_hex(v)
        do_update = lambda s,n: s if n in s else s + '\n' + n
        des1 = self.clean_sort(self.des)
        i = 0; j = 0
        while True:
            if j == len(des1) or i == len(self.locs):
                break
            # if i == len(self.locs)-1 and j == len(des1)-1:
            #    raise Exception("undefined des list")
            lh = self.locs[i]
            dh = des1[j]
            if dh == lh.loc_addr:
                lhs = 'S_' + dec_hex(lh.loc_addr)
                if ELF_utils.elf_arm() and not isinstance(self.instr_list[i][0], Types.InlineData):
                    lhs = '.thumb_func\n' + lhs
                label = do_update(lh.loc_label, lhs + ' : ')
                self.locs[i].loc_label = label
                j += 1
            elif dh < lh.loc_addr:
                j += 1
            i += 1


class reassemble(ailVisitor):

    data_set = {}
    plt_hash = {}
    pic_hash = {}
    text_set = {}

    def __init__(self):
        super(reassemble, self).__init__()
        self.label = []
        # collect relocation info in c2d
        self.c2d_addr = []
        self.deslist = []
        # only collect the relocated symbol
        self.deslist_reloc = []
        self.init_array_list = []
        self.eh_frame_list = []
        self.excpt_tbl_list = []
        self.jmpreflist = []
        self.sec = []
        self.instr_list = []
        self.text_sec = (0,0) # begin, size
        self.plt_sec = (0,0)  # begin, size
        self.text_mem_addrs = []
        # collect all the symbols from code section or from data sections
        self.symbol_list = []
        # Initializer
        self.section_collect()
        self.plt_collect()
        self.plt_sec_collect()
        self.text_sec_collect()
        # ARM
        self.ARMmovs = []
        self.ARMvldrtargets = []

    def section_collect(self):
        def secmapper(l):
            items = l.split()
            return Types.Section(items[0], int(items[1], 16), int(items[3], 16))
        lines = read_file('sections.info')
        self.sec = map(secmapper, lines)[::-1]
        self.text_mem_addrs = map(str.strip, read_file('text_mem.info'))

    def plt_collect(self):
        lines = read_file('plts.info')
        for l in lines:
            items = l.split()
            addr = int(items[0][1:], 16)
            name = items[1].split('@')[0][1:]
            reassemble.plt_hash[addr] = name

    def pic_collect(self):
        lines = read_file('pic_secs.info')
        for l in lines:
            items = l.split()
            reassemble.pic_hash[items[0]] = (int(items[1], 16), int(items[3], 16))

    def text_sec_collect(self):
        lines = read_file('text_sec.info')
        for l in lines:
            items = l.split()
            self.text_sec = (int(items[1], 16), int(items[3], 16))

    def plt_sec_collect(self):
        lines = read_file('plt_sec.info')
        for l in lines:
            items = l.split()
            self.plt_sec = (int(items[1], 16), int(items[3], 16))

    def check_sec(self, addr):
        for s in self.sec:
            b = s.sec_begin_addr
            e = b + s.sec_size
            if b <= addr < e: return s
        return None

    def check_text(self, addr):
        e = sum(self.text_sec)
        if addr == 0xffff: return False
        return self.text_sec[0] <= addr < e

    def check_text_abd(self, addr):
        e = sum(self.text_sec)
        return self.text_sec[0] <= addr <= e

    def check_plt(self, addr):
        e = sum(self.plt_sec)
        return self.plt_sec[0] <= addr < e

    def parse_const(self, c):
        if isinstance(c, Types.Const): return c
        raise Exception("Not a constant")

    normal_char = '#' if config.arch == config.ARCH_ARMT else '$'
    def build_symbol(self, c):
        if isinstance(c, Types.Point):
            return 'S_' + dec_hex(c)
        elif isinstance(c, Types.Normal):
            return reassemble.normal_char + 'S_' + dec_hex(c)

    def build_plt_symbol(self, c):
        n = reassemble.plt_hash[c]
        if isinstance(c, Types.Point):
            return n
        elif isinstance(c, Types.Normal):
            return reassemble.normal_char + n
        raise Exception("Failed plt symbol")

    def insert_text(self, l, exp):
        if exp not in reassemble.text_set:
            reassemble.text_set[exp] = ''
            self.deslist.insert(0, l)

    def insert_data(self, sec, exp, loc_addr):
        if exp not in reassemble.data_set:
            reassemble.data_set[exp] = ''
            self.label.insert(0, (sec, exp))
        self.c2d_addr.insert(0, loc_addr)

    def v_exp2(self, exp, instr, f, chk):
        if isinstance(exp, Types.Const):
            if isinstance(exp, Types.Normal) and chk: return exp
            s = self.check_sec(exp)
            if s is not None:
                self.insert_data(s.sec_name, exp, get_loc(instr).loc_addr)
                return Types.Label(self.build_symbol(exp))
            if self.check_text(exp):
                if ELF_utils.elf_arm(): exp = type(exp)(exp & (-2))
                s_label = self.build_symbol(exp)
                self.insert_text(s_label, exp)
                self.deslist_reloc.insert(0, get_loc(instr).loc_addr)
                return Types.Label(s_label)
            if self.check_plt(exp):
                return Types.Label(self.build_plt_symbol(exp))
        elif isinstance(exp, Types.Symbol):
            if isinstance(exp, Types.JumpDes):
                if self.check_text(exp):
                    s_label = 'S_' + dec_hex(exp)
                    self.insert_text(s_label, exp)
                    return Types.Label(s_label)
                elif self.check_plt(exp) and exp in reassemble.plt_hash:
                    return Types.Label(reassemble.plt_hash[exp])
            elif isinstance(exp, Types.StarDes):
                return Types.StarDes(self.v_exp2(exp.content, instr, f, chk))
            elif isinstance(exp, Types.CallDes):
                if exp.func_name.startswith('S_0'):
                    addr = int(exp.func_name[2:], 16)
                    if self.check_text(addr):
                        s_label = 'S_' + dec_hex(addr)
                        self.insert_text(s_label, addr)
                        return Types.Label(s_label)
                    elif self.check_plt(addr):
                        off = 0
                        while not reassemble.plt_hash.get(addr - off, None): off += 2
                        return Types.Label(reassemble.plt_hash[addr - off])
                else: self.symbol_list.insert(0, exp.func_begin_addr)
        elif isinstance(exp, Types.Ptr):
            if isinstance(exp, (Types.BinOP_PLUS, Types.BinOP_MINUS)):
                r, addr = exp
                s = self.check_sec(addr)
                if s is not None:
                    s_label = 'S_' + dec_hex(addr)
                    self.insert_data(s.sec_name, addr, get_loc(instr).loc_addr)
                    return Types.BinOP_PLUS_S((r, s_label)) \
                        if isinstance(exp, Types.BinOP_PLUS) \
                        else Types.BinOP_MINUS_S((r, s_label))
            elif isinstance(exp, (Types.FourOP_PLUS, Types.FourOP_MINUS)):
                r1, r2, off, addr = exp
                s = self.check_sec(addr)
                if s is not None:
                    s_label = 'S_' + dec_hex(addr)
                    self.insert_data(s.sec_name, addr, get_loc(instr).loc_addr)
                    return Types.FourOP_PLUS_S((r1,r2,off,s_label)) \
                        if isinstance(exp, Types.FourOP_PLUS) \
                        else Types.FourOP_MINUS_S((r1,r2,off,s_label))
            elif isinstance(exp, Types.JmpTable_PLUS):
                addr, r, off = exp
                s = self.check_sec(addr)
                if s is not None:
                    s_label = 'S_' + dec_hex(addr)
                    self.insert_data(s.sec_name, addr, get_loc(instr).loc_addr)
                    return Types.JmpTable_PLUS_S((s_label, r, off))
                if self.check_text(addr):
                    s_label = 'S_' + dec_hex(addr)
                    self.insert_text(s_label, addr)
                    self.deslist_reloc.insert(0, get_loc(instr).loc_addr)
                    return Types.JmpTable_PLUS_S((s_label, r, off))
            elif isinstance(exp, Types.JmpTable_MINUS):
                addr, r, off = exp
                s = self.check_sec(addr)
                if s is not None:
                    s_label = '-S_' + dec_hex(addr)
                    self.insert_data(s.sec_name, addr, get_loc(instr).loc_addr)
                    return Types.JmpTable_MINUS_S((s_label, r, off))
                if self.check_text(addr):
                    s_label = '-S_' + dec_hex(addr)
                    self.insert_text(s_label, addr)
                    self.deslist_reloc.insert(0, get_loc(instr).loc_addr)
                    return Types.JmpTable_MINUS_S((s_label, r, off))
        return exp

    def vinst2(self, f, instr):
        if isinstance(instr, Types.SingleInstr): return instr
        elif isinstance(instr, Types.DoubleInstr):
            return Types.DoubleInstr((instr[0], self.v_exp2(instr[1], instr, f, False),
                                      instr[2], instr[3]))
        elif isinstance(instr, Types.TripleInstr):
            is_test = instr[0].upper() in ['TEST', 'TESTL', 'TESTW', 'TESTB']
            return Types.TripleInstr((instr[0], self.v_exp2(instr[1], instr, f, is_test),
                                      self.v_exp2(instr[2], instr, f, is_test), instr[3], instr[4]))
        elif isinstance(instr, Types.FourInstr):
            return Types.FourInstr((instr[0], instr[1], self.v_exp2(instr[2], instr, f, False),
                                    instr[3], instr[4], instr[5]))

    def vinst2ARM(self, iv):
        instr = iv[1]
        if instr[0].upper() == 'MOVW': self.ARMmovs.append(iv[0])
        if isinstance(instr, Types.DoubleInstr):
            if isinstance(instr[1], Types.TBExp):
                self.insert_text(instr[1].base, int(instr[1].base.split('x')[1], 16))
                self.insert_text(instr[1].dest, int(instr[1].dest.split('x')[1], 16))
                return instr
            return Types.DoubleInstr((instr[0], self.v_exp2(instr[1], instr, None, False),
                                      instr[2], instr[3]))
        if isinstance(instr, Types.TripleInstr):
            if instr[0].startswith('vldr') and isinstance(instr[2], Types.Const):
                self.ARMvldrtargets.append(instr[2])
            return Types.TripleInstr((instr[0], instr[1], self.v_exp2(instr[2], instr, None, False),
                                      instr[3], instr[4]))
        return instr

    def doublemovARM(self, instrs):
        # insert labels for double mov operations
        #  movw r0, #0x102c -> movw r0, #:lower16:S_0x2102c
        #  movt r0, #0x2    -> movt r0, #:upper16:S_0x2102c
        for i in self.ARMmovs:
            mw = list(instrs[i])
            destreg = mw[1]
            tindex = 1
            while tindex < config.ARM_maxDoublemovDist:
                # GCC optimizations causes movw and movt not to be close to each other
                currinstr = instrs[i+tindex]
                if currinstr[0].upper() == 'MOV' and currinstr[2] == destreg:
                    # Sometimes GCC changes idea and picks another register to load the address
                    destreg = instrs[i+tindex][1]
                elif currinstr[1] == destreg:
                    if currinstr[0].upper() == 'STR':
                        # Some other times GCC wants to have even more fun and changes register using the stack
                        tindex += 1
                        while tindex < config.ARM_maxDoublemovDist:
                            if instrs[i+tindex][2] == currinstr[2]:
                                destreg = instrs[tindex+i][1]
                                break
                            tindex += 1
                    else: break
                tindex += 1
            tindex = i + tindex
            mt = list(instrs[tindex])
            if mt[0].upper() == 'MOVT' and mt[1] == destreg:
                val = (mt[2] << 16) + (mw[2] & 0xffff)
                s = self.check_sec(val)
                if s is not None:
                    s_label = 'S_' + dec_hex(val)
                    self.insert_data(s.sec_name, val, get_loc(mw).loc_addr)
                    self.c2d_addr.insert(0, get_loc(mt).loc_addr)
                    mw[2] = Types.Label('#:lower16:' + s_label)
                    mt[2] = Types.Label('#:upper16:' + s_label)
                    instrs[i] = type(instrs[i])(mw)
                    instrs[tindex] = type(instrs[tindex])(mt)
                if self.check_text(val):
                    val = val & (-2)
                    s_label = 'S_' + dec_hex(val)
                    self.insert_text(s_label, val)
                    self.deslist_reloc.insert(0, get_loc(mw).loc_addr)
                    self.deslist_reloc.insert(0, get_loc(mt).loc_addr)
                    mw[2] = Types.Label('#:lower16:' + s_label)
                    mt[2] = Types.Label('#:upper16:' + s_label)
                    instrs[i] = type(instrs[i])(mw)
                    instrs[tindex] = type(instrs[tindex])(mt)
        self.ARMmovs = []

    def visit_heuristic_analysis(self, instrs):
        func = lambda i: self.check_text(get_loc(i).loc_addr)
        self.instr_list = instrs
        if ELF_utils.elf_arm():
            tl = map(self.vinst2ARM, enumerate(instrs))
            self.doublemovARM(tl)
        else: tl = map(lambda i: self.vinst2(func, i), instrs)
        tl1 = map(lambda l: int(l.split('x')[1], 16), self.deslist)
        self.symbol_list = tl1 + self.symbol_list
        return tl

    def visit_type_infer_analysis(self, bbl, instrs):
        self.instr_list = instrs
        f = lambda: True
        return map(self.vinst2ARM, enumerate(instrs)) if ELF_utils.elf_arm() \
               else map(lambda i: self.vinst2(f, i), instrs)

    def share_lib_processing(self, instrs):
        if ELF_utils.elf_lib() and ELF_utils.elf_32():
            helper = lib32_helper(instrs)
            for addr in helper.traverse():
                s = self.check_sec(addr)
                if s is None: raise Exception('unsupported section info')
                self.label.insert(0, (s.sec_name, addr))
            return helper.get_instrs()
        return instrs

    def update_deslist_with_initarray(self):
        self.init_array_list = parse_init_array.main()

    def update_deslist_with_ehframe(self):
        self.eh_frame_list = exception_process.main('eh_frame')

    def update_deslist_with_excp_tbl(self):
        self.excpt_tbl_list = exception_process.main('gcc_exception_table')

    def dump_c2c_labels(self, dl):
        with open('final_c2c_label.txt', 'w') as f:
            f.write('\n'.join(map(dec_hex, dl)))

    def dump_c2d_labels(self, dl):
        with open('final_c2d_label.txt', 'w') as f:
            f.write('\n'.join(map(dec_hex, dl)))

    def adjust_loclabel(self, instr_list):
        self.update_deslist_with_initarray()
        self.dump_c2c_labels(self.deslist_reloc)
        t = self.init_array_list + self.deslist
        p = instrhandler(instr_list, t)
        p.set_instr_list()
        p.process()
        return p.get_instr_list()

    def adjust_jmpref(self, instr_list):
        p = instrhandler(instr_list, self.jmpreflist)
        p.set_instr_list()
        p.process()
        return p.get_instr_list()

    def adjust_globallabel(self, g_bss, instr_list):
        g_bss = filter(lambda e: '@' in e[1], g_bss)
        gbss_hs = {'S_0x' + e[0].lstrip('0'): e[1].split('@')[0] if '@' in e[1] else e[1] for e in g_bss}
        labels = gbss_hs.keys()
        def mapper(l):
            r = next((lab for lab in labels if lab in l), None)
            if r is not None: return l.replace(r, gbss_hs[r], 1)
            return l
        return map(mapper, instr_list)

    def data_dump(self, funcs):
        t = self.label + self.export_data_dump()
        p = datahandler(t)
        p.text_sec_collect()
        p.set_datas(funcs)
        self.jmpreflist = map(lambda l: 'S_' + dec_hex(l), p.get_textlabel())
        p.data_output()

    def init_array_dump(self):
        return # This seems creating problems rather than solving them
        if len(self.init_array_list) != 0 and not ELF_utils.elf_arm():
            with open('final_data.s', 'a') as f:
                f.write('\n\n.section .ctors,"aw",@progbits\n')
                f.write('.align 4\n')
                f.write('\n'.join(map(lambda s: '.long ' + s.strip(), self.init_array_list)))
                f.write('\n')

    def export_data_dump(self):
        def mapper(l):
            i = int(l.strip(), 16)
            s = self.check_sec(i)
            if s is None: raise Exception('unsupported export data')
            return (s.sec_name, i)
        return map(mapper, export_data.main())

    def reassemble_dump(self, u_funcs):
        self.data_dump(u_funcs)
        self.init_array_dump()

    def add_func_label(self, ufuncs, instrs):
        i = 0; j = 0
        while True:
            if i == len(ufuncs) or j == len(instrs):
                break
            hf = ufuncs[i]
            hi = instrs[j]
            iloc = get_loc(hi)
            if hf.func_begin_addr == iloc.loc_addr and hf.func_name not in iloc.loc_label:
                lab = '\n' + hf.func_name + ' : '
                if ELF_utils.elf_arm(): lab = '\n.thumb_func' + lab
                iloc.loc_label = lab + iloc.loc_label
                instrs[j] = set_loc(hi, iloc)
                i += 1
                j -= 1
            elif hf.func_begin_addr < iloc.loc_addr:
                i += 1
            j += 1
        return instrs

    def add_bblock_label(self, bbl, instrs):
        bbl1 = sorted(bbl, lambda b1,b2: b1.bblock_begin_loc.loc_addr - b2.bblock_begin_loc.loc_addr)
        i = 0; j = 0
        while True:
            if i == len(instrs) and j < len(bbl1):
                raise Exception('failed to add block label')
            if j == len(bbl1): break
            hi = instrs[i]
            hb = bbl1[j]
            iloc = get_loc(hi)
            bloc = hb.bblock_begin_loc
            if bloc.loc_addr == iloc.loc_addr:
                iloc = Types.Loc(hb.bblock_name + ': ' + iloc.loc_label, iloc.loc_addr, iloc.loc_visible)
                instrs[i] = set_loc(instrs[i], iloc)
                j += 1
            i += 1
        return instrs

    def unify_loc(self, instrs):
        last_label = ''
        for i in xrange(len(instrs)):
            lo = get_loc(instrs[i])
            if lo.loc_label != '' and lo.loc_label == last_label:
                instrs[i] = set_loc(instrs[i], Types.Loc('', lo.loc_addr, True))
            else:
                last_label = lo.loc_label
        return instrs

    def alignvldrARM(self, instrs):
        self.ARMvldrtargets = sorted(set(self.ARMvldrtargets))
        i = 0; j = 0
        while True:
            if i == len(instrs) or j == len(self.ARMvldrtargets): break
            loc = get_loc(instrs[i])
            if loc.loc_addr == self.ARMvldrtargets[j]:
                loc.loc_label = '\n.align 2' + loc.loc_label
                instrs[i] = set_loc(instrs[i], loc)
                j += 1
            i += 1
        return instrs
