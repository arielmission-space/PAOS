"""
Dictionary for optical materials for use in ``PAOS``.
"""

materials = {
    "CAF2": {
        "source": "Handbook of Optics Vol. II",
        "Tref": 20.0,
        "sellmeier": {
            "K1": 5.67588800e-001,
            "L1": 2.52643000e-003,
            "K2": 4.71091400e-001,
            "L2": 1.00783330e-002,
            "K3": 3.84847230e000,
            "L3": 1.20055600e003,
        },
        "Tmodel": {"D0": -2.6600e-005},
    },
    "SAPPHIRE": {
        "source": "The Infrared & Electro-Optical Systems Handbook V. III",
        "Tref": 20.0,
        "sellmeier": {
            "K1": 1.023798000e00,
            "L1": 3.775880000e-03,
            "K2": 1.058264000e00,
            "L2": 1.225440000e-02,
            "K3": 5.280792000e00,
            "L3": 3.213616000e02,
        },
        "Tmodel": {"D0": 1.80000000e-05},
    },
    "ZNSE": {
        "source": "Handbook of Optics Vol. II",
        "Tref": 20.0,
        "sellmeier": {
            "K1": 4.29801490e000,
            "L1": 3.68881960e-002,
            "K2": 6.27765570e-001,
            "L2": 1.43476258e-001,
            "K3": 2.89556330e000,
            "L3": 2.20849196e003,
        },
        "Tmodel": {"D0": 5.5400e-005},
    },
    "BK7": {
        "source": "catalog ADEPT-INFRARED.AGF",
        "Tref": 20.0,
        "sellmeier": {
            "K1": 1.03961212e000,
            "L1": 6.00069867e-003,
            "K2": 2.31792344e-001,
            "L2": 2.00179144e-002,
            "K3": 1.01046945e000,
            "L3": 1.03560653e002,
        },
        "Tmodel": {"D0": 1.8600e-006},
    },
    "SF6": {
        "source": "catalog SCHOTT.AGF",
        "Tref": 20.0,
        "sellmeier": {
            "K1": 1.724484820e000,
            "L1": 1.348719470e-002,
            "K2": 3.901048890e-001,
            "L2": 5.693180950e-002,
            "K3": 1.045728580e000,
            "L3": 1.185571850e002,
        },
        "Tmodel": {"D0": 6.69000000e-006},
    },
    "SF11": {
        "source": "catalog ADEPT-INFRARED.AGF",
        "Tref": 20.0,
        "sellmeier": {
            "K1": 1.73848403e000,
            "L1": 1.36068604e-002,
            "K2": 3.11168974e-001,
            "L2": 6.15960463e-002,
            "K3": 1.17490871e000,
            "L3": 1.21922711e002,
        },
        "Tmodel": {"D0": 1.1200e-005},
    },
    "BAF2": {
        "source": "Handbook of Optics Vol. II",
        "Tref": 20.0,
        "sellmeier": {
            "K1": 6.43356000e-001,
            "L1": 3.34000000e-003,
            "K2": 5.06762000e-001,
            "L2": 1.20300000e-002,
            "K3": 3.82610000e000,
            "L3": 2.15169810e003,
        },
        "Tmodel": {"D0": -4.4600e-005},
    },
}
