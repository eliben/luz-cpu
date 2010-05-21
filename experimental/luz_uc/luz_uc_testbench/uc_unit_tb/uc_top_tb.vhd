library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
library work;
use work.cpu_defs.all;


entity luz_uc_tb is end;

architecture luz_uc_tb_arc of luz_uc_tb is

    signal clk:     std_logic := '0';
    signal reset_n: std_logic;
    signal halt:    std_logic;

begin
    clk <= not clk after 14 ns;
    reset_n <= '0', '1' after 100 ns;

    process
    begin
        
        wait;
    end process;

    dut: entity work.luz_uc(luz_uc_arc)
    port map
    (
        clk         => clk,
        reset_n     => reset_n,
        halt        => halt
    );
end;

