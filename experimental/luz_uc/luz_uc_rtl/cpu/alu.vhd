-- The arithmetic-logic unit (ALU)
--
-- Luz micro-controller implementation
-- Eli Bendersky (C) 2008-2010
--
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.cpu_defs.all;
use work.utils_pak.all;


-- The 'op' input tells the ALU which operation to perform 
-- in this clock cycle. Its value is one of the OP_... 
-- constants in the cpu_defs package.
--
-- The output consists of two words:
--
--> For MUL and MULU, output_a is the low 32 bits of the
--  result, and output_b the high 32 bits of the result.
--> For DIV and DIVU, output_a is the quotient of the 
--  division, and output_b the remainder.
--> For comparison operations, the lowest bit of output_a
--  is set if the comparison yields TRUE. 
--> For all other operations, the result is stored into 
--  output_a.
--
entity alu is 
port
(
    clk:            in  std_logic;
    reset_n:        in  std_logic;
    
    op:             in  cpu_opcode;
    
    rs_in:          in  word;
    rt_in:          in  word;
    rd_in:          in  word;
    imm_in:         in  word;
    
    output_a:       out word;
    output_b:       out word
);
end alu;


architecture alu_arc of alu is
begin
    proc_output: process(clk, reset_n)
        variable temp: doubleword;
    begin
        if (reset_n = '0') then
            output_a <= (others => '0');
            output_b <= (others => '0');
        elsif (rising_edge(clk)) then
            -- Default values. This is convenient in particular 
            -- for output_b which is written only for very few
            -- instructions.
            --
            output_a <= (others => '0');
            output_b <= (others => '0');
        
            case op is
                when OP_ADD =>
                    output_a <= std_logic_vector(unsigned(rs_in) + unsigned(rt_in));
                
                when OP_ADDI =>
                    output_a <= std_logic_vector(unsigned(rs_in) + unsigned(imm_in));
                
                when OP_SUB =>
                    output_a <= std_logic_vector(unsigned(rs_in) - unsigned(rt_in));
                
                when OP_SUBI =>
                    output_a <= std_logic_vector(unsigned(rs_in) - unsigned(imm_in));
                    
                when OP_MUL =>
                    temp := std_logic_vector(signed(rs_in) * signed(rt_in));
                    output_a <= temp(31 downto 0);
                    output_b <= temp(63 downto 32);
                
                when OP_MULU =>
                    temp := std_logic_vector(unsigned(rs_in) * unsigned(rt_in));
                    output_b <= temp(63 downto 32);
                    output_a <= temp(31 downto 0);
                
                when OP_DIV =>
                    output_a <= std_logic_vector(signed(rs_in) / signed(rt_in));
                    output_b <= std_logic_vector(signed(rs_in) mod signed(rt_in));
                
                when OP_DIVU =>
                    output_a <= std_logic_vector(unsigned(rs_in) / unsigned(rt_in));
                    output_b <= std_logic_vector(unsigned(rs_in) mod unsigned(rt_in));
                
                when OP_LUI =>
                    output_a <= imm_in(15 downto 0) & x"0000";
                
                when OP_AND =>
                    output_a <= rs_in and rt_in;
                
                when OP_ANDI =>
                    output_a <= rs_in and imm_in;
                
                when OP_OR =>
                    output_a <= rs_in or rt_in;
                
                when OP_ORI =>
                    output_a <= rs_in or imm_in;
                    
                when OP_NOR =>
                    output_a <= not(rs_in or rt_in);
                
                when OP_XOR =>
                    output_a <= rs_in xor rt_in;
                
                when OP_SLL => 
                    output_a <= std_logic_vector(unsigned(rs_in) sll to_integer(unsigned(rt_in(4 downto 0))));
                
                when OP_SLLI =>
                    output_a <= std_logic_vector(unsigned(rs_in) sll to_integer(unsigned(imm_in(4 downto 0))));
                
                when OP_SRL =>
                    output_a <= std_logic_vector(unsigned(rs_in) srl to_integer(unsigned(rt_in(4 downto 0))));
                
                when OP_SRLI =>
                    output_a <= std_logic_vector(unsigned(rs_in) srl to_integer(unsigned(imm_in(4 downto 0))));
                    
                when OP_BEQ =>
                    output_a(0) <= bool2sl(rs_in = rd_in);
                
                when OP_BNE =>
                    output_a(0) <= bool2sl(rs_in /= rd_in);
                
                when OP_BGE =>
                    output_a(0) <= bool2sl(signed(rd_in) >= signed(rs_in));
                
                when OP_BGEU =>
                    output_a(0) <= bool2sl(unsigned(rd_in) >= unsigned(rs_in));
        
                when OP_BGT =>
                    output_a(0) <= bool2sl(signed(rd_in) > signed(rs_in));
                
                when OP_BGTU =>
                    output_a(0) <= bool2sl(unsigned(rd_in) > unsigned(rs_in));
                
                when OP_BLE =>
                    output_a(0) <= bool2sl(signed(rd_in) <= signed(rs_in));
                
                when OP_BLEU =>
                    output_a(0) <= bool2sl(unsigned(rd_in) <= unsigned(rs_in));

                when OP_BLT =>
                    output_a(0) <= bool2sl(signed(rd_in) < signed(rs_in));
                
                when OP_BLTU =>
                    output_a(0) <= bool2sl(unsigned(rd_in) < unsigned(rs_in));

                when others => 
                    null;                    
            end case;
        end if;
    end process;    
end;

