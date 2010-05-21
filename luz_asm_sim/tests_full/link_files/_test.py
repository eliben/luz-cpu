def test_addition_result(sim):
    return sim.reg_value(1) == 250 and sim.reg_value(2) == 250

def test_halted(sim):
    return sim.halted