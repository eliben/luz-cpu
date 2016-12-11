def test_addition_result(sim):
    return sim.reg_value(8) == 543

def test_halted(sim):
    return sim.halted