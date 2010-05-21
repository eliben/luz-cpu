library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
library work;
use work.cpu_defs.all;


entity luz_cpu_tb is end;

architecture luz_cpu_tb_arc of luz_cpu_tb is
    constant RESET_ADDRESS: word := x"00000000";

    signal clk:     std_logic := '0';
    signal reset_n: std_logic;
    signal ack_i:   std_logic;
    signal cyc_o:   std_logic;
    signal stb_o:   std_logic;
    signal we_o:    std_logic;
    signal sel_o:   std_logic_vector(3 downto 0);
    signal adr_o:   std_logic_vector(31 downto 0);
    signal data_o:  std_logic_vector(31 downto 0);
    signal data_i:  std_logic_vector(31 downto 0);
    signal irq_i:   std_logic_vector(31 downto 0);
    signal halt:    std_logic;
    signal ifetch:  std_logic;
begin
    clk <= not clk after 13 ns;
    reset_n <= '0', '1' after 100 ns;

    process
    begin
        
        wait;
    end process;

    uut: entity work.luz_cpu(luz_cpu_arc)
    generic map
    (
        RESET_ADDRESS    => RESET_ADDRESS
    )
    port map
    (
        clk        => clk,
        reset_n    => reset_n,
        ack_i      => ack_i,
        cyc_o      => cyc_o,
        stb_o      => stb_o,
        we_o       => we_o,
        sel_o      => sel_o,
        adr_o      => adr_o,
        data_o     => data_o,
        data_i     => data_i,
        irq_i      => irq_i,
        halt       => halt,
        ifetch     => ifetch
    );
end;

