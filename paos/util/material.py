import numpy as np
import matplotlib.pyplot as plt
from ..paos_config import logger


class Material:
    """
    Class for handling different optical materials for use in `PAOS`
    """

    def __init__(self, wl, Tambient=-218.0, materials=None):
        """
        Parameters
        ----------
        Tambient: scalar
            Ambient temperature during operation
        wl: scalar or array
            wavelength in microns
        materials: dict
            library of materials for optical use
        """
        self.wl = wl
        self.Tambient = Tambient
        if materials is None:
            from .lib import materials
            logger.debug('Using default library of optical materials')
        self.materials = materials

    def sellmeier(self, par):
        """
        Implements the Sellmeier 1 equation to estimate the glass
        index of refraction relative to air at the glass reference temperature,
        :math:`T_{ref} = 20^{\\circ}`, and pressure, :math:`P_{ref} = 1 \\ atm`.
        The Sellmeier 1 equation consists of three terms and is given as
        :math:`\\displaystyle n^{2}(\\lambda )=1+{\\frac {K_{1}\\lambda ^{2}}{\\lambda ^{2}-L_{1}}}+
        {\\frac {K_{2}\\lambda ^{2}}{\\lambda ^{2}-L_{2}}}+{\\frac {K_{3}\\lambda ^{2}}{\\lambda ^{2}-L_{3}}}`

        Parameters
        ----------
        par: dict
            dictionary containing the :math:`K_1`, :math:`L_1`, :math:`K_2`, :math:`L_2`, :math:`K_3`, :math:`L_3`
            parameters of the Sellmeier 1 model

        Returns
        -------
        scalar or array
            the refractive index
        """
        wl2 = self.wl ** 2
        n2_1 = par['K1'] * wl2 / (wl2 - par['L1'])
        n2_1 += par['K2'] * wl2 / (wl2 - par['L2'])
        n2_1 += par['K3'] * wl2 / (wl2 - par['L3'])

        return np.sqrt(n2_1 + 1.0)

    @staticmethod
    def nT(n, D0, delta_T):
        """
        Estimate the change in the glass absolute index of refraction with temperature as

        :math:`n(\\Delta T) = \\frac{n^2 - 1}{2 n} D_0 \\Delta T + n`

        Parameters
        ----------
        n: scalar or array
            relative index at the reference temperature of the glass
        D0: scalar
            model parameter
        delta_T: scalar
            change in temperature relative to the reference temperature of the glass.
            It is positive if the temperature is grater than the reference temperature

        Returns
        -------
        out: scalar or array (same shape as n)
            the scaled relative index
        """
        dnabs = (n ** 2 - 1.0) / (2.0 * n) * D0 * delta_T

        return n + dnabs

    def nair(self, T, P=1):
        """
        Estimate the air index of refraction at wavelength :math:`\\lambda`, temperature :math:`T`,
        and relative pressure :math:`P`.

        Parameters
        ----------
        T: scalar
            reference temperature in :math:`^{\\circ} K`
        P: scalar
            reference pressure in atmospheres. Defaults to 1 atm.
        """
        wl2 = self.wl ** 2

        nref = 1.0 + 1.0e-8 * (6432.8 + 2949810 * wl2 / (146 * wl2 - 1) + 25540 * wl2 / (41 * wl2 - 1))
        nair = 1 + (nref - 1) * P / (1.0 + 3.4785e-3 * (T - 15))

        return nair

    def nmat(self, name):
        """
        Given the name of an optical glass, returns the absolute and scaled relative index of refraction in
        function of wavelength.

        Parameters
        ----------
        name: str
            name of the optical glass

        Returns
        -------
        out: tuple
            returns two arrays for the glass index of refraction in function of wavelength:
            one for the absolute index and the other for the index relative to air.
        """

        name = name.upper()
        if name not in self.materials.keys():
            logger.error('Glass {} currently not supported.'.format(name))

        material = self.materials[name]
        logger.debug('Glass name: {} -- T ref: {}'.format(name, material['Tref']))

        nmat0 = self.sellmeier(par=material['sellmeier']) * self.nair(T=material['Tref'])
        nmat = self.nT(n=nmat0, D0=material['Tmodel']['D0'], delta_T=self.Tambient - material['Tref'])

        return nmat0, nmat

    def plot_relative_index(self, material_list=None, ncols=2, figname=None):
        """
        Given a list of materials for optical use, plots the relative index in function of wavelength,
        at the reference and operating temperature.

        Parameters
        ----------
        material_list: list
            a list of materials, e.g. ['SF11', 'ZNSE']
        ncols: int
            number of columns for the subplots
        figname: str
            name of figure to save

        Returns
        -------
        None
            displays the plot output or stores it to the indicated plot path

        Examples
        --------

        >>> from paos.util.material import Material
        >>> Material().plot_relative_index(material_list=['Caf2', 'Sf11', 'Sapphire'])

        """

        if material_list is None:
            material_list = []

        n_subplots = len(material_list)
        if ncols > n_subplots:
            ncols = n_subplots

        nrows = n_subplots // ncols
        if n_subplots % ncols:
            nrows += 1

        figsize = (8 * ncols, 6 * nrows)
        fig, ax = plt.subplots(nrows=nrows, ncols=ncols, figsize=figsize)
        fig.patch.set_facecolor('white')
        plt.subplots_adjust(hspace=0.3, wspace=0.5)

        for k, name in enumerate(material_list):

            if n_subplots == 1:
                axis = ax
            elif n_subplots == 2:
                axis = ax[k]
            else:
                i = k % ncols
                j = k // ncols
                axis = ax[j, i]

            nmat_abs, nmat = self.nmat(name)

            axis.plot(self.wl, nmat_abs, '--', label='T$_{ref}$')
            axis.plot(self.wl, nmat, label='T$_{oper}$')
            axis.set_title(name)
            axis.legend()
            axis.set_xlabel('Wavelength [micron]')
            axis.set_ylabel('Relative index')
            axis.grid()

            if n_subplots % ncols and k == n_subplots - 1:
                for col in range(i + 1, ncols):
                    ax[j, col].set_visible(False)

        if figname is not None:
            fig.savefig(figname, bbox_inches='tight', dpi=150)
            plt.close()
        else:
            fig.tight_layout()
            plt.show()

        return
