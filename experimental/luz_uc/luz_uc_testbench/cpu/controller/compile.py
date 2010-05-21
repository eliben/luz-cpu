
FILES = [
    '../../../luz_uc_rtl/cpu/defs.vhd',
    '../../../luz_uc_rtl/cpu/utils.vhd',
    '../../../luz_uc_rtl/cpu/alu.vhd',
    '../../../luz_uc_rtl/cpu/controller.vhd',
    '../../../luz_uc_rtl/cpu/program_counter.vhd',
    'controller_tb.vhd',
]


##################################################################

def do_compile():
    import sys
    sys.path.append('../../python_utils')
    from VHDLCompiler import VHDLCompiler, VHDLCompileError

    params = '-work work -quiet -pedanticerrors -2002 -explicit'
    
    if len(sys.argv) > 1 and sys.argv[1] == 'all':
        all = True
    else:
        all = False
    
    #~ all = True
    
    vc = VHDLCompiler()
    
    try:
        vc.compile_files(FILES, params=params, lib='work', force_compile_all=all)
    except VHDLCompileError, err:
        print '!!!! Compile error !!!!'
        print err


if __name__ == '__main__':
    do_compile()
    