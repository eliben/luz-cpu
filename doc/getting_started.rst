.. contents:: Table of Contents
   :backlinks: none
.. sectnum::


Introduction
************

This document will help you get started using / hacking on Luz. It doesn't explain Luz in any depth - read `the user manual <https://github.com/eliben/luz-cpu/blob/master/doc/luz_user_manual.rst>`_ for that.

What is Luz?
------------

Luz is an open-source CPU suite. The suite includes:

* A fully functional simulator of the Luz 32-bit RISC CPU.
* An assembler and a linker for code written in the Luz assembly (LASM) language.

In the future, Luz will also feature a complete synthesizable VHDL implementation of the CPU. For the time being, a partial implementation is available in the ``experimental`` directory of the Luz source code tree.

License
-------

The code of Luz is in the public domain. For more information, see the COPYING file in the main directory.

What is Luz useful for?
-----------------------

I don't know yet. It's a self-educational project of mine, and I learned a lot by working on it. I suppose that Luz's main value is as an educational tool. Its implementation focuses on simplicity and modularity, and is done in Python, which is a portable and very readable high-level language.

Luz can serve as a sample of implementing a complete assembler, a complete linker, a complete CPU simulator. Other such tools exist, but usually not in the clean and self-contained form offered by Luz. In any case, if you've found Luz iseful, I'd love to receive feedback.

Getting started with Luz
************************

Documentation
-------------

The Luz documentation is collected in the ``doc`` directory.

Dependencies
------------

Luz is implemented in pure Python. To run it, you need to have a couple of things installed:

* Python version 2.7 or 3.2+ 
* The PLY Python library, which you can obtain from its website (google it). Luz works with all recent versions of PLY

Structure of the source tree
----------------------------

* ``doc``: Documentation

* ``experimental``: Experimental code and features (not currently suitable for use)

* ``luz_asm_sim``: The Luz assembler/linker and simulator:

 - ``luz_asm_sim/lib``: The implementation of Luz
 - ``luz_asm_sim/tests_full``: Full tests of Luz that also serve as examples
 - ``luz_asm_sim/tests_unit``: Unit tests for Luz

Running examples
----------------

Luz has a framework of "full tests" in ``luz_asm_lib/tests_full``. Each full test is a directory with one or more ``.lasm`` files that implement a program in Luz assembly language (LASM). The full tests serve two roles:

* As examples of using Luz
* For testing the Luz suite on complete programs

The ``tests_full/README.txt`` explains in more detail how to run the full tests. Here I want to focus on one simple example.

The simple loop example
=======================

Open ``tests_full/loop_simple``. In there you'll find a LASM file named ``loop.asm``. Open it and take a look. This is a program that computes the sum of an array. The array is defined statically in the ``.data`` segment, and the program itself starts with the ``asm_main`` symbol (as all LASM programs should start - see the user's manual for more details). It iterates over the array in a loop and sums it into the ``$r8`` register.

Take a few minutes to study the code: if you've seen any other assembly code before, it should be simple to understand. Consult the user's manual for the meaning of individual instructions. 

Now, to run the example, go back to ``tests_full`` and execute:

::

  python run_test_interactive.py -i loop_simple

You should see something like:

::

  LUZ simulator started at 0x00100000
  
  [0x00100000] [lui $sp, 0x13] >>

This is the *interactive shell* of the Luz simulator that allows you to execute the code step-by step, viewing the contents of registers, and so on. If this sounds like a debugger, you're right - it is. Type ``help`` to see the available commands and what they mean. Note that ``run_test_interactive.py`` can also run the whole test from start to finish, without the interactive prompt. Run it with ``-h`` to see the options.

Execute the following commands:

::

  [0x00100000] [lui $sp, 0x13] >> s 100
  [0x00100038] [halt] >> set alias 0
  [0x00100038] [halt] >> r
  $r0   = 0x00000000     $r1   = 0x00000000     $r2   = 0x00000000     $r3   = 0x00000000
  $r4   = 0x00000000     $r5   = 0x00100050     $r6   = 0x00100050     $r7   = 0x00000000
  $r8   = 0x0000021F     $r9   = 0x0010003C     $r10  = 0x00000000     $r11  = 0x00000000
  $r12  = 0x00000000     $r13  = 0x00000000     $r14  = 0x00000000     $r15  = 0x00000000
  $r16  = 0x00000000     $r17  = 0x00000000     $r18  = 0x00000000     $r19  = 0x00000000
  $r20  = 0x00000000     $r21  = 0x00000000     $r22  = 0x00000000     $r23  = 0x00000000
  $r24  = 0x00000000     $r25  = 0x00000000     $r26  = 0x00000000     $r27  = 0x00000000
  $r28  = 0x00000000     $r29  = 0x0013FFFC     $r30  = 0x00000000     $r31  = 0x0010000C

* The first command asks the simulator to step through 100 instructions
* The second command disables displaying register alias names since the LASM code of ``loop_simple`` doesn't use them (see the user's manual about alias names)
* The third command asks Luz to display the contents of all registers.

As you can see, the simulator is now at a ``halt`` instruction, which means the CPU stopped executing ("halted"). ``$r8`` holds the sum of the array. Now you can enter the ``q`` command to quit the interactive simulator.

The other examples can be run similarly.

What's next?
------------

What's next depends on what you want to do with Luz. If you want to practice some assembly programming, just write LASM code, consulting the user's manual. If you want to hack on Luz, study the code (a developer's guide is planned for the near future...)
