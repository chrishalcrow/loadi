import json
from importlib import resources
from pathlib import Path

import numpy as np
import pynapple as nap
from scipy.io import loadmat
from spikeinterface.core import NumpySorting, aggregate_units
from spikeinterface.exporters import to_pynapple_tsgroup

from .base import BaseExperiment, BaseSession


class ChenBurgess2018Experiment(BaseExperiment):
    """ "
    Data from
        Spatial cell firing during virtual navigation of open arenas by head-restrained mice
        Guifen Chen, John Andrew King, Yi Lu, Francesca Cacucci, Neil Burgess
        Paper: https://elifesciences.org/articles/34789
        Data: https://osf.io/yvmf4/overview


    Data expected to be in the form:

    containing_folder/
        2dVR_data.mat
        vr_gain.mat
    """

    def __init__(
        self,
        containing_folder=None,
    ):
        if containing_folder is None:
            raise FileExistsError(
                'Please provide the the folder this dataset is stored in, using `containing_folder = "path/to/folder".'
            )
        self.containing_folder = Path(containing_folder)

        with (
            resources.files("loadi.resources.data_paths")
            .joinpath("Chen_Burgess_2018.json")
            .open("r") as f
        ):
            data_paths = json.load(f)

        with (
            resources.files("loadi.resources.data_paths")
            .joinpath("Chen_Burgess_2018_file_map.json")
            .open("r") as f
        ):
            file_map = json.load(f)

        self.file_map = file_map
        self.data_paths = data_paths
        self.session_class = ChenBurgess2018Session

    def get_session(self, mouse_id, day_id, session_id):
        if isinstance(mouse_id, int):
            mouse_id = str(mouse_id)

        if isinstance(day_id, int):
            day_id = str(day_id)

        mouse_dict = self.data_paths.get(mouse_id)
        if mouse_dict is None:
            raise ValueError(
                f"No mouse_id {mouse_id}. Possible mice are {self.data_paths.keys()}."
            )
        else:
            data_path = self.containing_folder / self.file_map[f"{mouse_id}"]
            if not data_path.is_file():
                raise FileNotFoundError(
                    f"Cannot find data path {data_path}, which contains rat {mouse_id}"
                )
            day_dict = mouse_dict.get(day_id)
            if day_dict is None:
                raise ValueError(
                    f"No day_id {day_id}. Possible session_ids are {mouse_dict.keys()}."
                )
            else:
                session_dict = day_dict.get(session_id)
                if session_dict is None:
                    raise ValueError(
                        f"No session_id called {session_id}. Possible mice are {day_dict.keys()}."
                    )
                else:
                    return self.session_class(
                        mouse_id,
                        day_id,
                        session_id,
                        known_data_types=session_dict,
                        data_path=data_path,
                    )


class ChenBurgess2018Session(BaseSession):
    def __init__(self, mouse, date, session, known_data_types=None, data_path=None):
        self.mouse = mouse
        self.date = date
        self.session = session
        self.cache = {}
        self.known_data_types = known_data_types

        data = loadmat(data_path)

        if mouse == "vr_gain_1061":
            self.session_data = data["VR_gain"][0][int(date)]["trialData"][0][
                int(session)
            ]
        else:
            self.session_data = data["data"]

    def _repr_html_(self):
        header_text = f"<b>Mouse</b> {self.mouse}, <b>Date</b> {self.date}, <b>Session</b> {self.session}<br />"
        streams_text = f"{self.known_data_types}"

        return header_text + streams_text

    def load_units(self) -> nap.TsGroup:
        sampling_rate = 30_000

        sortings = []
        for tetrode_id in range(8):
            if self.mouse == "2dVR":
                tetrode_data = self.session_data["spikeData"][0][int(self.date)][
                    tetrode_id
                ][0]
            else:
                tetrode_data = self.session_data[0]["spikeData"][0][tetrode_id][0]
            cluster_index = np.transpose(tetrode_data["cut"])[0]
            spike_timestamps = tetrode_data["timestamp"][:, 0]
            sample_times = np.round((spike_timestamps) * sampling_rate).astype(int)
            sort = NumpySorting.from_samples_and_labels(
                sample_times, cluster_index, sampling_frequency=30_000
            )
            sortings.append(sort)

        sorting = aggregate_units(sortings)
        spikes = to_pynapple_tsgroup(sorting)

        return spikes

    def load_subject_position(self):
        if self.mouse == "2dVR":
            xy = self.session_data["posData"][0][int(self.date)]["xy"][0][0]
            position_timesteps = np.transpose(
                self.session_data["posData"][0][int(self.date)]["times"][0][0]
            )[0]
        elif self.mouse == "vr_gain_1061":
            xy = self.session_data["posData"][0][0]["xy"][0][0]
            position_timesteps = np.transpose(
                self.session_data["posData"][0][0]["times"][0][0]
            )[0]
        positions = nap.TsdFrame(t=position_timesteps, d=xy, columns=["Px", "Py"])

        return positions

    def load_object_position(self):
        x = self.session_data["object_position"][0]["x"][0][0][0]
        y = self.session_data["object_position"][0]["y"][0][0][0]

        return np.array([x, y])
