import pynapple as nap
from .base import BaseSession, BaseExperiment
import numpy as np
from pathlib import Path
import json
from typing import TypedDict
from scipy.io import loadmat

class Q0FG1X8Experiment(BaseExperiment):

    def __init__(
        self, 
        full_data_path=Path("/home/nolanlab/Downloads/singlecellanalyses_CA1.mat"), 
        data_paths_path = Path("/home/nolanlab/Downloads/Q0FG-1X8_paths.json"),
    ):

        self.full_data_path = full_data_path
        with open(data_paths_path) as f:
            self.data_paths = json.load(f)


    def get_session(self, rat_id, day_id, session_type):

        if isinstance(rat_id, int):
            rat_id = str(rat_id)

        if isinstance(day_id, int):
            day_id = str(day_id)

        mouse_dict = self.data_paths.get(rat_id)
        if mouse_dict is None:
             raise ValueError(f"No rat_id {rat_id}. Possible mice are {self.data_paths.keys()}.")
        else:
             day_dict = mouse_dict.get(day_id)
             if day_dict is None:
                 raise ValueError(f"No day_id {day_id}. Possible mice are {mouse_dict.keys()}.")
             else:
                  session_dict = day_dict.get(session_type)
                  if session_dict is None:
                      raise ValueError(f"No session_type called {session_type}. Possible mice are {day_dict.keys()}.")
                  else:
                    return Q0FG1X8Session(rat_id, day_id, session_type, known_data_types=session_dict, full_data_path=self.full_data_path)


class PositionDict(TypedDict):
    Px: nap.Tsd
    Py: nap.Tsd

class Q0FG1X8Session(BaseSession):

    def __init__(self, mouse, date, session, known_data_types = None, full_data_path = None):
        self.mouse = mouse
        self.date = date
        self.session = session
        self.cache = {}
        self.known_data_types = known_data_types

        data = loadmat(full_data_path)
        data_all_sessions = data['dataset'][0][0]['sessions'][0]

        session_id = self.date
        session_types = list(np.concat(data_all_sessions[int(session_id)]['trial']['trial_name'][0]))
        session_index = session_types.index(self.session)

        self.session_data = data_all_sessions[int(session_id)][2][0][session_index]

    def _repr_html_(self):

        header_text = f"<b>Mouse</b> {self.mouse}, <b>Date</b> {self.date}, <b>Session</b> {self.session}<br />"
        streams_text = f"{self.known_data_types}"

        return header_text + streams_text

    def load_clusters(self) -> nap.TsGroup:
        
        spikes_np = [np.transpose(spike_train[0])[0] for spike_train in self.session_data['units'][0]]
        spikes = nap.TsGroup(spikes_np)

        return spikes
    
    def load_position(self) -> PositionDict:

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
