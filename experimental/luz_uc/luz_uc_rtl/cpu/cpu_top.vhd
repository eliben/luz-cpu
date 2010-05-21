-- CPU core top-level entity
--
-- Luz micro-controller implementation
-- Eli Bendersky (C) 2008-2010
--
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.cpu_defs.all;


entity luz_cpu is 
generic
(
    RESET_ADDRESS:  word
);
port
(
    clk:            in  std_logic;
    reset_n:        in  std_logic;
    
    -- Standard Wishbone signals
    --
    cyc_o:          out std_logic;
    stb_o:          out std_logic;
    we_o:           out std_logic;
    sel_o:          out std_logic_vector(3 downto 0);
    adr_o:          out word;
    data_o:         out word;
    ack_i:          in  std_logic;
    err_i:          in  std_logic;
    data_i:         in  word;

    -- IRQs
    --
    irq_i:          in  word;
    
    -- '1' when the CPU executes the 'halt' instruction
    --
    halt:           out std_logic;
    
    -- '1' when the CPU fetches an instruction from the bus
    --
    ifetch:         out std_logic;
    
    -- core regs ports
    --
    core_reg_read_sel:      out core_reg_sel;
    core_reg_read_data:     in  word;
    
    core_reg_write_sel:     out core_reg_sel;
    core_reg_write_strobe:  out std_logic;
    core_reg_write_data:    out word
);
end luz_cpu;


architecture luz_cpu_arc of luz_cpu is
    
    signal mem_read:        std_logic;
    signal mem_write:       std_logic;
    signal mem_bytesel:     std_logic_vector(3 downto 0);
    signal mem_addr:        word;
    signal mem_data_out:    word;
    signal mem_ack:         std_logic;
    signal mem_data_in:     word;
    signal reg_sel_a:       std_logic_vector(4 downto 0);
    signal reg_a_out:       word;
    signal reg_sel_b:       std_logic_vector(4 downto 0);
    signal reg_b_out:       word;
    signal reg_sel_c:       std_logic_vector(4 downto 0);
    signal reg_c_out:       word;
    signal reg_sel_y:       std_logic_vector(4 downto 0);
    signal reg_write_y:     std_logic;
    signal reg_y_in:        word;
    signal reg_sel_z:       std_logic_vector(4 downto 0);
    signal reg_write_z:     std_logic;
    signal reg_z_in:        word;
    signal alu_op:          cpu_opcode;
    signal alu_rs_in:       word;
    signal alu_rd_in:       word;
    signal alu_rt_in:       word;
    signal alu_imm_in:      word;
    signal alu_output_a:    word;
    signal alu_output_b:    word;
    signal pc_in:           word;
    signal pc_out:          word;
    signal pc_write:        std_logic;
    
begin

    controller_map: entity work.controller(controller_arc)
    port map
    (
        clk             => clk,
        reset_n         => reset_n,
        mem_read        => mem_read,
        mem_write       => mem_write,
        mem_bytesel     => mem_bytesel,
        mem_addr        => mem_addr,
        mem_data_out    => mem_data_out,
        mem_ack         => mem_ack,
        mem_data_in     => mem_data_in,
        reg_sel_a       => reg_sel_a,
        reg_a_out       => reg_a_out,
        reg_sel_b       => reg_sel_b,
        reg_b_out       => reg_b_out,
        reg_sel_c       => reg_sel_c,
        reg_c_out       => reg_c_out,
        reg_sel_y       => reg_sel_y,
        reg_write_y     => reg_write_y,
        reg_y_in        => reg_y_in,
        reg_sel_z       => reg_sel_z,
        reg_write_z     => reg_write_z,
        reg_z_in        => reg_z_in,
        alu_op          => alu_op,
        alu_rs_in       => alu_rs_in,
        alu_rd_in       => alu_rd_in,
        alu_rt_in       => alu_rt_in,
        alu_imm_in      => alu_imm_in,
        alu_output_a    => alu_output_a,
        alu_output_b    => alu_output_b,
        pc_in           => pc_in,
        pc_out          => pc_out,
        pc_write        => pc_write
    );
    
    -- Bridging the controller memory interface to Wishbone
    --
    mem_ack         <= ack_i;
    mem_data_in     <= data_i;
    cyc_o           <= mem_write or mem_read;
    stb_o           <= mem_write or mem_read;
    we_o            <= mem_write;
    sel_o           <= mem_bytesel;
    adr_o           <= mem_addr;
    data_o          <= mem_data_out;    

    alu_map: entity work.alu(alu_arc)
    port map
    (
        clk         => clk,
        reset_n     => reset_n,
        op          => alu_op,
        rs_in       => alu_rs_in,
        rt_in       => alu_rt_in,
        rd_in       => alu_rd_in,
        imm_in      => alu_imm_in,
        output_a    => alu_output_a,
        output_b    => alu_output_b
    );

    gp_registers_map: entity work.registers(registers_arc)
    generic map
    (
        NREGS_LOG2      => 5
    )
    port map
    (
        clk             => clk,
        reset_n         => reset_n,
        sel_a           => reg_sel_a,
        reg_a_out       => reg_a_out,
        sel_b           => reg_sel_b,
        reg_b_out       => reg_b_out,
        sel_c           => reg_sel_c,
        reg_c_out       => reg_c_out,
        sel_y           => reg_sel_y,
        write_y         => reg_write_y,
        reg_y_in        => reg_y_in,
        sel_z           => reg_sel_z,
        write_z         => reg_write_z,
        reg_z_in        => reg_z_in
    );

    pc_map: entity work.program_counter(program_counter_arc)
    generic map
    (
        INIT        => RESET_ADDRESS
    )
    port map
    (
        clk         => clk,
        reset_n     => reset_n,
        pc_in       => pc_in,
        pc_out      => pc_out,
        pc_write    => pc_write
    );

end;


