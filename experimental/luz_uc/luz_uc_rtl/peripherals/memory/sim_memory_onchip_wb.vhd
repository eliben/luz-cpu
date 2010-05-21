-- >> Simulation model <<
-- On-chip memory with Wishbone interface.
--
-- 32-bit wide data port. Accesses are allowed only to bytes, 
-- half-words (at half-word boundaries) and full words.
-- Word-addressing is used (address 3 is bytes 12-15, etc.)
--
-- Initializes itself from a .hex file.
--
-- Luz micro-controller implementation
-- Eli Bendersky (C) 2008
--
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library std;
use std.textio.all;

library work;
use work.io_utils.all;
use work.txt_util.all;


entity sim_memory_onchip_wb is
generic
(
    -- Address width: controls the memory size, which is
    -- 2 ^ width bytes
    --
    ADDR_WIDTH:             natural;
    
    -- Name of the memory image file from which the module is 
    -- initialized. 
    -- Must be a file in Intel HEX format
    --
    MEMORY_IMAGE_FILE:      string;
    
    -- Enable diagnostic print-outs while initializing from the
    -- memory image file.
    --
    PRINT_INITIALIZATION:   boolean := false      
);
port
(
    clk:            in  std_logic;
    
    -- Asynchronous, zero-active reset
    --
    reset_n:        in  std_logic;
    
    -- Standard Wishbone signals
    --
    cyc_i:          in  std_logic;
    stb_i:          in  std_logic;
    we_i:           in  std_logic;
    sel_i:          in  std_logic_vector(3 downto 0);
    adr_i:          in  std_logic_vector(ADDR_WIDTH - 1 downto 0);
    data_i:         in  std_logic_vector(31 downto 0);
    data_o:         out std_logic_vector(31 downto 0);
    ack_o:          out std_logic;
    err_o:          out std_logic
);
end sim_memory_onchip_wb;


architecture sim_memory_onchip_wb_arc of sim_memory_onchip_wb is

    subtype memory_word     is std_logic_vector(31 downto 0);
    subtype memory_size     is natural range 0 to 2**ADDR_WIDTH - 1;
    type    memory_area     is array(memory_size) of memory_word;
    
    signal mem: memory_area;
    
    signal strobe:           std_logic;
    
    -- "Mixes" the 'a' and 'b' words using 'sel_a'. 
    -- Bytes corresponding to bits turned on in sel_a are 
    -- taken from a, and the rest from b.
    --
    function mix_with_sel(  a:      std_logic_vector(31 downto 0);
                            b:      std_logic_vector(31 downto 0);
                            sel_a:  std_logic_vector(3 downto 0)) 
                        return std_logic_vector is
        
        variable val:   std_logic_vector(31 downto 0);
    begin
        if (sel_a = "1111") then
            val := a;
        elsif (sel_a = "0011") then
            val := b(31 downto 16) & a(15 downto 0);
        elsif (sel_a = "1100") then
            val := a(31 downto 16) & b(15 downto 0);
        elsif (sel_a = "0001") then
            val := b(31 downto 8) & a(7 downto 0);
        elsif (sel_a = "0010") then
            val := b(31 downto 16) & a(15 downto 8) & b(7 downto 0);
        elsif (sel_a = "0100") then
            val := b(31 downto 24) & a(23 downto 16) & b(15 downto 0);
        elsif (sel_a = "1000") then
            val := a(31 downto 24) & b(23 downto 0);
        else
            val := (others => '0');
        end if;    
        
        return val;
    end function mix_with_sel;
    
    constant BAD_VALUE: integer := -999;
    
    -- Convert a character representing a hexadecimal digit to a
    -- value from 0 to 15.
    -- If the character is not a valid hexadecimal digit,
    -- returns BAD_VALUE.
    --
    function hex_digit_value(c: character) return integer is
    begin
        if (c >= '0') and (c <= '9') then
            return (character'pos(c) - character'pos('0'));
        elsif (c >= 'a') and (c <= 'f') then
            return (character'pos(c) - character'pos('a') + 10);
        elsif (c >= 'A') and (c <= 'F') then
            return (character'pos(c) - character'pos('A') + 10);
        else
            return BAD_VALUE;
        end if;
    end;
    
    -- Reads two characters from the line. These characters
    -- represent a byte encoded in two hexadecimal digits. 
    -- Returns the integer value of the byte.
    --
    -- For example, if the line contains 'a51028472', 
    -- returns 165, because 'a5' is hex for 165. The line
    -- is advanced by 2 characters.
    --
    -- If the line is too short, or the characters are not valid
    -- hexadecimal digits (for example 'z3'), returns BAD_VALUE.
    --
    procedure read_hex_byte(ln: inout line; val: out integer) is
        variable c_high, c_low: character;
        variable i_high, i_low: integer;
        variable read_ok:       boolean;
    begin
        val := BAD_VALUE;
    
        if (ln'length >= 2) then
            read(ln, c_high, read_ok);
            if not read_ok then return; end if;
            read(ln, c_low, read_ok);
            if not read_ok then return; end if;
            
            i_high := hex_digit_value(c_high);
            i_low := hex_digit_value(c_low);
            
            if (i_high = BAD_VALUE or i_low = BAD_VALUE) then
                return;
            end if;
            
            val := i_high * 16 + i_low;
        end if;
        
        return;
    end;
    
    -- Reads a memory image file in Intel-hex format.
    -- Supports the following record types:
    --  00 - Data record
    --  01 - End of file record
    --  04 - Extended linear address record
    --
    function read_memory_hex_image(filename: string) return memory_area is
        file image_file:            text open read_mode is filename;
        variable mem_image:         memory_area;
        variable ln:                line;
        variable c:                 character;
        variable read_ok:           boolean;
        variable line_count:        natural := 0;
        
        variable    rec_len,
                    rec_offset_low,
                    rec_offset_high,
                    rec_offset,
                    rec_checksum,
                    rec_data_byte,
                    rec_type:       integer;
        
        variable base_address:      integer := 0;
        variable target_address:    integer;
        variable running_checksum:  integer;
        
        variable tmp_word:          memory_word;
        variable word_address:      integer;
        variable n_byte_in_word:    integer;

    begin
        while (not endfile(image_file)) loop
            line_count := line_count + 1;
            
            -- Read a line from the file and skip empty lines
            --
            readline(image_file, ln);
            next when (ln'length < 1);
            
            -- Each record begins with a colon ':'
            --
            read(ln, c, read_ok);
            assert read_ok report "Expected data at line #" & str(line_count);
            assert c = ':' report "Expected ':' at line #" & str(line_count);
            
            read_hex_byte(ln, rec_len);
            assert rec_len /= BAD_VALUE report "Expected record length after ':' at line #" & str(line_count);
            
            read_hex_byte(ln, rec_offset_high);
            read_hex_byte(ln, rec_offset_low);
            
            assert  rec_offset_high /= BAD_VALUE and
                    rec_offset_low /= BAD_VALUE
                report "Expected record offset at line #" & str(line_count);

            rec_offset := rec_offset_high * 256 + rec_offset_low;
            
            read_hex_byte(ln, rec_type);
            assert rec_type /= BAD_VALUE report "Expected record type at line #" & str(line_count);

            running_checksum := (rec_len + rec_offset_high + rec_offset_low + rec_type) mod 256;

            case (rec_type) is
                -- For data record, insert each data byte into
                -- base_address + rec_offset of the memory array.
                --
                when 0 =>
                    assert (base_address + rec_offset + rec_len <= (2 ** ADDR_WIDTH) * 4) 
                        report "Record beyond memory capacity: " & 
                                str(base_address + rec_offset + rec_len) &
                                " > " & str(2 ** ADDR_WIDTH * 4);

                    for i in 0 to rec_len - 1 loop
                        read_hex_byte(ln, rec_data_byte);
                        assert rec_data_byte /= BAD_VALUE 
                            report "Expected " & str(rec_len) & 
                                    " valid data bytes at line#" &
                                    str(line_count);

                        running_checksum := (running_checksum + rec_data_byte) mod 256;
                        
                        -- The memory image array is 32-bit wide.
                        -- But we're reading bytes from the file
                        -- one at a time. Therefore, we must 
                        -- compute where to insert the current byte.
                        --
                        target_address := base_address + rec_offset + i;
                        n_byte_in_word := target_address mod 4;
                        word_address := target_address / 4;
                        tmp_word := mem_image(word_address);
                        
                        tmp_word((n_byte_in_word * 8) + 7 downto n_byte_in_word * 8) := std_logic_vector(to_unsigned(rec_data_byte, 8));
                        mem_image(word_address) := tmp_word;
                        
                        if (PRINT_INITIALIZATION) then
                            print("Inserted value " & 
                                    str(rec_data_byte) &
                                    " at word " & str(word_address) &
                                    ", byte #" & str(n_byte_in_word));
                        end if;
                    end loop;
                    
                    read_hex_byte(ln, rec_checksum);
                    running_checksum := (running_checksum + rec_checksum) mod 256;
                    
                    assert running_checksum = 0
                        report "Checksum error. Expected 0, got 0x" &
                                hstr(std_logic_vector(to_unsigned(running_checksum, 8))) &
                                " at line #" & str(line_count);
                                
                
                -- End of file record
                --
                when 1 =>
                    read_hex_byte(ln, rec_checksum);
                    assert rec_checksum = 255 
                        report "Checksum error. Expected 0xFF, got 0x" & 
                                hstr(std_logic_vector(to_unsigned(rec_checksum, 8))) & 
                                " at line #" & str(line_count);
                
                    if (PRINT_INITIALIZATION) then
                        print("End of file record at line #" & str(line_count));
                    end if;
                    
                    return mem_image;
                
                -- For extended linear address records, set
                -- the base address.
                --                
                when 4 =>
                    read_hex_byte(ln, rec_data_byte);
                    assert rec_data_byte /= BAD_VALUE report "Bad data byte at line #" & str(line_count);
                    base_address := rec_data_byte * 65536;
                    running_checksum := (running_checksum + rec_data_byte) mod 256;
                    
                    read_hex_byte(ln, rec_data_byte);
                    assert rec_data_byte /= BAD_VALUE report "Bad data byte at line #" & str(line_count);
                    base_address := base_address + rec_data_byte;
                    running_checksum := (running_checksum + rec_data_byte) mod 256;
                    
                    read_hex_byte(ln, rec_checksum);
                    running_checksum := (running_checksum + rec_checksum) mod 256;
                    
                    assert running_checksum = 0
                        report "Checksum error. Expected 0, got 0x" &
                                hstr(std_logic_vector(to_unsigned(running_checksum, 8))) &
                                " at line #" & str(line_count);
                
                when others =>
                    assert false report "Unsupported record type " & str(rec_type) & " at line #" & str(line_count);
            end case;

            --~ print ( "Line# " & str(line_count) &
                    --~ " -- Len: " & str(rec_len) & 
                    --~ ", Offset: " & str(rec_offset) &
                    --~ ", Type: " & str(rec_type));

        end loop;
    
        return mem_image;
    end function read_memory_hex_image;
    
begin

    strobe <= stb_i and cyc_i;
    
    err_o <= '1' when   strobe = '1' and 
                        sel_i /= "1111" and
                        sel_i /= "0011" and
                        sel_i /= "1100" and
                        sel_i /= "0001" and
                        sel_i /= "0010" and
                        sel_i /= "0100" and
                        sel_i /= "1000" 
                        else '0';

    mem_read_proc: process(clk)
        variable tmp: std_logic_vector(31 downto 0);
    begin
        if (rising_edge(clk)) then
            if (strobe = '1' and we_i = '0') then
                data_o <= mix_with_sel(mem(to_integer(unsigned(adr_i))), x"00000000", sel_i);
            end if;
        end if;
    end process;

    mem_write_proc: process
        variable tmp: std_logic_vector(31 downto 0);
    begin
        -- initialize memory at startup
        mem <= read_memory_hex_image(MEMORY_IMAGE_FILE);

        -- now ready to write data
        loop
            wait until rising_edge(clk);
            if (strobe = '1' and we_i = '1') then
                mem(to_integer(unsigned(adr_i))) <= mix_with_sel(data_i, mem(to_integer(unsigned(adr_i))), sel_i);
            end if;
        end loop;
        
        wait;
    end process;

    -- This is a single-cycle synchronous memory, so 
    -- ack_o is always "ready" during an access. 
    --
    ack_o <= strobe;
    
end sim_memory_onchip_wb_arc;
