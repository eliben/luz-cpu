
FILES = [
    '../../../luz_uc_rtl/cpu/defs.vhd',
    '../../../luz_uc_rtl/cpu/registers.vhd',
    'registers_tb.vhd',
]


##################################################################

def do_compile():
    import sys
    sys.path.append('../../python_utils')
    from VHDLCompiler import VHDLCompiler, VHDLCompileError

    params = '-work work -quiet -pedanticerrors -2002 -explicit'
    all = True
    
    vc = VHDLCompiler()
    
    try:
        vc.compile_files(FILES, params=params, lib='work', force_compile_all=all)
    except VHDLCompileError, err:
        print '!!!! Compile error !!!!'
        print err


if __name__ == '__main__':
    do_compile()
    