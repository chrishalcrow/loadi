import pynapple as nap
from .base import BaseSession, BaseExperiment, PositionDict
import numpy as np
from pathlib import Path
import json
from scipy.io import loadmat
from importlib import resources

class NagelhusMoser2023Experiment(BaseExperiment):

    def __init__(
        self, 
        containing_folder=None, 
    ):
        if containing_folder is None:
            raise FileExistsError('Please provide the the folder this dataset is stored in, using `containing_folder = "path/to/folder".')
        self.containing_folder = Path(containing_folder)

        with resources.files('loadi.resources.data_paths').joinpath('Nagelhus_Moser_2023.json').open('r') as f:
            data_paths = json.load(f)

        with resources.files('loadi.resources.data_paths').joinpath('Nagelhus_Moser_2023_file_map.json').open('r') as f:
            file_map = json.load(f)
            
        self.file_map = file_map
        self.data_paths = data_paths
        self.session_class = NagelhusMoser2023Session


    def get_session(self, rat_id, day_id, session_type):

        if isinstance(rat_id, int):
            rat_id = str(rat_id)

        if isinstance(day_id, int):
            day_id = str(day_id)

        mouse_dict = self.data_paths.get(rat_id)
        if mouse_dict is None:
             raise ValueError(f"No rat_id {rat_id}. Possible mice are {self.data_paths.keys()}.")
        else:
            data_path = self.containing_folder / 'datasets' / self.file_map[f'{rat_id}_{day_id}']
            if not data_path.is_file():
                raise FileNotFoundError(f'Cannot find data path {data_path}, which contains rat {rat_id}')
            day_dict = mouse_dict.get(day_id)
            if day_dict is None:
                raise ValueError(f"No session_id {day_id}. Possible session_ids are {mouse_dict.keys()}.")
            else:
                session_dict = day_dict.get(session_type)
                if session_dict is None:
                    raise ValueError(f"No session_type called {session_type}. Possible mice are {day_dict.keys()}.")
                else:
                    return NagelhusMoser2023Session(rat_id, day_id, session_type, known_data_types=session_dict, data_path=data_path)


class NagelhusMoser2023Session(BaseSession):

    def __init__(self, mouse, date, session, known_data_types = None, data_path = None):
        self.mouse = mouse
        self.date = date
        self.session = session
        self.cache = {}
        self.known_data_types = known_data_types

        data = loadmat(data_path)
        data_all_sessions = data['dataset'][0][0]['sessions'][0]

        session_id = self.date.split('_')[-1]
        session_types = list(np.concat(data_all_sessions[int(session_id)]['trial']['trial_name'][0]))
        session_index = session_types.index(self.session)

        self.session_data = data_all_sessions[int(session_id)][2][0][session_index]

    def _repr_html_(self):

        header_text = f"<b>Mouse</b> {self.mouse}, <b>Date</b> {self.date}, <b>Session</b> {self.session}<br />"
        streams_text = f"{self.known_data_types}"

        return header_text + streams_text

    def load_units(self) -> nap.TsGroup:
        
        spikes_np = [np.transpose(spike_train[0])[0] for spike_train in self.session_data['units'][0]]
        spikes = nap.TsGroup(spikes_np)

        return spikes
    
    def load_subject_position(self) -> PositionDict:

        positions = self.session_data['tracking']
        x = np.transpose(positions['x'][0][0])[0]
        y = np.transpose(positions['y'][0][0])[0]
        timestamps = np.transpose(positions['timestamp'][0][0])[0]

        Px = nap.Tsd(timestamps, x)
        Py = nap.Tsd(timestamps, y)

        beh_dict = {'Px': Px, 'Py': Py}

        return beh_dict
    
    def load_object_position(self):

        x = self.session_data['object_position'][0]['x'][0][0][0]
        y = self.session_data['object_position'][0]['y'][0][0][0]

        return np.array([x,y])
