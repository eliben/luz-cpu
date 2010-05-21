library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.cpu_defs.all;


entity registers_tb is end;

architecture registers_tb_arc of registers_tb is

    signal clk:         std_logic := '0';
    signal reset_n:     std_logic;
    signal sel_a:       std_logic_vector(4 downto 0);
    signal reg_a_out:   std_logic_vector(31 downto 0);
    signal sel_b:       std_logic_vector(4 downto 0);
    signal reg_b_out:   std_logic_vector(31 downto 0);
    signal sel_c:       std_logic_vector(4 downto 0);
    signal write_c:     std_logic;
    signal reg_c_in:    std_logic_vector(31 downto 0);
    signal sel_d:       std_logic_vector(4 downto 0);
    signal write_d:     std_logic;
    signal reg_d_in:    std_logic_vector(31 downto 0);
begin
    clk <= not clk after 13 ns;
    reset_n <= '0', '1' after 100 ns;

    process
    
        procedure write_c_reg(data: std_logic_vector(31 downto 0); sel: std_logic_vector(4 downto 0))is
        begin
            reg_c_in <= data;
            sel_c <= sel;
            write_c <= '1';
            wait until rising_edge(clk); wait for 1 ns;
            write_c <= '0';
            wait for 1 ns;
        end procedure write_c_reg;
        
    
    begin
        sel_a <= (others => '0');
        sel_b <= (others => '0');
        sel_c <= (others => '0');
        reg_c_in <= (others => '0');
        write_c <= '0';
        wait for 140 ns;
        
        write_c_reg(x"ABCDEF01", "00110");
        write_c_reg(x"12345678", "10110");
        write_c_reg(x"F1E2D3C4", "00001");
        
        wait for 200 ns;
       
        sel_a <= "00001";
        sel_b <= "10110";
        
        wait for 37 ns;
        
        -- read and write on the same cycle
        sel_b <= "00110";
        write_c_reg(x"555DEF01", "00110");
        
        wait;
    end process;

    uut: entity work.registers(registers_arc)
    generic map 
    (
        NREGS_LOG2  => 5
    )
    port map
    (
        clk         => clk,
        reset_n     => reset_n,
        sel_a       => sel_a,
        reg_a_out   => reg_a_out,
        sel_b       => sel_b,
        reg_b_out   => reg_b_out,
        sel_c       => sel_c,
        write_c     => write_c,
        reg_c_in    => reg_c_in,
        sel_d       => sel_d,
        write_d     => write_d,
        reg_d_in    => reg_d_in
    );
end;

