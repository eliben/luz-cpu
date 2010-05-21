-- Generic registers file.
--
-- Luz micro-controller implementation
-- Eli Bendersky (C) 2008-2010
--
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.cpu_defs.all;


-- 5-port (three reads, two writes on the same clock cycle) 
-- The registers file is completely synchronous. Therefore, read
-- before write is possible on the same cycle into the same
-- register.
--
-- Read ports: A, B, C
--  sel_a/b/c selects which register to output to A/B/C
--  The contents of the selected register will appear on the data
--  lines of the port in the next clock cycle.
--
-- Write ports: Y and Z
--  sel_y/z selects which register to write
--  write_y/z is a strobe to activate writing
--
entity registers is 
generic
(
    -- Number of registers: 2**NREGS_LOG2
    --
    NREGS_LOG2:     natural := 5
);
port
(
    clk:            in  std_logic;
    reset_n:        in  std_logic;
    
    sel_a:          in  std_logic_vector(NREGS_LOG2 - 1 downto 0);
    reg_a_out:      out word;
    
    sel_b:          in  std_logic_vector(NREGS_LOG2 - 1 downto 0);
    reg_b_out:      out word;
    
    sel_c:          in  std_logic_vector(NREGS_LOG2 - 1 downto 0);
    reg_c_out:      out word;
    
    sel_y:          in  std_logic_vector(NREGS_LOG2 - 1 downto 0);
    write_y:        in  std_logic;
    reg_y_in:       in  word;

    sel_z:          in  std_logic_vector(NREGS_LOG2 - 1 downto 0);
    write_z:        in  std_logic;
    reg_z_in:       in  word
);
end registers;


architecture registers_arc of registers is
    
    type register_file_type is array(natural range 0 to 2**NREGS_LOG2 - 1) of word;
    signal register_file:   register_file_type;
    
begin
    
    proc_regs_out: process(clk, reset_n)
    begin
        if (reset_n = '0') then
            reg_a_out <= (others => '0');
            reg_b_out <= (others => '0');
            reg_c_out <= (others => '0');
        elsif (rising_edge(clk)) then
            reg_a_out <= register_file(to_integer(unsigned(sel_a)));
            reg_b_out <= register_file(to_integer(unsigned(sel_b)));
            reg_c_out <= register_file(to_integer(unsigned(sel_c)));
        end if;
    end process;
    
    proc_regs_in: process(clk, reset_n)
    begin
        if (reset_n = '0') then
            for i in 0 to 2**NREGS_LOG2 - 1 loop
                register_file(i) <= (others => '0');
            end loop;
        elsif (rising_edge(clk)) then
            if (write_y = '1') then
                register_file(to_integer(unsigned(sel_y))) <= reg_y_in;
            end if;

            if (write_z = '1') then
                register_file(to_integer(unsigned(sel_z))) <= reg_z_in;
            end if;
        end if;
    end process;    
end;


