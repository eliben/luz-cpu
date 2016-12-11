import unittest

import test_common
import test_lexer
import test_parser
import test_assembler
import test_disassembler
import test_linker
import test_asm_instructions
import test_luzsim


if __name__ == '__main__':
    suite = unittest.TestSuite()
    loader = unittest.defaultTestLoader

    suite.addTests([
        loader.loadTestsFromModule(test_lexer),
        loader.loadTestsFromModule(test_common),
        loader.loadTestsFromModule(test_parser),
        loader.loadTestsFromModule(test_asm_instructions),
        loader.loadTestsFromModule(test_assembler),
        loader.loadTestsFromModule(test_disassembler),
        loader.loadTestsFromModule(test_linker),
        loader.loadTestsFromModule(test_luzsim),
    ])

    unittest.TextTestRunner().run(suite)
