library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
library work;
use work.cpu_defs.all;


entity core_regs_tb is end;

architecture core_regs_tb_arc of core_regs_tb is

    signal clk:         std_logic := '0';
    signal reset_n:     std_logic;
    signal sel_a:       core_reg_sel;
    signal reg_a_out:   word;
    signal sel_c:       core_reg_sel;
    signal write_c:     std_logic;
    signal reg_c_in:    word;
    signal ack_o:       std_logic;
    signal err_o:       std_logic;
    signal cyc_i:       std_logic;
    signal stb_i:       std_logic;
    signal we_i:        std_logic;
    signal sel_i:       std_logic_vector(3 downto 0);
    signal adr_i:       core_reg_addr;
    signal data_o:      std_logic_vector(31 downto 0);
    signal data_i:      std_logic_vector(31 downto 0);

begin
    clk <= not clk after 14 ns;
    reset_n <= '0', '1' after 100 ns;

    process
        -- Simulates an access through the memory bus interface
        --
        procedure mem_access(   adr: core_reg_addr;
                                we: std_logic;
                                data: std_logic_vector(31 downto 0) := x"00000000") is
        begin
            stb_i <= '1';
            cyc_i <= '1';
            we_i <= we;
            adr_i <= adr;
            data_i <= data;
            wait until rising_edge(clk);
            wait for 1 ns;
            stb_i <= '0';
            cyc_i <= '0';
            wait for 1 ns;
        end procedure mem_access;
    begin
        -- init uC interface signals
        cyc_i <= '0';
        stb_i <= '0';
        we_i <= '0';
        sel_i <= (others => '0');
        adr_i <= (others => '0');
        data_i <= (others => '0');
        
        -- init register port interface signals
        sel_a <= (others => '0');
        sel_c <= (others => '0');
        write_c <= '0';
        reg_c_in <= (others => '0');
        
        wait for 203 ns;
        ------------------- **** -------------------

        mem_access(x"004", '1', x"ABDA1002");
        mem_access(x"120", '1', x"23456890");
        
        -- write through register port 
        write_c <= '1';
        reg_c_in <= x"55667788";
        sel_c <= x"B";
        wait until rising_edge(clk);
        wait for 1 ns;
        write_c <= '0';
        
        -- write to readonly reg: should cause an error
        mem_access(x"108", '1', x"55112231");
        
        -- read from valid place
        mem_access(x"120", '0');
        
        -- read from invalid place
        mem_access(x"180", '0');

        wait;
    end process;

    dut: entity work.core_regs(core_regs_arc)
    port map
    (
        clk         => clk,
        reset_n     => reset_n,
        sel_a       => sel_a,
        reg_a_out   => reg_a_out,
        sel_c       => sel_c,
        write_c     => write_c,
        reg_c_in    => reg_c_in,
        ack_o       => ack_o,
        err_o       => err_o,
        cyc_i       => cyc_i,
        stb_i       => stb_i,
        we_i        => we_i,
        sel_i       => sel_i,
        adr_i       => adr_i,
        data_o      => data_o,
        data_i      => data_i
    );
end;

