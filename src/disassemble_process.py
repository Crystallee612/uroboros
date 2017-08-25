import os
import filter_nop
import useless_func_del
from ail_parser import AilParser

class Disam(object):

    @staticmethod
    def disasm_skip(filepath, ba, ea):
        os.system("objdump -Dr -j .text " + filepath + " --start-address=" + str(ba) + " --stop-address=" + str(ea) + " > " + filepath + ".temp")
        useless_func_del.main(filepath)
        os.system("cat " + filepath + ".disassemble | grep \"^ \" | cut -f1,3 > instrs.info")
        filter_nop.main()
        os.system("cut -f 1 instrs.info > text_mem.info")

    @staticmethod
    def get_userfuncs(funcs):
        return filter(lambda f: not f.is_lib, funcs)

    @staticmethod
    def disassemble(filepath, funcs, secs):
        #TODO: stub
        ailpar = AilParser()
        total = 0.0
        cond = False
        while not cond and total < 600.0:
            ailpar.set_funcs(funcs)
            ailpar.set_secs(secs)

            # ailpar.processInstrs(ilist)
            print "2: disassembly validates"


