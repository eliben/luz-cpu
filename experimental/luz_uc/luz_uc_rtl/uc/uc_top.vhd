-- Luz uC top-level entity
--
-- Luz micro-controller implementation
-- Eli Bendersky (C) 2008-2010
--
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.cpu_defs.all;


entity luz_uc is 
port
(
    clk:        in  std_logic;
    reset_n:    in  std_logic;
    
    -- '1' when the CPU executes the 'halt' instruction
    --
    halt:       out std_logic
);
end luz_uc;


architecture luz_uc_arc of luz_uc is

    signal cpu_cyc_o:   std_logic;
    signal cpu_stb_o:   std_logic;
    signal cpu_we_o:    std_logic;
    signal cpu_sel_o:   std_logic_vector(3 downto 0);
    signal cpu_adr_o:   word;
    signal cpu_data_o:  word;
    signal cpu_ack_i:   std_logic;
    signal cpu_err_i:   std_logic;
    signal cpu_data_i:  word;
    signal cpu_irq_i:   word;
    signal cpu_halt:    std_logic;
    signal cpu_ifetch:  std_logic;
    
    signal cpu_core_reg_read_sel:       core_reg_sel;
    signal cpu_core_reg_read_data:      word;
    signal cpu_core_reg_write_sel:      core_reg_sel;
    signal cpu_core_reg_write_strobe:   std_logic;
    signal cpu_core_reg_write_data:     word;

    signal mem_cyc_i:   std_logic;
    signal mem_stb_i:   std_logic;
    signal mem_we_i:    std_logic;
    signal mem_sel_i:   std_logic_vector(3 downto 0);
    signal mem_adr_i:   std_logic_vector(MEM_ADDR_SIZE - 1 downto 0);
    signal mem_data_i:  word;
    signal mem_ack_o:   std_logic;
    signal mem_err_o:   std_logic;
    signal mem_data_o:  word;

    signal core_reg_cyc_i:  std_logic;
    signal core_reg_stb_i:  std_logic;
    signal core_reg_we_i:   std_logic;
    signal core_reg_sel_i:  std_logic_vector(3 downto 0);
    signal core_reg_adr_i:  std_logic_vector(11 downto 0);
    signal core_reg_data_i: word;
    signal core_reg_ack_o:  std_logic;
    signal core_reg_err_o:  std_logic;
    signal core_reg_data_o: word;
    
begin
    
    cpu_map: entity work.luz_cpu(luz_cpu_arc)
    generic map
    (
        RESET_ADDRESS   => MEM_ADDR_START
    )
    port map
    (
        clk                     => clk,
        reset_n                 => reset_n,
        cyc_o                   => cpu_cyc_o,
        stb_o                   => cpu_stb_o,
        we_o                    => cpu_we_o,
        sel_o                   => cpu_sel_o,
        adr_o                   => cpu_adr_o,
        data_o                  => cpu_data_o,
        ack_i                   => cpu_ack_i,
        err_i                   => cpu_err_i,
        data_i                  => cpu_data_i,
        irq_i                   => cpu_irq_i,
        halt                    => cpu_halt,
        ifetch                  => cpu_ifetch,
        core_reg_read_sel       => cpu_core_reg_read_sel,
        core_reg_read_data      => cpu_core_reg_read_data,
        core_reg_write_sel      => cpu_core_reg_write_sel,
        core_reg_write_strobe   => cpu_core_reg_write_strobe,
        core_reg_write_data     => cpu_core_reg_write_data
    );

    memorymapper_map: entity work.memorymapper(memorymapper_arc)
    port map
    (
        clk                 => clk,
        reset_n             => reset_n,
        cpu_cyc_o           => cpu_cyc_o,
        cpu_stb_o           => cpu_stb_o,
        cpu_we_o            => cpu_we_o,
        cpu_sel_o           => cpu_sel_o,
        cpu_adr_o           => cpu_adr_o,
        cpu_data_o          => cpu_data_o,
        cpu_ack_i           => cpu_ack_i,
        cpu_err_i           => cpu_err_i,
        cpu_data_i          => cpu_data_i,
        mem_cyc_i           => mem_cyc_i,
        mem_stb_i           => mem_stb_i,
        mem_we_i            => mem_we_i,
        mem_sel_i           => mem_sel_i,
        mem_adr_i           => mem_adr_i,
        mem_data_i          => mem_data_i,
        mem_ack_o           => mem_ack_o,
        mem_err_o           => mem_err_o,
        mem_data_o          => mem_data_o,
        core_reg_cyc_i      => core_reg_cyc_i,
        core_reg_stb_i      => core_reg_stb_i,
        core_reg_we_i       => core_reg_we_i,
        core_reg_sel_i      => core_reg_sel_i,
        core_reg_adr_i      => core_reg_adr_i,
        core_reg_data_i     => core_reg_data_i,
        core_reg_ack_o      => core_reg_ack_o,
        core_reg_err_o      => core_reg_err_o,
        core_reg_data_o     => core_reg_data_o
    );
    
    core_regs_map: entity work.core_regs(core_regs_arc)
    port map
    (
        clk             => clk,
        reset_n         => reset_n,
        read_port_sel   => cpu_core_reg_read_sel,
        read_port_out   => cpu_core_reg_read_data,
        write_port_sel  => cpu_core_reg_write_sel,
        write_port_wr   => cpu_core_reg_write_strobe,
        write_port_in   => cpu_core_reg_write_data,
        ack_o           => core_reg_ack_o,
        err_o           => core_reg_err_o,
        cyc_i           => core_reg_cyc_i,
        stb_i           => core_reg_stb_i,
        we_i            => core_reg_we_i,
        sel_i           => core_reg_sel_i,
        adr_i           => core_reg_adr_i,
        data_o          => core_reg_data_o,
        data_i          => core_reg_data_i
    );
    
    user_memory_map: entity work.user_memory(user_memory_arc)
    port map
    (
        clk         => clk,
        reset_n     => reset_n,
        cyc_i       => mem_cyc_i,
        stb_i       => mem_stb_i,
        we_i        => mem_we_i,
        sel_i       => mem_sel_i,
        adr_i       => mem_adr_i,
        data_i      => mem_data_i,
        data_o      => mem_data_o,
        ack_o       => mem_ack_o,
        err_o       => mem_err_o
    );

end;
