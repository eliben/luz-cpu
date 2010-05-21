library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;


entity memory_onchip_wb_tb is 
end;

architecture memory_onchip_wb_tb_arc of memory_onchip_wb_tb is
    constant ADDR_WIDTH:    natural := 8;

    signal clk:             std_logic := '0';
    signal reset_n:         std_logic;
    signal ack_o:           std_logic;
    signal cyc_i:           std_logic;
    signal stb_i:           std_logic;
    signal we_i:            std_logic;
    signal sel_i:           std_logic_vector(3 downto 0);
    signal adr_i:           std_logic_vector(ADDR_WIDTH - 1 downto 0);
    signal data_i:          std_logic_vector(31 downto 0);
    signal data_o:          std_logic_vector(31 downto 0);
    signal access_error:    std_logic;
    
    constant WR: std_logic := '1';
    constant RD: std_logic := '0';

begin
    clk <= not clk after 10 ns;
    reset_n <= '0', '1' after 105 ns;

    process
        procedure mem_access(   adr: std_logic_vector(ADDR_WIDTH - 1 downto 0);
                                sel: std_logic_vector(3 downto 0);
                                we: std_logic;
                                data: std_logic_vector(31 downto 0) := x"00000000") is
        begin
            stb_i <= '1';
            cyc_i <= '1';
            we_i <= we;
            sel_i <= sel;
            adr_i <= adr;
            data_i <= data;
            wait until rising_edge(clk);
            wait for 1 ns;
            stb_i <= '0';
            cyc_i <= '0';
            wait for 1 ns;
        end procedure mem_access;
    begin
        cyc_i <= '0';
        stb_i <= '0';
        we_i <= '0';
        sel_i <= (others => '0');
        adr_i <= (others => '0');
        data_i <= (others => '0');
        
        wait for 203 ns;
        
        mem_access(x"03", x"F", RD, x"ABCDFAEC");
        --~ mem_access(x"04", x"8", WR, x"12345678");
        --~ mem_access(x"03", x"3", RD);
        mem_access(x"04", x"f", RD);
        --~ mem_access(x"03", x"6", RD);
        --~ mem_access(x"03", x"8", RD);
        
        wait;
    end process;

    uut: entity work.sim_memory_onchip_wb(sim_memory_onchip_wb_arc)
    generic map
    (
        ADDR_WIDTH              => ADDR_WIDTH,
        MEMORY_IMAGE_FILE       => "bin2hex.hex",
        PRINT_INITIALIZATION    => false
    )
    port map
    (
        clk             => clk,
        reset_n         => reset_n,
        ack_o           => ack_o,
        cyc_i           => cyc_i,
        stb_i           => stb_i,
        we_i            => we_i,
        sel_i           => sel_i,
        adr_i           => adr_i,
        data_i          => data_i,
        data_o          => data_o,
        access_error    => access_error
    );
end;

