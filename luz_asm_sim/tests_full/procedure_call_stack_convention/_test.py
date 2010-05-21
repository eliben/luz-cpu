def test_calling_nummult(sim):
    return (    sim.reg_alias_value('$s5') == 0x562 * 0x18A and
                sim.reg_alias_value('$s6') & 0x1 == 1)


def test_scalarproduct(sim):
    # the scalar product tested
    return sim.reg_alias_value('$s4') == 94078

