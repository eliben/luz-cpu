-- Program counter (PC)
--
-- Luz micro-controller implementation
-- Eli Bendersky (C) 2008-2010
--
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.cpu_defs.all;


-- Implementes the program counter with the initial value INIT.
--
-- Its current value is always reflected to pc_out.
-- The value is overwritten with pc_in on clock cycles where 
-- pc_write is '1'.
--
entity program_counter is 
generic
(
    INIT:   word
);
port
(
    clk:        in  std_logic;
    reset_n:    in  std_logic;
    
    pc_in:      in  word;
    pc_out:     out word;
    pc_write:   in  std_logic
);
end program_counter;


architecture program_counter_arc of program_counter is
    signal pc:  word;
begin
    pc_out <= pc;
    
    proc_pc: process(clk, reset_n)
    begin
        if (reset_n = '0') then
            pc <= INIT;
        elsif (rising_edge(clk)) then
            if pc_write = '1' then
                pc <= pc_in;
            end if;
        end if;
    end process;
end;
