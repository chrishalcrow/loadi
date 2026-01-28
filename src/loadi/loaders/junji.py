import pynapple as nap
import probeinterface as pi
from .base import BaseSession
from pathlib import Path
import pandas as pd
from typing import TypedDict
import spikeinterface.full as si
import numpy as np

class PositionDict(TypedDict):
    Px: nap.Tsd
    Py: nap.Tsd

class JunjiSession(BaseSession):

    def __init__(self, mouse, day, session_type, active_projects_path="/run/user/1000/gvfs/smb-share:server=cmvm.datastore.ed.ac.uk,share=cmvm/sbms/groups/CDBS_SIDB_storage/NolanLab/ActiveProjects/"):
        self.mouse = mouse
        self.day = day
        self.session_type = session_type
        self.active_projects_path = Path(active_projects_path)
        self.cache = {}

    def _get_session_folder(self) -> Path:
        session_type_folders = [
            self.active_projects_path / "Junji/Data/2019cohort1/" / self.session_type,
            self.active_projects_path / "Junji/Data/2021cohort1/" / self.session_type,
            self.active_projects_path / "Junji/Data/2021cohort2/" / self.session_type,
            self.active_projects_path / "Junji/Data/2022cohort1/" / self.session_type,
        ]
        for session_type_folder in session_type_folders:
            session_folder_list = list(session_type_folder.glob(f'M{self.mouse}_D{self.day}*'))
            if len(session_folder_list) > 0:
                return session_folder_list[0]

        raise FileNotFoundError("Can't find session folder.")

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

    def get_ephys(self) -> si.BaseRecording:

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

    def get_clusters(self) -> nap.TsGroup:

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

    def get_position(self) -> PositionDict:

        if (positions := self.cache.get('positions')) is not None:
            return positions

        path_to_behaviour = self.get_position_path()
        position_df = pd.read_pickle(path_to_behaviour)

        Px = nap.Tsd(t=position_df['synced_time'].values, d=position_df['position_x'].values)
        Py = nap.Tsd(t=position_df['synced_time'].values, d=position_df['position_y'].values)

        beh_dict = PositionDict(Px = Px, Py = Py)

        self.cache['positions'] = beh_dict
        return beh_dict


    def make_sorting(self) -> si.NumpySorting:

        unit_dict = {}
        clusters = self.get_clusters()

        for cluster_id, spike_times in clusters.items():
            unit_dict[cluster_id] = np.round(spike_times.t*30_000)

        sort = si.NumpySorting.from_unit_dict(unit_dict, sampling_frequency=30_000)

        return sort


    def create_analyzer(self) -> si.SortingAnalyzer:

        si.set_global_job_kwargs(n_jobs=2)

        sort = self.make_sorting()
        rec = self.get_ephys()

        analyzer = si.create_sorting_analyzer(sorting=sort, recording=si.bandpass_filter(rec))
        analyzer.compute({
                'unit_locations': {},
                'random_spikes': {},
                'noise_levels': {},
                'templates': {},
                'spike_amplitudes': {},
                'amplitude_scalings': {},
                'isi_histograms': {},
                'spike_locations': {},
                'correlograms': {},
                'template_similarity': {'method': 'l2'},
                'quality_metrics': {},
                'template_metrics': {'include_multi_channel_metrics': False},
        })

        return analyzer
