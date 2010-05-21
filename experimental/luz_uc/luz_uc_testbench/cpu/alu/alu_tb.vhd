library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
library work;
use work.cpu_defs.all;


entity alu_tb is end;

architecture alu_tb_arc of alu_tb is

    signal clk:     std_logic := '0';
    signal reset_n: std_logic;
    signal op:      alu_operation;
    signal arg1:    std_logic_vector(31 downto 0);
    signal arg2:    std_logic_vector(31 downto 0);
    signal output_a:    std_logic_vector(31 downto 0);
    signal output_b:    std_logic_vector(31 downto 0);
begin
    clk <= not clk after 13 ns;
    reset_n <= '0', '1' after 100 ns;

    process
    begin
        arg1 <= x"82000064";
        arg2 <= x"0000DE70";
        op <= ALU_SLL;
        wait for 800 ns;
        op <= ALU_SRL;
        wait for 800 ns;
        op <= ALU_CMP_GT;
        wait for 800 ns;
        op <= ALU_CMP_NE;
        
        wait;
    end process;

    uut: entity work.alu(alu_arc)
    port map
    (
        clk        => clk,
        reset_n    => reset_n,
        op         => op,
        arg1       => arg1,
        arg2       => arg2,
        output_a     => output_a,
        output_b     => output_b
    );
end;

