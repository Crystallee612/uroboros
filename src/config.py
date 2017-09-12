from subprocess import check_output
from utils.ail_utils import ELF_utils


ARCH_ARMT = 'thumb'
ARCH_X86 = 'x86'
X86_TOOL = ''
ARM_TOOL = 'arm-linux-gnueabihf-'

# Defaults
arch = ARCH_X86
objdump = 'objdump'
strip = 'strip'
compiler = 'gcc'


def setup(filepath):
    global arch
    global strip
    global objdump
    global compiler
    if ELF_utils.elf_arm():
        entry = check_output('readelf -h ' + filepath + ' | grep Entry', shell=True)
        entry = int(entry.split()[3], 16)
        if entry & 1: print 'Thumb binary detected'
        else: raise Exception('Only thumb supported')
        arch = ARCH_ARMT
        objdump = ARM_TOOL + objdump + ' --disassembler-options=force-thumb'
        strip = ARM_TOOL + strip
        compiler = ARM_TOOL + compiler
