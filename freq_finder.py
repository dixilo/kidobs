#!/usr/bin/env python3
'''Sweep helper'''
import matplotlib.pyplot as plt


from measure_mulswp import measure_mulswp
from mkid_pylibs.readfile import readfile_swp

class SweepObs:
    '''Sweeep observation helper'''
    def __init__(self, fpga, freqs_megahz, path=None, width_megahz=6,
                 resolution_megahz=0.01, lo_hz=4e9, power=1,
                 kid_indices=None, verbose=False):
        self.fpga = fpga
        self.freq = freqs_megahz

        if path is None:
            self.path = 'tmpswp.rawdata'
        else:
            self.path = path

        self.width = width_megahz
        self.resolution = resolution_megahz
        self.done = False
        self._fit_result = None
        self.lo_hz = lo_hz
        self.verbose = verbose
        self.power = power

        self.swp_kids = None

        if kid_indices is None:
            self.kid_indices = [0]
        else:
            self.kid_indices = kid_indices

        self._fit_results = None

    def do_measurement(self, force=False):
        '''Perform mulsweep measurement.

        Parameter
        ---------
        force : bool
            Perform measurement regardless of whether or not the it has been done before.
        '''
        if self.done and (not force):
            return

        measure_mulswp(self.fpga,
                       max_ch=self.fpga.max_ch,
                       dds_f_megahz=self.freq,
                       width=self.width,
                       step=self.resolution,
                       fname=self.path,
                       power=self.power,
                       verbose=self.verbose)

        self.done = True

    @property
    def analyzed(self):
        '''Returns the status of sweep analysis.

        Returns
        -------
        analyzed : bool
            True if already analyzed.
        '''
        return self._fit_result is not None

    @property
    def fit_results(self):
        '''Fit result.

        Returns
        -------
        fit_results : list of FitResult
            Fitting results.
        '''
        if not self.analyzed:
            self.analyze()

        return self._fit_results

    def analyze(self):
        '''Perform analysis.'''

        if not self.done:
            raise Exception('Not sweeped/analyzed yet.')

        self.swp_kids = {index:readfile_swp('rhea', self.path, lo=self.lo_hz, index=index)
                            for index in self.kid_indices}
        self._fit_results = {kidid: swp.fitIQ() for kidid, swp in self.swp_kids.items()}

    def plot(self, index=0):
        '''Plot frequency sweep data and analysis results.

        Parameter
        ---------
        index : int, optional
            KID index to be plotted.
        '''
        if (not self.done) or (not self.analyzed):
            raise Exception('Not sweeped/analyzed yet.')

        swp = self.swp_kids[index]
        fitr = self.fit_results[index]

        fig, axarr = plt.subplots(1, 2, figsize=(8,4))
        axarr[0].plot(swp.x/1e6, swp.amplitude)
        axarr[0].set_ylim([0, max(swp.amplitude)*1.1])
        axarr[0].axvline(fitr.fitparamdict['fr']/1e6, ls='--', color='r')

        resiq = fitr.rewind(swp.x, fitr.fitted(swp.x))
        diq = fitr.rewind(swp.x, swp.iq)
        axarr[1].plot(resiq.real, resiq.imag)
        axarr[1].plot(diq.real[::5], diq.imag[::5], marker='.', ls='')

        return fig, axarr


    def f_r(self, index=0):
        '''Resonant frequency.

        Parameters
        ----------
        index : int
            KID index.

        Returns
        -------
        fr : float
            Resonant frequency.
        '''
        return self.fit_results[index].fitparamdict['fr']

    def fr_loc(self, index):
        '''Resonant frequency in DAC (IF) frequency.

        fr_loc : float
            IF frequency in Hz.
        '''
        return self.f_r(index) - self.lo_hz


def main():
    '''Main function'''
    print('bye.')

if __name__ == '__main__':
    main()
