# Portability code for working with different versions of Python
#
# Luz micro-controller assembler
# Eli Bendersky (C) 2010
#
import sys


def printme(s):
    # This function exists because I was initially developing Luz on Python 2.5
    sys.stdout.write(str(s))


def get_input(prompt):
    if sys.hexversion > 0x03000000:
        return input(prompt)
    else:
        return raw_input(prompt)


def is_int_type(obj):
    if sys.hexversion > 0x03000000:
        return isinstance(obj, int)
    else:
        return isinstance(obj, int) or isinstance(obj, long)

# Borrowed from Ned Batchelder
if sys.hexversion > 0x03000000:
    def exec_function(source, filename, global_map):
        """A wrapper around exec()."""
        exec(compile(source, filename, "exec"), global_map)
else:
    # OK, this is pretty gross.  In Py2, exec was a statement, but that will
    # be a syntax error if we try to put it in a Py3 file, even if it isn't
    # executed.  So hide it inside an evaluated string literal instead.
    eval(compile("""\
def exec_function(source, filename, global_map):
    exec compile(source, filename, "exec") in global_map
""",
    "<exec_function>", "exec"))
