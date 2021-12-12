"""
Dictionary for optical materials for use in `PAOS`.
"""

materials = {
    'CAF2': {'source': 'Handbook of Optics Vol. II',
             'Tref': 20.0,
             'sellmeier': {
                 'K1': 5.67588800E-001,
                 'L1': 2.52643000E-003,
                 'K2': 4.71091400E-001,
                 'L2': 1.00783330E-002,
                 'K3': 3.84847230E+000,
                 'L3': 1.20055600E+003},
             'Tmodel': {
                 'D0': -2.6600E-005}
             },

    'SAPPHIRE': {'source': 'The Infrared & Electro-Optical Systems Handbook V. III',
                 'Tref': 20.0,
                 'sellmeier': {
                     'K1': 1.023798000E+00,
                     'L1': 3.775880000E-03,
                     'K2': 1.058264000E+00,
                     'L2': 1.225440000E-02,
                     'K3': 5.280792000E+00,
                     'L3': 3.213616000E+02},
                 'Tmodel': {
                     'D0': 1.80000000E-05}
                 },

    'ZNSE': {'source': 'Handbook of Optics Vol. II',
             'Tref': 20.0,
             'sellmeier': {
                 'K1': 4.29801490E+000,
                 'L1': 3.68881960E-002,
                 'K2': 6.27765570E-001,
                 'L2': 1.43476258E-001,
                 'K3': 2.89556330E+000,
                 'L3': 2.20849196E+003
             },
             'Tmodel': {
                 'D0': 5.5400E-005}
             },

    'BK7': {'source': 'not provided',
            'Tref': 20.0,
            'sellmeier': {
                'K1': 1.03961212E+000,
                'L1': 6.00069867E-003,
                'K2': 2.31792344E-001,
                'L2': 2.00179144E-002,
                'K3': 1.01046945E+000,
                'L3': 1.03560653E+002
            },
            'Tmodel': {
                'D0': 1.8600E-006}
            },

    'SF11': {'source': 'not provided',
             'Tref': 20.0,
             'sellmeier': {
                 'K1': 1.73848403E+000,
                 'L1': 1.36068604E-002,
                 'K2': 3.11168974E-001,
                 'L2': 6.15960463E-002,
                 'K3': 1.17490871E+000,
                 'L3': 1.21922711E+002
             },
             'Tmodel': {
                 'D0': 1.1200E-005}
             },

    'BAF2': {'source': 'Handbook of Optics Vol. II',
             'Tref': 20.0,
             'sellmeier': {
                 'K1': 6.43356000E-001,
                 'L1': 3.34000000E-003,
                 'K2': 5.06762000E-001,
                 'L2': 1.20300000E-002,
                 'K3': 3.82610000E+000,
                 'L3': 2.15169810E+003
             },
             'Tmodel': {
                 'D0': -4.4600E-005}
             },

}