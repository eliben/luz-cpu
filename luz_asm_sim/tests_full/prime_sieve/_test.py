def test_intsqrt(sim):
    
    return sim.debugq.items == [
        0xFAFAFAFA,
        2, 3, 5, 7, 11, 13,      # 6 primes
        0xEEEEBAAB,
        4,                          # intsqrt(20)
        321,                        # intsqrt(103456)
    ]
        


