-- CPU controller.
-- Main controller code of the CPU - fetching, decoding and 
-- executing instructions.
--
-- Luz micro-controller implementation
-- Eli Bendersky (C) 2008-2010
--
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.cpu_defs.all;
use work.utils_pak.all;


-- The main CPU controller module.
--
entity controller is 
port
(
    clk:            in  std_logic;
    reset_n:        in  std_logic;

    -- memory interface
    --
    mem_read:       out std_logic;
    mem_write:      out std_logic;
    mem_bytesel:    out std_logic_vector(3 downto 0);
    mem_addr:       out word;
    mem_data_out:   out word;
    mem_ack:        in  std_logic;
    mem_data_in:    in  word;

    -- interface to the register file
    --
    reg_sel_a:      out std_logic_vector(4 downto 0);
    reg_a_out:      in  word;    
    reg_sel_b:      out std_logic_vector(4 downto 0);
    reg_b_out:      in  word;
    reg_sel_c:      out std_logic_vector(4 downto 0);
    reg_c_out:      in  word;    
    reg_sel_y:      out std_logic_vector(4 downto 0);
    reg_write_y:    out std_logic;
    reg_y_in:       out word;
    reg_sel_z:      out std_logic_vector(4 downto 0);
    reg_write_z:    out std_logic;
    reg_z_in:       out word;

    -- interface to the ALU
    --
    alu_op:         out cpu_opcode;
    alu_rs_in:      out word;
    alu_rt_in:      out word;
    alu_rd_in:      out word;
    alu_imm_in:     out word;
    alu_output_a:   in  word;
    alu_output_b:   in  word;
    
    -- interface to the program counter
    --
    pc_in:          out word;
    pc_write:       out std_logic;
    pc_out:         in  word;
    
    dummy:          out std_logic
);
end controller;


architecture controller_arc of controller is
    
    signal PC_ff, NPC_ff:       word;
    signal IR_ff:               word;
    signal Rs_ff, Rt_ff, Rd_ff: word;
    signal Imm_unsigned_ff:     word;
    signal Imm_signed_ff:       word;
    signal ALU_out_a_ff:        word;
    signal ALU_out_b_ff:        word;
    signal LMD_ff:              word;
    
    signal OP_ff:               cpu_opcode;
    signal load_addr_ff:        word;
    signal store_addr_ff:       word;
    signal branch_addr_ff:      word;
    
    signal reg_rs_sel:          std_logic_vector(4 downto 0); 
    signal reg_rt_sel:          std_logic_vector(4 downto 0); 
    signal reg_rd_sel:          std_logic_vector(4 downto 0); 
    
    -- CPU execution cycles:
    --
    -- out_of_reset:
    --
    type cycle_type is
    (
        halted,
        out_of_reset,
        
        fetch,
        decode,
        execution,
        memory_access,
        write_back
    );
    signal cycle:       cycle_type;
    
    signal instr_fetch:         boolean;
    signal instr_is_load:       boolean;
    signal instr_is_store:      boolean;
    signal instr_is_branch:     boolean;
    signal instr_writes_back:   boolean;
    signal instr_result_dword:  boolean;
    
    signal branch_is_taken:     boolean;
    
begin
    
    -- The main state machine process
    --
    proc_cycle: process(clk, reset_n)
    begin
        if (reset_n = '0') then
            cycle <= out_of_reset;
        elsif (rising_edge(clk)) then
            case (cycle) is
                when out_of_reset =>
                    cycle <= fetch;
                
                -- When data is ready in mem_data_in, move to
                -- the decoding cycle.
                --
                when fetch =>
                    if mem_ack = '1' then
                        cycle <= decode;
                    end if;
                
                -- During the decoding cycle the instruction is
                -- taken from IR and is decoded into its 
                -- constituents.
                --
                when decode =>
                    cycle <= execution;
                
                -- During the execution cycle, the ALU does its
                -- work on the arguments taken from registers.
                --
                when execution => 
                    cycle <= memory_access;
                
                -- The memory access is for memory loads/stores.
                --
                when memory_access =>
                    if (    not (instr_is_store or instr_is_load) or 
                            mem_ack = '1') then
                        cycle <= write_back;
                    end if;
                
                when write_back =>
                    cycle <= fetch;
                
                when halted =>
                    cycle <= halted;
                
                when others =>
                    
            end case;            
        end if;
    end process;

    -- Updating the value of the program counter when in memory
    -- access cycle. The value is either changed to a branch 
    -- address for branch instructions, or just advanced by 4 for
    -- other instructions. ZZZ: what about JR?!
    --
    pc_write <= '1' when cycle = memory_access else '0';
    
    pc_in <= branch_addr_ff when instr_is_branch and branch_is_taken else 
             std_logic_vector(unsigned(PC_ff) + 4);
    
    -- Next PC 
    --
    NPC_ff <= pc_out;
    
    -- Stores the program counter for later usage
    -- 
    proc_PC_ff: process(clk, reset_n)
    begin
        if (reset_n = '0') then
            PC_ff <= NPC_ff;
        elsif (rising_edge(clk)) then
            if cycle = fetch then
                PC_ff <= NPC_ff;
            end if;
        end if;
    end process;

    -- Instruction fetch
    --
    instr_fetch <= cycle = fetch;
    
    -- Helper signals for identifying instruction types
    --
    with OP_ff select
        instr_is_load <= true when OP_LB | OP_LBU | OP_LH | OP_LHU | OP_LW,
                         false when others;

    with OP_ff select
        instr_is_store <= true when OP_SB | OP_SH | OP_SW,
                          false when others;
    
    with OP_ff select
        instr_is_branch <= true when OP_BEQ | OP_BNE | OP_BGE |
                                     OP_BGT | OP_BLE | OP_BLT | 
                                     OP_BGEU | OP_BGTU |
                                     OP_BLEU | OP_BLTU,
                           false when others; 
    
    -- instr_writes_back: an instruction that stores a result in
    -- a register
    --
    with OP_ff select 
        instr_writes_back <= true when OP_ADD | OP_ADDI | OP_SUB |
                                       OP_SUBI | OP_MULU | OP_MUL |
                                       OP_DIVU | OP_DIV | OP_LUI |
                                       OP_SLL | OP_SLLI | OP_SRL |
                                       OP_SRLI | OP_AND | OP_ANDI |
                                       OP_OR | OP_ORI | OP_NOR |
                                       OP_XOR | OP_LB | OP_LBU |
                                       OP_LH | OP_LHU | OP_LW |
                                       OP_CALL,
                             false when others;
    
    -- instr_result_dword: an instruction that produces a 64-bit 
    -- result
    --
    with OP_ff select 
        instr_result_dword <= true when OP_MUL | OP_MULU | 
                                        OP_DIV | OP_DIVU,
                              false when others;
    
    branch_is_taken <= instr_is_branch and ALU_out_a_ff(0) = '1';
    
    -- Read from memory when:
    -- * fetching an instruction
    -- * executing a load instruction
    -- 
    mem_read <= '1' when instr_fetch or 
                (cycle = memory_access and instr_is_load)
                else '0';
    
    -- Write to memory when executing a store instruction
    --
    mem_write <= '1' when cycle = memory_access and instr_is_store else '0';
    
    -- Byte select lines depend on the width of the load/store 
    -- access. For instructions, words are fetched.
    --
    mem_bytesel <= "1111" when instr_fetch else
                   "0001" when OP_ff = OP_SB or OP_ff = OP_LB or OP_ff = OP_LBU else
                   "0011" when OP_ff = OP_SH or OP_ff = OP_LH or OP_ff = OP_LHU else
                   "1111" when OP_ff = OP_LW or OP_ff = OP_SW else
                   "0000";
    
    -- Memory address
    -- 
    mem_addr <= NPC_ff when instr_fetch else
                load_addr_ff when cycle = memory_access and instr_is_load else
                store_addr_ff when cycle = memory_access and instr_is_store                
                else (others => '0');

    -- Memory data in is taken from Rs in store instructions
    --
    mem_data_out <= Rs_ff;

    -- The instruction register holds the current instruction 
    -- read from the memory.
    -- Since the memory outputs are synchronous, IR_ff is just an
    -- alias. It will be read only on rising_edge(clk), so it 
    -- really represents a register.
    --
    IR_ff <= mem_data_in;
    
    -- The opcode
    --
    proc_OP_ff: process(clk, reset_n)
    begin
        if (reset_n = '0') then
            OP_ff <= (others => '0');
        elsif (rising_edge(clk)) then
            OP_ff <= IR_ff(31 downto 26);
        end if;
    end process;

    reg_rd_sel <= IR_ff(25 downto 21);
    reg_rs_sel <= IR_ff(20 downto 16);
    reg_rt_sel <= IR_ff(15 downto 11);
    
    reg_sel_a <= reg_rd_sel;
    reg_sel_b <= reg_rs_sel;
    reg_sel_c <= reg_rt_sel;

    -- The unsigned (zero-extended) and signed (sign-extended)
    -- interpretations of the immediate value.
    -- Both are delayed by a clock cycle to be ready in the same
    -- cycle with the values of registers.
    --
    proc_Imm_ff: process(clk, reset_n)
    begin
        if (reset_n = '0') then
            Imm_unsigned_ff <= (others => '0');
            Imm_signed_ff <= (others => '0');
        elsif (rising_edge(clk)) then
            Imm_unsigned_ff <= std_logic_vector(resize(unsigned(IR_ff(15 downto 0)), 32));
            Imm_signed_ff <= std_logic_vector(resize(signed(IR_ff(15 downto 0)), 32));
        end if;
    end process;
    
    -- Contents of registers. 
    --
    Rd_ff <= reg_a_out;
    Rs_ff <= reg_b_out;
    Rt_ff <= reg_c_out;
    
    -- ALU arguments and outputs
    --
    alu_op <= OP_ff;
    alu_rs_in <= Rs_ff;
    alu_rt_in <= Rt_ff;
    alu_rd_in <= Rd_ff;
    alu_imm_in <= Imm_unsigned_ff;
    
    ALU_out_a_ff <= alu_output_a;
    ALU_out_b_ff <= alu_output_b;
    
    -- load and store addresses, computed during the execution
    -- cycle.
    --
    proc_load_addr_ff: process(clk, reset_n)
    begin
        if (reset_n = '0') then
            load_addr_ff <= (others => '0');
        elsif (rising_edge(clk)) then
            load_addr_ff <= std_logic_vector(signed(Rs_ff) + signed(Imm_signed_ff));
        end if;
    end process;
    
    proc_store_addr_ff: process(clk, reset_n)
    begin
        if (reset_n = '0') then
            store_addr_ff <= (others => '0');
        elsif (rising_edge(clk)) then
            store_addr_ff <= std_logic_vector(signed(Rd_ff) + signed(Imm_signed_ff));
        end if;
    end process;
    
    -- Loaded memory data
    --
    LMD_ff <= mem_data_in;
    
    -- branch address, computed during the execution cycle.
    --
    proc_branch_addr_ff: process(clk, reset_n)
    begin
        if (reset_n = '0') then
            branch_addr_ff <= (others => '0');
        elsif (rising_edge(clk)) then
            if cycle = execution then
                branch_addr_ff <= std_logic_vector(signed(PC_ff) + shift_left(signed(Imm_signed_ff), 2));
            end if;
        end if;
    end process;
    
    -- writing to registers
    --
    reg_y_in <= ALU_out_a_ff;
    reg_z_in <= ALU_out_b_ff;
    
    -- Port y is Rd
    -- Port z is R(d+1) unless d is 31
    --
    reg_sel_y <= reg_rd_sel;
    reg_sel_z <= (others => '0') when unsigned(reg_rd_sel) = 31 else
                 std_logic_vector(unsigned(reg_rd_sel) + 1);

    reg_write_y <= '1' when (cycle = write_back and 
                             instr_writes_back and 
                             unsigned(reg_rd_sel) /= 0) 
                    else '0';

    reg_write_z <= '1' when (cycle = write_back and 
                             instr_result_dword and 
                             unsigned(reg_rd_sel) /= 31)
                    else '0';    
    
end;



