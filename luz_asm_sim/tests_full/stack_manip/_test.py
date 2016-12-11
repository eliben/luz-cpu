def test_sp_reg_back(sim):
    return sim.reg_value(29) == sim.reg_value(9)

def test_addition(sim):
    return sim.reg_value(8) == (0x45678901 + 0xABBACEED + 
                                0x12 + 0x98 + 0xFFFF)


