# Interactive command-line simulation functions
#
# Luz micro-controller simulator
# Eli Bendersky (C) 2008-2010
import readline
import sys
from .luzsim import LuzSim
from ..asmlib.disassembler import disassemble
from ..asmlib.asm_instructions import register_alias_of
from ..commonlib.utils import word2bytes
from ..commonlib.portability import printme, get_input


def print_regs(sim, replace_alias=True):
    for i in range(32):
        if replace_alias:
            regname = register_alias_of[i]
        else:
            regname = "$r%s" % i
        printme('%-5s = 0x%08X' % (regname, sim.reg_value(i)))
        if i % 4 == 3:
            printme('\n')
        else:
            printme('   ')
    printme('\n')


def do_step(sim):
    instr_word = sim.memory.read_instruction(sim.pc)
    sim.step()


def show_memory(sim, addr):
    for linenum in range(4):
        printme("0x%08X:   " % (addr + linenum * 16,))
        for wordnum in range(4):
            waddr = addr + linenum * 16 + wordnum * 4
            memword = sim.memory.read_mem(waddr, width=4)
            bytes = word2bytes(memword)

            for b in bytes:
                printme("%02X" % b)
            printme('   ')
        printme('\n')


COMMANDS = ('s', 'r', 'sr', 'm', 'rst', 'help', 'q', 'set')

help_message = r'''
Supported commands:

    s [nsteps]      Single step. If 'nsteps' is specified, then 'nsteps'
                    steps are done.

    r               Print the contents of all registers

    sr              Single step and print the contents of all registers

    m <addr>        Show memory contents at <addr>

    rst             Restart the simulator

    ? or help       Print this help message

    q               Quit the simulator

    set <param> <value>
                    Set parameter value (see next section)

Parameters:

    alias           1 to show alias names of registers, 0 to show plain
                    register names.
'''


def print_help():
    printme(help_message + '\n')


def get_matches_for_completion(text, candidates):
    """Create matches for readline completion for text.

    candidates is a sequence of candidates to match. The returned list ends with
    a None.
    """
    return [w + ' ' for w in candidates if w.startswith(text)] + [None]


def make_command_completer(params):
    def command_completer(text, state):
        linebuf = readline.get_line_buffer()
        parts = linebuf.split()

        if len(parts) >= 1 and linebuf.endswith(' '):
            # If we're past the first part and there is whitespace at the end of
            # the buffer, it means we're already completing the next part.
            parts.append('')

        if len(parts) <= 1:
            # Completing command.
            matches = get_matches_for_completion(text, COMMANDS)
            return matches[state]
        elif len(parts) == 2:
            command = parts[0]
            if command == 'set':
                matches = get_matches_for_completion(text, params)
                return matches[state]
        return None

    return command_completer


def interactive_cli_sim(img):
    """ An interactive command-line simulation.

        img: Executable image
    """
    sim = LuzSim(img)
    printme('\nLUZ simulator started at 0x%08X\n\n'  % sim.pc)

    params = {
        'alias':        True,
    }

    readline.parse_and_bind('tab: complete')
    readline.set_completer(make_command_completer(params))

    while True:
        try:
            # show the current instruction
            instr_disasm = disassemble(
                                word=sim.memory.read_instruction(sim.pc),
                                replace_alias=params['alias'])

            # get a command from the user
            line = get_input('[0x%08X] [%s] >> ' % (sim.pc, instr_disasm)).strip()

            # skip empty lines
            if not line.strip():
                continue

            cmd, args = parse_cmd(line)

            if cmd == 's':
                if len(args) >= 1:
                    nsteps = int(args[0])
                else:
                    nsteps = 1

                for i in range(nsteps):
                    do_step(sim)
            elif cmd == 'q':
                return
            elif cmd == 'rst':
                sim.restart()
                printme('Restarted\n')
            elif cmd == 'r':
                print_regs(sim, replace_alias=params['alias'])
            elif cmd == 'sr':
                do_step(sim)
                print_regs(sim, replace_alias=params['alias'])
            elif cmd == 'm':
                if len(args) != 1:
                    printme("Error: expected memory address\n")
                    continue
                addr = args[0]
                show_memory(sim, int(addr, 0))
            elif cmd == 'set':
                if len(args) != 2:
                    printme("Error: invalid command\n")
                    continue
                param, value = args[0], args[1]
                if param in params:
                    params[param] = int(value, 0)
                else:
                    printme("Error: no such parameter '%s'\n" % param)
            elif cmd == '?' or cmd == 'help':
                print_help()
            else:
                printme('Unknown command. To get some help, type ? or help\n')
        except (EOFError, KeyboardInterrupt):
            printme("\nExiting...\n")
            break
        except Exception:
            e = sys.exc_info()[1]
            printme('\n!!ERROR!!: %s %s\n' % (type(e), str(e)))


def parse_cmd(line):
    """ Parses a command
    """
    tokens = [t.strip() for t in line.split()]
    return tokens[0], tokens[1:]
