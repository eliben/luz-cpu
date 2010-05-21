-- CPU package of common definitions, types and constants
--
-- Luz micro-controller implementation
-- Eli Bendersky (C) 2008-2010
--
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;


package cpu_defs is 
    
    --------------------------------------------------------------
    --
    -- Data types
    --
    subtype doubleword  is std_logic_vector(63 downto 0);
    subtype word        is std_logic_vector(31 downto 0);
    subtype halfword    is std_logic_vector(15 downto 0);
    subtype byte        is std_logic_vector(7 downto 0);
    
    --------------------------------------------------------------
    --
    -- Slave/peripheral interfaces for memory mapping
    --
    -- For each slave interface, we have:
    --
    -- START/END: first and last address in the memory map of the
    --            interface
    -- MASKBIT: for masking the part of an address given to the
    --          slave. 
    --
    constant CORE_REG_ADDR_START:   word := x"00000000";
    constant CORE_REG_ADDR_END:     word := x"00000FFF";
    constant CORE_REG_ADDR_SIZE:    natural := 12;
    
    constant MEM_ADDR_START:        word := x"00100000";
    constant MEM_ADDR_END:          word := x"0013FFFF";
    constant MEM_ADDR_SIZE:         natural := 18;
    
    --------------------------------------------------------------
    -- 
    -- Core registers
    -- 
    constant NCORE_REGS_LOG2: natural := 4;
    subtype core_reg_addr is std_logic_vector(11 downto 0);
    subtype core_reg_sel is std_logic_vector(NCORE_REGS_LOG2 - 1 downto 0);
    
    constant CORE_REG_EXCEPTION_VECTOR:     natural := 1;
    constant CORE_REG_CONTROL_1:            natural := 5;
    constant CORE_REG_EXCEPTION_CAUSE:      natural := 7;
    constant CORE_REG_EXCEPTION_RET_ADDR:   natural := 8;
    constant CORE_REG_INTERRUPT_ENABLE:     natural := 11;
    constant CORE_REG_INTERRUPT_PENDING:    natural := 12;
    
    constant ADDR_OF_EXCEPTION_VECTOR:      core_reg_addr := x"004";    
    constant ADDR_OF_CONTROL_1:             core_reg_addr := x"100";
    constant ADDR_OF_EXCEPTION_CAUSE:       core_reg_addr := x"108";
    constant ADDR_OF_EXCEPTION_RET_ADDR:    core_reg_addr := x"10C";
    constant ADDR_OF_INTERRUPT_ENABLE:      core_reg_addr := x"120";
    constant ADDR_OF_INTERRUPT_PENDING:     core_reg_addr := x"124";
    
    function core_reg2addr_map (sel: core_reg_sel) return core_reg_addr;    
    function addr2core_reg_map (addr: core_reg_addr) return core_reg_sel;
    
    --------------------------------------------------------------
    --
    -- Opcodes
    --
    subtype cpu_opcode is std_logic_vector(5 downto 0);
    
    constant OP_ADD:    cpu_opcode := "000000";
    constant OP_SUB:    cpu_opcode := "000001";
    constant OP_MULU:   cpu_opcode := "000010";
    constant OP_MUL:    cpu_opcode := "000011";
    constant OP_DIVU:   cpu_opcode := "000100";
    constant OP_DIV:    cpu_opcode := "000101";
    constant OP_LUI:    cpu_opcode := "000110";
    constant OP_SLL:    cpu_opcode := "000111";
    constant OP_SRL:    cpu_opcode := "001000";
    constant OP_AND:    cpu_opcode := "001001";
    constant OP_OR:     cpu_opcode := "001010";
    constant OP_NOR:    cpu_opcode := "001011";
    constant OP_XOR:    cpu_opcode := "001100";
    constant OP_LB:     cpu_opcode := "001101";
    constant OP_LH:     cpu_opcode := "001110";
    constant OP_LW:     cpu_opcode := "001111";
    constant OP_LBU:    cpu_opcode := "010000";
    constant OP_LHU:    cpu_opcode := "010001";
    constant OP_SB:     cpu_opcode := "010010";
    constant OP_SH:     cpu_opcode := "010011";
    constant OP_SW:     cpu_opcode := "010100";
    constant OP_B:      cpu_opcode := "010101";
    constant OP_JR:     cpu_opcode := "010110";
    constant OP_BEQ:    cpu_opcode := "010111";
    constant OP_BNE:    cpu_opcode := "011000";
    constant OP_BGE:    cpu_opcode := "011001";
    constant OP_BGT:    cpu_opcode := "011010";
    constant OP_BLE:    cpu_opcode := "011011";
    constant OP_BLT:    cpu_opcode := "011100";
    constant OP_CALL:   cpu_opcode := "011101";
    constant OP_ADDI:   cpu_opcode := "100000";
    constant OP_SUBI:   cpu_opcode := "100001";
    constant OP_BGEU:   cpu_opcode := "100010";
    constant OP_BGTU:   cpu_opcode := "100011";
    constant OP_BLEU:   cpu_opcode := "100100";
    constant OP_BLTU:   cpu_opcode := "100101";
    constant OP_ANDI:   cpu_opcode := "101001";
    constant OP_ORI:    cpu_opcode := "101010";
    constant OP_SLLI:   cpu_opcode := "101011";
    constant OP_SRLI:   cpu_opcode := "101100";
    constant OP_ERET:   cpu_opcode := "111110";
    constant OP_HALT:   cpu_opcode := "111111";

end cpu_defs;


package body cpu_defs is
    function core_reg2addr_map (sel: core_reg_sel) return core_reg_addr is
    begin
        case to_integer(unsigned(sel)) is
            when CORE_REG_EXCEPTION_VECTOR      => return ADDR_OF_EXCEPTION_VECTOR;
            when CORE_REG_CONTROL_1             => return ADDR_OF_CONTROL_1;
            when CORE_REG_EXCEPTION_CAUSE       => return ADDR_OF_EXCEPTION_CAUSE;
            when CORE_REG_EXCEPTION_RET_ADDR    => return ADDR_OF_EXCEPTION_RET_ADDR;
            when CORE_REG_INTERRUPT_ENABLE      => return ADDR_OF_INTERRUPT_ENABLE;
            when CORE_REG_INTERRUPT_PENDING     => return ADDR_OF_INTERRUPT_PENDING;
            when others                         => return x"000";
        end case;
    end;

    function addr2core_reg_map (addr: core_reg_addr) return core_reg_sel is
        variable sel_integer: natural range 0 to 2**NCORE_REGS_LOG2 - 1;
    begin
        case addr is
            when ADDR_OF_EXCEPTION_VECTOR   => sel_integer := CORE_REG_EXCEPTION_VECTOR;
            when ADDR_OF_CONTROL_1          => sel_integer := CORE_REG_CONTROL_1;
            when ADDR_OF_EXCEPTION_CAUSE    => sel_integer := CORE_REG_EXCEPTION_CAUSE;
            when ADDR_OF_EXCEPTION_RET_ADDR => sel_integer := CORE_REG_EXCEPTION_RET_ADDR;
            when ADDR_OF_INTERRUPT_ENABLE   => sel_integer := CORE_REG_INTERRUPT_ENABLE;
            when ADDR_OF_INTERRUPT_PENDING  => sel_integer := CORE_REG_INTERRUPT_PENDING;
            when others                     => sel_integer := 0;
        end case;
        
        return std_logic_vector(to_unsigned(sel_integer, NCORE_REGS_LOG2));
    end;
end cpu_defs;

