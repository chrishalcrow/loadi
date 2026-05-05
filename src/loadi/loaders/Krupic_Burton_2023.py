import json
from importlib import resources
from pathlib import Path
from typing import Literal

import numpy as np
import pynapple as nap
from scipy.io import loadmat

from .base import BaseExperiment, BaseSession


class KrupicBurton2023Experiment(BaseExperiment):
    """ "
    Data from
        Data for Simultaneous representation of multiple time horizons by entorhinal grid cells and CA1 place cells, Cell Reports
         Julija Krupic, Prannoy Chaudhuri-Vayalambrone,, Michael Rule, Marino Krstulovic, Pauline Kerekes, Marius Bauza, Stephen Burton
        Data: https://figshare.com/articles/dataset/Data_for_Simultaneous_representation_of_multiple_time_horizons_by_entorhinal_grid_cells_and_CA1_place_cells_Cell_Reports/22794161/1?file=40506140

    Data expected to be in the form:

    containing_folder/
        r2288_180515a_tet2_cell2_GC.mat
        ...


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
            .joinpath("Krupic_Burton_2023.json")
            .open("r") as f
        ):
            data_paths = json.load(f)

        self.data_paths = data_paths
        self.session_class = KrupicBurton2023Session

    def get_session(self, subject_id, day_id, session_id):
        if isinstance(subject_id, int):
            subject_id = str(subject_id)

        if isinstance(day_id, int):
            day_id = str(day_id)

        mouse_dict = self.data_paths.get(subject_id)
        if mouse_dict is None:
            raise ValueError(
                f"No subject_id {subject_id}. Possible subject_ids are {self.data_paths.keys()}."
            )
        else:
            day_dict = mouse_dict.get(day_id)
            if day_dict is None:
                raise ValueError(
                    f"No session_id {day_id}. Possible session_ids are {mouse_dict.keys()}."
                )
            else:
                session_dict = day_dict.get(session_id)
                if session_dict is None:
                    raise ValueError(
                        f"No session_type called {session_id}. Possible mice are {day_dict.keys()}."
                    )
                else:
                    return KrupicBurton2023Session(
                        subject_id,
                        day_id,
                        session_id,
                        self.containing_folder,
                    )


class KrupicBurton2023Session(BaseSession):
    def __init__(self, mouse, date, session, containing_folder):
        self.mouse = mouse
        self.date = date
        self.session = session
        self.datapaths = list(containing_folder.glob(f"{mouse}_{date}{session}*"))

        self.data = [loadmat(datapath) for datapath in self.datapaths]

    def _repr_html_(self):
        header_text = f"<b>Mouse</b> {self.mouse}, <b>Date</b> {self.date}, <b>Session</b> {self.session}<br />"

        return header_text

    def load_units(self) -> nap.TsGroup:
        all_spike_times = {}
        cell_types = []
        for datapath, cell_data in zip(self.datapaths, self.data):
            data_path_split = datapath.name.split(".")[0].split("_")
            cell_id = data_path_split[3][4:]
            if len(data_path_split) == 5:
                cell_type = data_path_split[4]
            else:
                cell_type = "N/A"
            cell_types.append(cell_type)
            sample_rate = cell_data["spk_sample_rate"][0][0]
            spike_times = cell_data["spikes_times"].T[0] / sample_rate
            all_spike_times[cell_id] = nap.Ts(spike_times)

        spikes = nap.TsGroup(all_spike_times, metadata={"cell_type": cell_types})
        return spikes

    def load(self, key: Literal["xy", "dir", "speed"]):
        first_data = self.data[0]

        pos_sample_rate = first_data["pos_sample_rate"][0][0]
        beh_data = first_data[key]

        if key == "xy":
            pixels_per_m = first_data["pixels_per_m"][0][0].astype("float32")
            pixels_per_cm = pixels_per_m / 100
            beh_data /= pixels_per_cm

        timestamps = np.arange(0, len(beh_data)) / pos_sample_rate

        beh_frame = nap.TsdFrame(t=timestamps, d=beh_data)

        return beh_frame
