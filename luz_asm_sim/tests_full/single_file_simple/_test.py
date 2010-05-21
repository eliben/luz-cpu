def test_regs(sim):
    return sim.reg_value(5) == 0x45

def test_halted(sim):
    return sim.halted


