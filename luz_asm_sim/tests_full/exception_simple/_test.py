def test_main(sim):
    return sim.debugq.items == [0xABBA, 0xBEEF, 0x3, 0x44]

