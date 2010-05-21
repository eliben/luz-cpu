-- user_memory module for simulation
--
-- Luz micro-controller implementation
-- Eli Bendersky (C) 2008
--
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library work;
use work.cpu_defs.all;


entity user_memory is 
port
(
    clk:        in  std_logic;
    reset_n:    in  std_logic;

    cyc_i:      in  std_logic;
    stb_i:      in  std_logic;
    we_i:       in  std_logic;
    sel_i:      in  std_logic_vector(3 downto 0);
    adr_i:      in  std_logic_vector(MEM_ADDR_SIZE - 1 downto 0);
    data_i:     in  word;
    data_o:     out word;
    ack_o:      out std_logic;
    err_o:      out std_logic
);
end user_memory;


architecture user_memory_arc of user_memory is    
begin
    memory: entity work.sim_memory_onchip_wb(sim_memory_onchip_wb_arc)
    generic map
    (
        ADDR_WIDTH              => MEM_ADDR_SIZE,
        MEMORY_IMAGE_FILE       => "program.hex",
        PRINT_INITIALIZATION    => false
    )
    port map
    (
        clk             => clk,
        reset_n         => reset_n,
        ack_o           => ack_o,
        err_o           => err_o,
        cyc_i           => cyc_i,
        stb_i           => stb_i,
        we_i            => we_i,
        sel_i           => sel_i,
        adr_i           => adr_i,
        data_i          => data_i,
        data_o          => data_o
    );    
end;


