from paos.gui.core.shared import to_configparser


def to_ini(input, config, tmp):
    dictionary = {}
    dictionary["general"] = {
        "project": input.project(),
        "version": input.version(),
        "grid_size": input.grid_size(),
        "zoom": input.zoom(),
        "lens_unit": "m",
        "Tambient": input.tambient(),
        "Pambient": input.pambient(),
    }

    values = input.__dict__["_map"]

    def get_value(key):
        return "" if key not in values.keys() else values[key]()

    dictionary["wavelengths"] = {}
    for key in values.keys():
        if "Wavelength" in key:
            i = int(key.split("_")[1])
            dictionary["wavelengths"][f"w{i}"] = get_value(key)

    dictionary["fields"] = {}
    for key in values.keys():
        if "Field" in key:
            i = int(key.split("_")[1])
            dictionary["fields"][f"f{i}"] = get_value(key)

    nlenses = len({key for key in values.keys() if "lens_SurfaceType" in key})
    for i in range(1, nlenses + 1):
        surface_type = get_value(f"lens_SurfaceType_{i}_1")

        dictionary[f"lens_{i:02d}"] = {
            "surfacetype": surface_type,
        }

        if surface_type == "Zernike":
            zcoeffs = {
                key: values[key]() for key in values.keys() if f"lens_{i}_Zcoeff" in key
            }
            zcoeffs = dict(
                sorted(zcoeffs.items(), key=lambda item: int(item[0].split("_")[3]))
            )
            zcoeffs = list(zcoeffs.values())
            if not zcoeffs:
                zcoeffs = config.get()[f"lens_{i:02d}"]["z"].split(",")
            zindex = list(range(len(zcoeffs)))
            zcoeffs = ",".join(zcoeffs)
            zindex = ",".join(map(str, zindex))

            dictionary[f"lens_{i:02d}"]["zindex"] = zindex
            dictionary[f"lens_{i:02d}"]["z"] = zcoeffs

        aperture_type = get_value(f"lens_Aperture_Type_{i}_9")
        aperture_xhw = get_value(f"lens_Aperture_xhw_{i}_9")
        aperture_yhw = get_value(f"lens_Aperture_yhw_{i}_9")
        aperture_xdecenter = get_value(f"lens_Aperture_xdecenter_{i}_9")
        aperture_ydecenter = get_value(f"lens_Aperture_ydecenter_{i}_9")
        aperture = (
            ""
            if aperture_type == ""
            else f"{aperture_type},{aperture_xhw},{aperture_yhw},{aperture_xdecenter},{aperture_ydecenter}"
        )

        dictionary[f"lens_{i:02d}"].update(
            {
                "comment": get_value(f"lens_Comment_{i}_2"),
                "radius": get_value(f"lens_Radius_{i}_3"),
                "thickness": get_value(f"lens_Thickness_{i}_4"),
                "material": get_value(f"lens_Material_{i}_5"),
                "save": get_value(f"lens_Save_{i}_6"),
                "ignore": get_value(f"lens_Ignore_{i}_7"),
                "stop": get_value(f"lens_Stop_{i}_8"),
                "aperture": aperture,
                "par1": get_value(f"lens_Par1_{i}_10"),
                "par2": get_value(f"lens_Par2_{i}_11"),
                "par3": get_value(f"lens_Par3_{i}_12"),
                "par4": get_value(f"lens_Par4_{i}_13"),
                "par5": get_value(f"lens_Par5_{i}_14"),
                "par6": get_value(f"lens_Par6_{i}_15"),
                "par7": get_value(f"lens_Par7_{i}_16"),
                "par8": get_value(f"lens_Par8_{i}_17"),
            }
        )

    config.set(to_configparser(dictionary))

    with open(tmp, "w") as cf:
        config.get().write(cf)
