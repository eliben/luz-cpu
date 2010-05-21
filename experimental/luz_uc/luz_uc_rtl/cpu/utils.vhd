-- Package of utility functions and constants
--
-- Luz micro-controller implementation
-- Eli Bendersky (C) 2008-2010
--
library ieee;
use ieee.std_logic_1164.all;

library work;

package utils_pak is 

    -- Convert a boolean to std_logic
    --
    function bool2sl(b: boolean) return std_logic;    

end utils_pak;

package body utils_pak is

    function bool2sl(b: boolean) return std_logic is
    begin
        if (b) then
            return '1';
        else
            return '0';
        end if;
    end function bool2sl;

end utils_pak;

