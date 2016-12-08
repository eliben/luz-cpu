*************************
 Instruction set summary
*************************

Some registers have special roles in this instruction set:

R0          - Always 0. Writes to R0 are ignored.
R31         - Used to store the return address of CALL

Nomenclature:

<n>         - a number
Rd          - Destination register
Rs, Rt      - Source operand registers
PC          - Program counter
R<n>        - General Purpose Register number <n>
const<n>    - a constant (immediate) <n> bits long
off<n>      - an offset <n> bits long. always signed.
+-          - the operation is signed
HI, LO      - high and low words of a 64-bit result
quot, rem   - quotient and remainder of division
Rn[n:m]     - bits [n:m] of register Rn
mem<n>      - n-bit access to memory

All the instructions are encoded in a single 32-bit word. The opcode always takes 6 bits, 31:26.


|---------------------------|-------------------------------|
| ADD   Rd, Rs, Rt          | Rd = Rs + Rt                  |
|---------------------------|-------------------------------|

Add register.

Addition is unsigned, without overflow detection. Signed numbers can be added with the same instruction, but the programmer is responsible for taking care of their ranges and possible overflows.

Encoding:
31:26   Opcode = 000000
25:21   Rd
20:16   Rs
15:11   Rt
10:0    reserved


|---------------------------|-------------------------------|
| ADDI  Rd, Rs, const16     | Rd = Rs + const16             |
|---------------------------|-------------------------------|

Add immediate.

Addition is unsigned, without overflow detection. Signed numbers can be added with the same instruction, but the programmer is responsible for taking care of their ranges and possible overflows.

The immediate is assumed to be unsigned. If you want to add a negative immediate, subtract its absolute value instead.

Encoding:
31:26   Opcode = 100000
25:21   Rd
20:16   Rs
15:0    const16


|---------------------------|-------------------------------|
| SUB   Rd, Rs, Rt          | Rd = Rs - Rt                  |
|---------------------------|-------------------------------|

Subtract register.

Subtraction is unsigned, without overflow detection. Signed numbers can be subtracted with the same instruction, but the programmer is responsible for taking care of their ranges and possible overflows.

Encoding:
31:26   Opcode = 000001
25:21   Rd
20:16   Rs
15:11   Rt
10:0    reserved


|---------------------------|-------------------------------|
| SUBI  Rd, Rs, const16     | Rd = Rs - const16             |
|---------------------------|-------------------------------|

Subtract immediate.

Subtraction is unsigned, without overflow detection. Signed numbers can be subtracted with the same instruction, but the programmer is responsible for taking care of their ranges and possible overflows.

The immediate is assumed to be unsigned.

Encoding:
31:26   Opcode = 100001
25:21   Rd
20:16   Rs
15:0    const16


|---------------------------|-------------------------------|
| MULU  Rd, Rs, Rt          | Rd+1 = HI, Rd = LO            |
|---------------------------|-------------------------------|

Unsigned multiplication - treats operands as unsigned.

In 32-bit multiplication the result is 64-bit long. The lower bits of the result are placed in Rd, and the higher bits in Rd+1.

For example, if Rd is R24, then R24 <- LO, R25 <- HI.
If Rd is R31, the higher bits are lost. 

Encoding:
31:26   Opcode = 000010
25:21   Rd
20:16   Rs
15:11   Rt
10:0    reserved


|---------------------------|-------------------------------|
| MUL   Rd, Rs, Rt          | Rd+1 = HI, Rd = LO (+-)       |
|---------------------------|-------------------------------|

Signed multiplication - treads operands as signed.

In 32-bit multiplication the result is 64-bit long. Result assignment is similar to MULU.

Encoding:
31:26   Opcode = 000011
25:21   Rd
20:16   Rs
15:11   Rt
10:0    reserved


|---------------------------|-------------------------------|
| DIVU  Rd, Rs, Rt          | Rd+1 = rem, Rd = quot         |
|---------------------------|-------------------------------|

Unsigned division.
The quotient is placed in Rd and the remainder in Rd+1.

For example, if Rd is R24, then R24 <- quot, R25 <- rem.
If Rd is R31, then reminder is lost.

Encoding:
31:26   Opcode = 000100
25:21   Rd
20:16   Rs
15:11   Rt
10:0    reserved


|---------------------------|-------------------------------|
| DIV   Rd, Rs, Rt          | Rd+1 = rem, Rd = quot (+-)    |
|---------------------------|-------------------------------|

Signed division.
Result assignment is similar to DIVU.

Encoding:
31:26   Opcode = 000101
25:21   Rd
20:16   Rs
15:11   Rt
10:0    reserved


|---------------------------|-------------------------------|
| LUI   Rd, const16         | Rd = const16 << 16            |
|---------------------------|-------------------------------|

Load upper immediate.
Loads the immediate into the upper half-word of the target register. The lower half-word is set to 0.

Encoding:
31:26   Opcode = 000110
25:21   Rd
20:16   reserved
15:0    const16


|---------------------------|-------------------------------|
| SLL   Rd, Rs, Rt          | Rd = Rs << Rt[4:0]            |
|---------------------------|-------------------------------|

Shift left logical. 
0 is shifted into the lower bits. Only the lower 5 bits of Rt take part in the computation (maximal shift amount is 31).

Encoding:
31:26   Opcode = 000111
25:21   Rd
20:16   Rs
15:11   Rt
10:0    reserved


|---------------------------|-------------------------------|
| SLLI   Rd, Rs, const16    | Rd = Rs << const16[4:0]       |
|---------------------------|-------------------------------|

Shift left logical by immediate.
Similar to SLL. Only the low 5 bits of const16 are used for the shift distance.

Encoding:
31:26   Opcode = 101011
25:21   Rd
20:16   Rs
15:0    const16


|---------------------------|-------------------------------|
| SRL   Rd, Rs, Rt          | Rd = Rs >> Rt[4:0]            |
|---------------------------|-------------------------------|

Shift right logical. 
0 is shifted into the upper bits. Only the lower 5 bits of Rt take part in the computation (maximal shift amount is 31).

Encoding:
31:26   Opcode = 001000
25:21   Rd
20:16   Rs
15:11   Rt
10:0    reserved


|---------------------------|-------------------------------|
| SRLI   Rd, Rs, const16    | Rd = Rs >> const16[4:0]       |
|---------------------------|-------------------------------|

Shift right logical by immediate.
Similar to SRL. Only the low 5 bits of const16 are used for the shift distance.

Encoding:
31:26   Opcode = 101100
25:21   Rd
20:16   Rs
15:0    const16


|---------------------------|-------------------------------|
| AND   Rd, Rs, Rt          | Rd = Rs & Rt                  |
|---------------------------|-------------------------------|

AND of registers.

Encoding:
31:26   Opcode = 001001
25:21   Rd
20:16   Rs
15:11   Rt
10:0    reserved


|---------------------------|-------------------------------|
| ANDI  Rd, Rs, const16     | Rd = Rs & const16             |
|---------------------------|-------------------------------|

AND with immediate (zero extended).

Encoding:
31:26   Opcode = 101001
25:21   Rd
20:16   Rs
15:0    const16


|---------------------------|-------------------------------|
| OR    Rd, Rs, Rt          | Rd = Rs | Rt                  |
|---------------------------|-------------------------------|

OR of registers.

Encoding:
31:26   Opcode = 001010
25:21   Rd
20:16   Rs
15:11   Rt
10:0    reserved


|---------------------------|-------------------------------|
| ORI   Rd, Rs, const16     | Rd = Rs | const16             |
|---------------------------|-------------------------------|

OR with immediate (zero extended).

Encoding:
31:26   Opcode = 101010
25:21   Rd
20:16   Rs
15:0    const16


|---------------------------|-------------------------------|
| NOR   Rd, Rs, Rt          | Rd = ~(Rs | Rt)               |
|---------------------------|-------------------------------|

NOR of registers.

Encoding:
31:26   Opcode = 001011
25:21   Rd
20:16   Rs
15:11   Rt
10:0    reserved


|---------------------------|-------------------------------|
| XOR   Rd, Rs, Rt          | Rd = Rs XOR Rt                |
|---------------------------|-------------------------------|

XOR of registers.

Encoding:
31:26   Opcode = 001100
25:21   Rd
20:16   Rs
15:11   Rt
10:0    reserved


|---------------------------|-------------------------------|
| LB    Rd, off16(Rs)       | Rd = mem8(Rs + off16)         |
|---------------------------|-------------------------------|

Load byte from memory into the lower byte of Rd. Sign extend into the higher bits. 

Encoding:
31:26   Opcode = 001101
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|-------------------------------|
| LH    Rd, off16(Rs)       | Rd = mem16(Rs + off16)        |
|---------------------------|-------------------------------|

Load half-word from memory into the lower half-word of Rd. Sign extend into the higher bits.

Encoding:
31:26   Opcode = 001110
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|-------------------------------|
| LW    Rd, off16(Rs)       | Rd = mem32(Rs + off16)        |
|---------------------------|-------------------------------|

Load word from memory into Rd.

Encoding:
31:26   Opcode = 001111
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|-------------------------------|
| LBU   Rd, off16(Rs)       | Rd = mem8(Rs + off16)         |
|---------------------------|-------------------------------|

Load byte from memory into the lower byte of Rd. Zero extend into the higher bits.

Encoding:
31:26   Opcode = 010000
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|-------------------------------|
| LHU   Rd, off16(Rs)       | Rd = mem16(Rs + off16)        |
|---------------------------|-------------------------------|

Load half-word from memory into the lower half-word of Rd. Zero extend into the higher bits.

Encoding:
31:26   Opcode = 010001
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|-------------------------------|
| SB    Rs, off16(Rd)       | mem8(Rd + off16) = Rs[7:0]    |
|---------------------------|-------------------------------|

Store the lower byte of Rs into memory.

Encoding:
31:26   Opcode = 010010
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|-------------------------------|
| SH    Rs, off16(Rd)       | mem16(Rd + off16) = Rs[15:0]  |
|---------------------------|-------------------------------|

Store the lower half-word of Rs into memory.

Encoding:
31:26   Opcode = 010011
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|-------------------------------|
| SW    Rs, off16(Rd)       | mem32(Rd + off16) = Rs        |
|---------------------------|-------------------------------|

Store Rs into memory.

Encoding:
31:26   Opcode = 010100
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|-------------------------------|
| JR    Rd                  | PC = Rd                       |
|---------------------------|-------------------------------|

Jump the the address stored in Rd.

Encoding:
31:26   Opcode = 010110
25:21   Rd
20:0    reserved


|---------------------------|-------------------------------|
| CALL    const26           | R31 = PC + 4                  |
|                           | PC = const26 * 4              |
|---------------------------|-------------------------------|

Procedure call. Save the address of the next instruction in R31 and jump (unconditionally) to the address const26 * 4 (instructions are aligned on word boundaries).

Encoding: 
31:26   Opcode = 011101
25:0    off26


|---------------------------|-------------------------------|
| B     off26               | PC += off26 * 4 (+-)          |
|---------------------------|-------------------------------|

Branch unconditionally, relative to PC.
Offset is off26 * 4, because instructions are aligned on word boundaries.

Encoding:
31:26   Opcode = 010101
25:0    off26


|---------------------------|-------------------------------|
| BEQ   Rd, Rs, off16       | IF Rd = Rs, PC += off16 * 4   |
|---------------------------|-------------------------------|

Branch on equal.
Offset is off16 * 4, because instructions are aligned on word boundaries.

Encoding:
31:26   Opcode = 010111
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|-------------------------------|
| BNE   Rd, Rs, off16       | IF Rd != Rs, PC += off16 * 4  |
|---------------------------|-------------------------------|

Branch on not equal.
Offset is off16 * 4, because instructions are aligned on word boundaries.

Encoding:
31:26   Opcode = 011000
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|-----------------------------------|
| BGE   Rd, Rs, off16       | IF Rd >= Rs (+-), PC += off16 * 4 |
|---------------------------|-----------------------------------|

Branch on greater than or equal. Signed.
Offset is off16 * 4, because instructions are aligned on word boundaries.

Encoding:
31:26   Opcode = 011001
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|-------------------------------|
| BGEU   Rd, Rs, off16      | IF Rd >= Rs, PC += off16 * 4  |
|---------------------------|-------------------------------|

Branch on greater than or equal. Unsigned.
Offset is off16 * 4, because instructions are aligned on word boundaries.

Encoding:
31:26   Opcode = 100010
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|----------------------------------|
| BGT   Rd, Rs, off16       | IF Rd > Rs (+-), PC += off16 * 4 |
|---------------------------|----------------------------------|

Branch on greater than. Signed.
Offset is off16 * 4, because instructions are aligned on word boundaries.

Encoding:
31:26   Opcode = 011010
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|-------------------------------|
| BGTU  Rd, Rs, off16       | IF Rd > Rs, PC += off16 * 4   |
|---------------------------|-------------------------------|

Branch on greater than. Unsigned.
Offset is off16 * 4, because instructions are aligned on word boundaries.

Encoding:
31:26   Opcode = 100011
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|-----------------------------------|
| BLE   Rd, Rs, off16       | IF Rd <= Rs (+-), PC += off16 * 4 |
|---------------------------|-----------------------------------|

Branch on less than or equal. Signed.
Offset is off16 * 4, because instructions are aligned on word boundaries.

Encoding:
31:26   Opcode = 011011
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|-------------------------------|
| BLEU  Rd, Rs, off16       | IF Rd <= Rs, PC += off16 * 4  |
|---------------------------|-------------------------------|

Branch on less than or equal. Unsigned.
Offset is off16 * 4, because instructions are aligned on word boundaries.

Encoding:
31:26   Opcode = 100100
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|----------------------------------|
| BLT   Rd, Rs, off16       | IF Rd < Rs (+-), PC += off16 * 4 |
|---------------------------|----------------------------------|

Branch on less than. Signed.
Offset is off16 * 4, because instructions are aligned on word boundaries.

Encoding:
31:26   Opcode = 011100
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|----------------------------------|
| BLTU  Rd, Rs, off16       | IF Rd < Rs     , PC += off16 * 4 |
|---------------------------|----------------------------------|

Branch on less than. Unsigned.
Offset is off16 * 4, because instructions are aligned on word boundaries.

Encoding:
31:26   Opcode = 100101
25:21   Rd
20:16   Rs
15:0    off16


|---------------------------|-------------------------------|
| ERET                      | Return from exception handler |
|---------------------------|-------------------------------|

Returns from an exception handler. The PC is set to the address from which the CPU will resume execution (this address is saved internally by the CPU when an exception occurs).

Encoding:
31:26   Opcode = 111110
25:0    Reserved

|---------------------------|-------------------------------|
| HALT                      | Halts CPU                     |
|---------------------------|-------------------------------|

Halts the CPU. A hardware 'halt' line is raised.

Encoding:
31:26   Opcode = 111111
25:0    reserved


********************************
 Additional pseudo-instructions
********************************

The following instructions are not really implemented in the CPU. Rather, these are pseudo-instructions, made for the convenience of the programmer and translated by the assembler into real instructions. So they have no encoding and no opcode.

|---------------------------|-------------------------------|
| NOT   Rd, Rs              | Rd = ~Rs                      |
|---------------------------|-------------------------------|

Translated to:
    NOR Rd, Rs, Rs


|---------------------------|-------------------------------|
| NOP                       | No op.                        |
|---------------------------|-------------------------------|

Translated to:
    ADD R0, R0, R0


|---------------------------|-------------------------------|
| MOVE  Rd, Rs              | Rd = Rs                       |
|---------------------------|-------------------------------|

Translated to:
    ADD Rd, Rs, R0


|---------------------------|-------------------------------|
| NEG  Rd, Rs               | Rd = -Rs                      |
|---------------------------|-------------------------------|

Translated to:
    SUB Rd, R0, Rs


|---------------------------|-------------------------------|
| BEQZ  Rd, off16           | IF Rd = 0, PC += off16 * 4    |
|---------------------------|-------------------------------|

Translated to:
    BEQ Rd, R0, off16


|---------------------------|-------------------------------|
| BNEZ  Rd, off16           | IF Rd != 0, PC += off16 * 4   |
|---------------------------|-------------------------------|

Translated to:
    BNE Rd, R0, off16


|---------------------------|-------------------------------|
| LLI   Rd, const16         | Rd[15:0] = const16            |
|---------------------------|-------------------------------|

Load lower immediate. 
Translated to:
    ORI Rd, R0, const16


|---------------------------|-------------------------------|
| LI    Rd, const32         | Rd = const32                  |
|---------------------------|-------------------------------|

Load 32-bit immediate.
Translated to:
    LUI Rd, const32[31:16]
    ORI Rd, Rd, const32[15:0]


|---------------------------|-------------------------------|
| RET                       |                               |
|---------------------------|-------------------------------|

Returns to the address stored in R31 (returning from subroutine calls).
Translated to:
    JR R31



**********************
 Assembler directives 
**********************

|-----------------------------|
| .segment label              |
|-----------------------------|

Subsequent lines will be assembled into the specified segment. 


|-----------------------------|
| .global label               |
|-----------------------------|

Declare the label to be global (exported). The label must exist in this assembly file.


|-----------------------------|
| .define name, value         |
|-----------------------------|

Name: alphanumeric 
Value: numeric

Defines a mnemonic constant that can be used in immediate values and offsets. Constants have to be defined before use.


|-----------------------------|
| .alloc n                    |
|-----------------------------|

Allocate <n> bytes from here on. <n> must be numeric (not a constant from .define).


|-----------------------------|
| .byte b1, .. ,bN            |
|-----------------------------|

Store the supplied bytes in memory, in successive addresses. Each value must be an unsigned number that fits in a byte.


|-----------------------------|
| .word w1, .. ,wN            |
|-----------------------------|

Store the supplied words in memory, in successive addresses. Each value must be an unsigned number that fits in a 4-byte word.


|-----------------------------|
| .string str                 |
|-----------------------------|

'str' is a string enclosed in double quotes ("). Supports C-like escaping of \t, \n, \\, \". The string will be stored in memory and zero-terminated (i.e. a zero byte will be appended to its end).

