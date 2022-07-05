#!/usr/bin/env python3
'''Environment setting for observation scripts.
'''
import sys
import yaml


ENV_DEFAULT = {
    'rhea_comm':{
        'path': './rhea_comm',
        'load': True
    },
    'mkid_pylibs':{
        'path': '.',
        'load': False
    }
}

class ObsEnv:
    '''Observation environment manager.

    Parameter
    ---------
    env_path : str or Path, optional
        Path to the yaml file that has environmental setup information.
    '''
    def __init__(self, envpath=None):
        if envpath is None:
            self._env_dict = ENV_DEFAULT
        else:
            with open(envpath, encoding='utf-8') as f_desc:
                self._env_dict = yaml.safe_load(f_desc)['env']

        self._loaded = False

    def load(self, force=False):
        '''Load environment.'''
        if self._loaded and (not force):
            return

        for _, target in self._env_dict.items():
            if target['load']:
                sys.path.append(target['path'])
