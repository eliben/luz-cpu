-- CPU core registers.
--
-- Luz micro-controller implementation
-- Eli Bendersky (C) 2008-2010
--
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.cpu_defs.all;


-- The core registers are simply a set of registers accessible
-- by the CPU through read/write register ports, and also 
-- accessible from the uC bus.
-- 
-- Register port interface: similar to the generic registers
-- module, just with a single read and single write port.
-- 
-- uC bus interface: standard and allows access to a single 
-- register at a time, according to the memory mapping defined in
-- the cpu_defs package. The address width of the internal memory 
-- mapping of this module is 12 bits.
-- Accesses are assumed to be aligned at word boundaries. 
-- Therefore, bits 1:0 of adr_i are ignored, and the sel_i signal
-- is ignored.
--
entity core_regs is 
port
(
    clk:            in  std_logic;
    reset_n:        in  std_logic;
    
    -- Register ports interface
    --
    
    -- read port
    read_port_sel:  in  core_reg_sel;
    read_port_out:  out word;
    
    -- write port
    write_port_wr:  in  std_logic;
    write_port_sel: in  core_reg_sel;
    write_port_in:  in  word;

    -- Bus interface
    --
    cyc_i:          in  std_logic;
    stb_i:          in  std_logic;
    we_i:           in  std_logic;
    sel_i:          in  std_logic_vector(3 downto 0);  -- unused
    adr_i:          in  core_reg_addr;
    data_i:         in  std_logic_vector(31 downto 0);
    ack_o:          out std_logic;
    err_o:          out std_logic;
    data_o:         out std_logic_vector(31 downto 0)
);
end core_regs;


architecture core_regs_arc of core_regs is
    signal bus_strobe:      std_logic;
    signal bus_write:       std_logic;

    signal sel_b_sig:       core_reg_sel;
    signal reg_b_out_sig:   word;
    signal sel_z_sig:       core_reg_sel;
    signal write_z_sig:     std_logic;
    signal reg_z_in_sig:    word;
    
    signal write_to_readonly:   boolean;
begin

    registers_map: entity work.registers(registers_arc)
    generic map
    (
        NREGS_LOG2      => NCORE_REGS_LOG2
    )
    port map
    (
        clk             => clk,
        reset_n         => reset_n,
        sel_a           => read_port_sel,
        reg_a_out       => read_port_out,
        sel_b           => sel_b_sig,
        reg_b_out       => reg_b_out_sig,
        sel_c           => (others => '0'),
        reg_c_out       => open, 
        sel_y           => write_port_sel,
        write_y         => write_port_wr,
        reg_y_in        => write_port_in,
        sel_z           => sel_z_sig,
        write_z         => write_z_sig,
        reg_z_in        => reg_z_in_sig
    );

    bus_strobe <= stb_i and cyc_i;
    bus_write <= bus_strobe and we_i;

    write_to_readonly <= bus_write = '1' and (  adr_i = x"108" or 
                                                adr_i = x"10C" or
                                                adr_i = x"124");    

    -- Synchronous single-cycle access
    proc_ack_err: process(clk, reset_n)
    begin
    
        if (reset_n = '0') then
            ack_o <= '0';
            err_o <= '0';
        elsif (rising_edge(clk)) then
            -- We're in error if an inexistent register is 
            -- accessed or a write is attempted into a read-only
            -- register
            --
            if bus_strobe = '1' and (sel_z_sig = x"0" or write_to_readonly) then
                ack_o <= '0';
                err_o <= '1';
            else
                ack_o <= bus_strobe;
                err_o <= '0';
            end if;
        end if;
    end process;

    -- uC bus reads are done from port B
    data_o <= reg_b_out_sig;
    sel_b_sig <= addr2core_reg_map(adr_i);

    -- uC bus writes are done into port Z
    reg_z_in_sig <= data_i;
    write_z_sig <= '1' when bus_write = '1' and not write_to_readonly else '0';
    sel_z_sig <= addr2core_reg_map(adr_i);

end core_regs_arc;

