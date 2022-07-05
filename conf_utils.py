#!/usr/bin/env python3
'''Utilities for YAML setting file.'''
from tone_conf import ToneConf

def read_tone(max_ch:int, tone_setting:dict) -> ToneConf:
    '''Parse dictionary to yield ToneConf.

    Parameters
    ----------
    max_ch : int
        Number of DDSes in the FPGA firmware.
    tone_setting : dict
        Tone setting dictionary from YAML setting file.

    Returns
    -------
    tone_conf : ToneConf
        Tone configuration object.
    '''
    return ToneConf(max_ch,
                    tone_setting['freq_MHz'],
                    phases=tone_setting.get('phases'),
                    amps=tone_setting.get('amps'),
                    power=tone_setting.get('power'))


def main():
    '''Main function.'''
    print('bye')

if __name__ == '__main__':
    main()
