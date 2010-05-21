-- Luz uC memory mapper - connects the internal Wishbone bus 
-- between the CPU, user memory, and the various peripherals.
-- Serves as a crossbar, routing bus transactions from the CPU
-- to different modules depending on address mapping.
--
-- Luz micro-controller implementation
-- Eli Bendersky (C) 2008-2010
--
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.cpu_defs.all;


entity memorymapper is 
port
(
    clk:        in  std_logic;
    reset_n:    in  std_logic;
    
    -- CPU master port
    --
    cpu_cyc_o:  in  std_logic;
    cpu_stb_o:  in  std_logic;
    cpu_we_o:   in  std_logic;
    cpu_sel_o:  in  std_logic_vector(3 downto 0);
    cpu_adr_o:  in  word;
    cpu_data_o: in  word;
    cpu_ack_i:  out std_logic;
    cpu_err_i:  out std_logic;
    cpu_data_i: out word;
    
    -- User memory slave port
    --
    mem_cyc_i:  out std_logic;
    mem_stb_i:  out std_logic;
    mem_we_i:   out std_logic;
    mem_sel_i:  out std_logic_vector(3 downto 0);
    mem_adr_i:  out std_logic_vector(17 downto 0);
    mem_data_i: out word;
    mem_ack_o:  in  std_logic;
    mem_err_o:  in  std_logic;
    mem_data_o: in  word;

    -- Core registers slave port
    --
    core_reg_cyc_i:     out std_logic;
    core_reg_stb_i:     out std_logic;
    core_reg_we_i:      out std_logic;
    core_reg_sel_i:     out std_logic_vector(3 downto 0);
    core_reg_adr_i:     out std_logic_vector(11 downto 0);
    core_reg_data_i:    out word;
    core_reg_ack_o:     in  std_logic;
    core_reg_err_o:     in  std_logic;
    core_reg_data_o:    in  word
);
end memorymapper;


architecture memorymapper_arc of memorymapper is

    signal bus_strobe:  std_logic;
    
    signal core_reg_access:         boolean;
    signal mem_access:              boolean;
    
begin

    bus_strobe <= cpu_cyc_o and cpu_stb_o;
    
    core_reg_access <=  bus_strobe = '1' and
                        cpu_adr_o >= CORE_REG_ADDR_START and
                        cpu_adr_o <= CORE_REG_ADDR_END;
    
    mem_access <=   bus_strobe = '1' and 
                    cpu_adr_o >= MEM_ADDR_START and
                    cpu_adr_o <= MEM_ADDR_END;

    --
    -- Signals from master to slaves
    --

    mem_cyc_i   <= cpu_cyc_o when mem_access else '0';
    mem_stb_i   <= cpu_stb_o when mem_access else '0';
    mem_we_i    <= cpu_we_o when mem_access else '0';
    mem_sel_i   <= cpu_sel_o;
    mem_adr_i   <= cpu_adr_o(MEM_ADDR_SIZE - 1 downto 0);
    mem_data_i  <= cpu_data_o;
    
    core_reg_cyc_i  <= cpu_cyc_o when core_reg_access else '0';
    core_reg_stb_i  <= cpu_stb_o when core_reg_access else '0';
    core_reg_we_i   <= cpu_we_o when core_reg_access else '0';
    core_reg_sel_i  <= cpu_sel_o;
    core_reg_adr_i  <= cpu_adr_o(CORE_REG_ADDR_SIZE - 1 downto 0);
    core_reg_data_i <= cpu_data_o;
    
    --
    -- Signals from slaves to master
    --
    
    cpu_ack_i   <=  mem_ack_o when mem_access else
                    core_reg_ack_o when core_reg_access else
                    '0';
    
    cpu_err_i   <=  mem_err_o when mem_access else
                    core_reg_err_o when core_reg_access else
                    '1';

    cpu_data_i  <=  mem_data_o when mem_access else
                    core_reg_data_o when core_reg_access else
                    (others => '0');
    
end;

