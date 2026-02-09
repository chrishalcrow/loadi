import pynapple as nap
from .base import BaseSession
from pathlib import Path
import pandas as pd
from typing import TypedDict
import numpy as np
from .base import BaseExperiment

data_path = Path("/run/user/1000/gvfs/smb-share:server=cmvm.datastore.ed.ac.uk,share=cmvm/sbms/groups/CDBS_SIDB_storage/NolanLab/ActiveProjects/Bri/optetrode_recordings/")

class BriExperiment(BaseExperiment):

    def get_session(self, mouse, day, session_type):

        mouse_dict = self.data_paths.get(mouse)
        if mouse_dict is None:
             raise ValueError(f"No mouse called {mouse}. Possible mice are {self.data_paths.keys()}.")
        else:
             day_dict = mouse_dict.get(day)
             if day_dict is None:
                 raise ValueError(f"No day called {day}. Possible mice are {mouse_dict.keys()}.")
             else:
                  session_dict = day_dict.get(session_type)
                  if session_dict is None:
                      raise ValueError(f"No session called {session_type}. Possible mice are {day_dict.keys()}.")
                  else:
                    return BriSession(mouse, day, session_type, known_data_types=list(session_dict.keys()))


class PositionDict(TypedDict):
    Px: nap.Tsd
    Py: nap.Tsd

class BriSession(BaseSession):

    def __init__(self, mouse, date, session, known_data_types = None):
        self.mouse = mouse
        self.date = date
        self.session = session
        self.cache = {}
        self.known_data_types = known_data_types

    def _repr_html_(self):

        header_text = f"<b>Mouse</b> {self.mouse}, <b>Date</b> {self.date}, <b>Session</b> {self.session}<br />"
        streams_text = f"{self.known_data_types}"

        return header_text + streams_text


    def _get_session_folder(self) -> Path:
        if (session_folder := self.cache.get('session_folder')) is not None:
            return session_folder

        subfolders = ['chR2', 'control', 'inhibitory_opto']

        correct_subfolder = None
        for subfolder in subfolders:
            if len(list((data_path / subfolder).glob(self.mouse))) > 0:
                correct_subfolder = subfolder
                break

        if correct_subfolder is None:
            raise ValueError('No session folder found.')

        session_folder = list((data_path / f"{correct_subfolder}/{self.mouse}").glob(f'{self.mouse}_{self.date}_*_{self.session}'))[0]
        self.cache['session_folder'] = session_folder
        return session_folder

    def get_clusters_path(self) -> Path:
        session_folder = self._get_session_folder()
        return session_folder / "MountainSort/DataFrames/spatial_firing.pkl"

    def get_position_path(self) -> Path:
        session_folder = self._get_session_folder()
        position_file = session_folder / "MountainSort/DataFrames/position.pkl"
        return position_file

    def get_ephys_path(self) -> Path:
        ephys_folder = self._get_session_folder()
        return ephys_folder

    def load_ephys(self):
        import probeinterface as pi
        import spikeinterface.full as si

        path_to_ephys = self.get_ephys_path()
        recording = si.read_openephys(path_to_ephys, stream_id = "CH")

        tetrode_group = pi.ProbeGroup()
        for a in range(4):
            one_tetrode = pi.generate_tetrode()
            one_tetrode.move([a*250,0])
            tetrode_group.add_probe(one_tetrode)

        tetrode_group.set_global_device_channel_indices(range(16))
        recording = recording.set_probegroup(tetrode_group)

        return recording

    def load_clusters(self) -> nap.TsGroup:

        if (clusters := self.cache.get('clusters')) is not None:
            return clusters

        clusters_path = self.get_clusters_path()
        clusters_df = pd.read_pickle(clusters_path)

        sampling_frequency = 30_000

        spikes_dict = dict(zip(clusters_df['cluster_id'].values, clusters_df['firing_times'].values))
        spikes_dict_s = {key: nap.Ts(t=value/sampling_frequency) for key, value in spikes_dict.items()}
        spikes_frame = nap.TsGroup(data=spikes_dict_s)

        self.cache['clusters'] = spikes_frame
        return spikes_frame

    def load_position(self) -> PositionDict:

        if (positions := self.cache.get('positions')) is not None:
            return positions

        path_to_behaviour = self.get_position_path()
        position_df = pd.read_pickle(path_to_behaviour)

        Px = nap.Tsd(t=position_df['synced_time'].values, d=position_df['position_x'].values)
        Py = nap.Tsd(t=position_df['synced_time'].values, d=position_df['position_y'].values)

        beh_dict = {'Px': Px, 'Py': Py}

        self.cache['positions'] = beh_dict
        return beh_dict


    def make_sorting(self):
        import spikeinterface.full as si


        unit_dict = {}
        clusters = self.load_clusters()

        for cluster_id, spike_times in clusters.items():
            unit_dict[cluster_id] = np.round(spike_times.t*30_000)

        sort = si.NumpySorting.from_unit_dict(unit_dict, sampling_frequency=30_000)

        return sort


    def create_analyzer(self):

        import spikeinterface.full as si


        sort = self.make_sorting()
        rec = self.load_ephys()

        analyzer = si.create_sorting_analyzer(sorting=sort, recording=si.bandpass_filter(rec))
        analyzer.compute({
                'unit_locations': {},
                'random_spikes': {},
                'noise_levels': {},
                'templates': {},
                'spike_amplitudes': {},
                'isi_histograms': {},
                'spike_locations': {},
                'correlograms': {},
                'waveforms': {},
                'principal_components': {},
                'template_similarity': {'method': 'l2'},
                'quality_metrics': {},
                'template_metrics': {'include_multi_channel_metrics': False},
        })

        return analyzer
