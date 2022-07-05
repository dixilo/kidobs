#!/usr/bin/env python3
'''Orchestration of trigger measurment.'''
from datetime import datetime, timezone, timedelta
from pathlib import Path
from copy import deepcopy
from time import sleep
from sys import stderr
from argparse import ArgumentParser
import numpy as np

from fpga_control import FPGAControl
from sg_manager import QuickSyn
from measure_trg import measure_trg
import yaml

from conf_utils import read_tone
from freq_finder import SweepObs

JST = timezone(timedelta(hours=+9), 'JST')

class TrgManager:
    '''Trigger measurement manager.

    Parameter
    ---------
    path : str or pathlib.Path
        Path to the setting YAML file.
    '''
    def __init__(self, path='./default.yaml'):
        with open(path, encoding='utf-8') as f_desc:
            conf = yaml.safe_load(f_desc)
            trg_setting = conf['trg']
            fpga_setting = conf['fpga']
            sg_setting = conf['sg']
            tone_setting = conf['tone']

        self._schedule = trg_setting['schedule']
        self._path_base = Path(trg_setting['basedir']['path'])
        self._subdict = trg_setting['subdir']
        self._swp = trg_setting['sweep']
        self._meas = trg_setting['meas']

        self._fpga = FPGAControl(ip_address=fpga_setting['ip'])

        # Tones
        self._tone_conf = read_tone(self._fpga.max_ch, tone_setting)
        self._kid_indices = tone_setting['kid_indices']

        self._lo_gigahz = sg_setting['freq_gigahz']
        self._lo_hz = self._lo_gigahz * 1e9

        # synthesizer
        synthesizer = QuickSyn(port=sg_setting['port'])
        synthesizer.set_freq_mHz(int(self._lo_hz*1e3))
        synthesizer.close()
        del synthesizer

    def _subdir(self, runid):
        if self._subdict['make_subdir']:
            dirname = self._subdict['dirbase']
            dirname += str(runid).zfill(self._subdict['n_zfill'])
            path = self._path_base.joinpath(dirname)
            if not path.exists():
                path.mkdir()
        else:
            path = self._path_base

        return path

    def _swp_path(self, path:Path, runid:int):
        if self._subdict['make_subdir']:
            return path.joinpath('swp.rawdata')

        swpname = 'swp'
        swpname += str(runid).zfill(self._subdict['n_zfill'])
        swpname += '.rawdata'

        return path.joinpath(swpname)

    def _swp_fig_path(self, path:Path, runid:int, kidid:int):
        if self._subdict['make_subdir']:
            return path.joinpath(f'swp_{kidid:03d}.png')

        figname = 'swp'
        figname += str(runid).zfill(self._subdict['n_zfill'])
        figname += f'_{kidid:03d}.png'

        return path.joinpath(figname)

    def _trg_path(self, path:Path, trg_index:int):
        fname = f'trg_{str(trg_index).zfill(self._meas["n_zfill"])}.rawdata'

        return path.joinpath(fname)

    def run(self):
        '''Perform measurement.'''
        while True:
            dt_now = datetime.now(tz=JST)
            target = None

            for i, sdict in enumerate(self._schedule):
                if dt_now < sdict['end']:
                    target = sdict
                    runid = i
                    break

            if target is None:
                return

            path = self._subdir(runid)
            path_swp = self._swp_path(path, runid)

            # wait until the time comes
            while datetime.now(tz=JST) < target['start']:
                print(f'waiting...{target["start"]}', file=stderr)
                sleep(20)

            # perform sweep measurement
            print('Starting sweep measurement.', file=stderr)
            swpobs = SweepObs(self._fpga,
                              self._tone_conf.freq_if_megahz,
                              path=path_swp,
                              width_megahz=self._swp['width_megahz'],
                              resolution_megahz=self._swp['resolution_megahz'],
                              lo_hz=self._lo_hz,
                              power=self._swp['power'],
                              kid_indices=self._kid_indices,
                              verbose=True)

            swpobs.do_measurement()
            swpobs.analyze()

            # Quick plot
            for kidid in self._kid_indices:
                fig, _ = swpobs.plot(kidid)
                figpath = self._swp_fig_path(path, runid, kidid)
                fig.savefig(figpath)

            newtone = deepcopy(self._tone_conf)

            for kidid in self._kid_indices:
                newtone.freq_if[kidid] = np.round(swpobs.fr_loc(kidid), -3)

            print(f'Resonant freqs [MHz]: {[f/1e6 for f in newtone.freq_if]}', file=stderr)
            # Trigger measurement
            trg_index = 0
            while True:
                now = datetime.now(tz=JST)
                print('=============', file=stderr)
                print(f'Trigger #: {trg_index}', file=stderr)
                print('=============', file=stderr)

                if target['end'] < now:
                    break

                measure_trg(self._fpga, newtone,
                            data_length=self._meas['length'],
                            thre_sigma=self._meas['threshold'],
                            thre_count=self._meas['count'],
                            rate_ksps=self._meas['rate'],
                            trig_pos=self._meas['position'],
                            pre_length=self._meas['pre_length'],
                            fname=self._trg_path(path, trg_index),
                            end=target['end'])

                trg_index += 1


def main():
    '''Trigger measurement orchestration.'''
    parser = ArgumentParser()

    parser.add_argument('path_yaml',
                        type=str,
                        nargs='?',
                        default='./default.yaml',
                        help='Path to the YAML setting file.')

    args = parser.parse_args()

    trg_man = TrgManager(args.path_yaml)
    trg_man.run()

if __name__ == '__main__':
    main()
