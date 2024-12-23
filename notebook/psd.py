import marimo

__generated_with = "0.10.6"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("""# Plot PSD""")
    return


@app.cell
def _(mo):
    mo.md(
        r"""The PSD is given by the following expression: PSD(f) = $\frac{A}{B + (f/f_{knee})^C}$"""
    )
    return


@app.cell
def _(mo):
    zoom = mo.ui.number(value=4, label="Zoom")
    grid = mo.ui.number(value=1024, label="Grid size")

    mo.hstack([zoom, grid], justify="start")
    return grid, zoom


@app.cell
def _(mo):
    phi_x = mo.ui.number(value=110.0, label=r"Phi$_x$")
    phi_y = mo.ui.number(value=73.0, label=r"Phi$_y$")

    mo.hstack([phi_x, phi_y], justify="start")
    return phi_x, phi_y


@app.cell
def _(mo):
    seed = mo.ui.number(value=42, step=1, label="Random seed")

    seed
    return (seed,)


@app.cell
def _(mo):
    A = mo.ui.number(value=7.0, label="A")
    B = mo.ui.number(value=0.0, label="B")
    C = mo.ui.number(value=1.5, label="C")
    fknee = mo.ui.number(value=1.0, label="fknee")
    fmin = mo.ui.number(value=1 / 20, label="fmin")
    fmax = mo.ui.number(value=1 / 2, label="fmax")
    SR = mo.ui.number(value=0.0, label="Surface Roughness")

    mo.vstack(
        [
            mo.hstack(
                [A, B, C, fknee],
            ),
            mo.hstack(
                [fmin, fmax],
            ),
            SR,
        ],
        align="start",
    )
    return A, B, C, SR, fknee, fmax, fmin


@app.cell
def _(mo):
    unit = mo.ui.dropdown(["m", "mm", "um", "nm"], label="PSD rms units", value="nm")

    unit
    return (unit,)


@app.cell
def _(compute_psd, plot_psd):
    psd = compute_psd()
    plot_psd(psd)
    return (psd,)


@app.cell
def _(A, B, C, fknee, fmax, fmin, mo, psd, u, unit):
    mo.md(
        f"Desired PSD rms is {psd.sfe_rms(A.value, B.value, C.value, fknee.value, fmin.value, fmax.value):.2f} {u.Unit(unit.value)}"
    )
    return


@app.cell
def _(mo):
    mo.md(r"""Note: the SR is added to the desired PSD""")
    return


@app.cell
def _(grid, plt, zoom):
    def plot_psd(wfo):
        plt.figure()
        im = plt.imshow(wfo(), cmap="Reds", origin="lower")
        plt.xlim(
            grid.value // 2 - grid.value // (2 * zoom.value),
            grid.value // 2 + grid.value // (2 * zoom.value),
        )
        plt.ylim(
            grid.value // 2 - grid.value // (2 * zoom.value),
            grid.value // 2 + grid.value // (2 * zoom.value),
        )
        plt.colorbar(im, ax=plt.gca(), label="Error [m]")
        return plt.gca()

    return (plot_psd,)


@app.cell
def _(
    A,
    B,
    C,
    PSD,
    SR,
    fknee,
    fmax,
    fmin,
    grid,
    np,
    phi_x,
    phi_y,
    seed,
    u,
    unit,
    zoom,
):
    def compute_psd():

        np.random.seed(seed.value)

        D = zoom.value * np.max([phi_x.value, phi_y.value])
        delta = D / grid.value

        x = y = np.arange(-grid.value // 2, grid.value // 2) * delta
        xx, yy = np.meshgrid(x, y)
        pupil = np.zeros((grid.value, grid.value))

        mask = (2 * xx / phi_x.value) ** 2 + (2 * yy / phi_y.value) ** 2 <= 1
        pupil[mask] = 1.0
        wfo = np.ma.masked_array(pupil, mask=~mask)

        fx = np.fft.fftfreq(wfo.shape[0], delta)
        fxx, fyy = np.meshgrid(fx, fx)
        f = np.sqrt(fxx**2 + fyy**2)
        f[f == 0] = 1e-100

        return PSD(
            wfo,
            A.value,
            B.value,
            C.value,
            f,
            fknee.value,
            fmin.value,
            fmax.value,
            SR.value,
            units=u.Unit(unit.value),
        )

    return (compute_psd,)


@app.cell
def _():
    import marimo as mo

    from paos import PSD
    import numpy as np
    import matplotlib.pyplot as plt
    import astropy.units as u

    return PSD, mo, np, plt, u


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
