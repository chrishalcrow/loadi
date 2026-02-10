import pynapple as nap
from .base import BaseSession, BaseExperiment, PositionDict
import numpy as np
from pathlib import Path
import json
from scipy.io import loadmat

from importlib import resources

# 'my_app.resources' is the dot-notation to your folder
# 'data.json' is the file name

class KanterMoser2025Experiment(BaseExperiment):

    def __init__(
        self, 
        containing_folder=Path("/home/nolanlab/Downloads/d-885b4936-9345-43bd-880e-eebc19898ded/"), 
        data_paths_path = Path("/home/nolanlab/Downloads/Q0FG-1X8_paths.json"),
    ):

        self.containing_folder = containing_folder
        with resources.files('loadi.resources.data_paths').joinpath('Kanter_Moser_2025.json').open('r') as f:
            data_paths = json.load(f)

        self.data_paths = data_paths


    def get_session(self, rat_id, session_id):

        mouse_dict = self.data_paths.get(rat_id)
        if mouse_dict is None:
             raise ValueError(f"No mouse called {rat_id}. Possible mice are {self.data_paths.keys()}.")
        else:
             day_list = mouse_dict.get(session_id)
             if day_list is None:
                 raise ValueError(f"No day called {session_id}. Possible mice are {mouse_dict.keys()}.")
             else:
                 filepath = self.containing_folder / 'data' / rat_id / (rat_id + "_" + session_id + ".nwb")
                 return KanterMoser2025Session(rat_id, session_id, known_data_types=day_list, filepath=filepath)

class KanterMoser2025Session(BaseSession):

    def __init__(self, rat_id, session_id, known_data_types = None, filepath = None):
        self.mouse = rat_id
        self.date = session_id
        self.cache = {}
        self.known_data_types = known_data_types

        self.data = nap.load_file(filepath)

    def _repr_html_(self):

        header_text = f"<b>Rat id</b> {self.mouse}, <b>Session id</b> {self.date}<br />"
        streams_text = f"{self.known_data_types}"

        return header_text + streams_text

    def load_units(self) -> nap.TsGroup:
        
        return self.data['units']
    
    def load_animal_position(self) -> PositionDict:

        return self.data['animal_position']
    
