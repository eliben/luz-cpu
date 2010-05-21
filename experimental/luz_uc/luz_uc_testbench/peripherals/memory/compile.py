
FILES = [
    '../../vhdl_utils/io_utils.vhd',
    '../../vhdl_utils/txt_util.vhd',
    '../../../luz_uc_rtl/peripherals/memory/sim_memory_onchip_wb.vhd',
    'memory_onchip_wb_tb.vhd',
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
    