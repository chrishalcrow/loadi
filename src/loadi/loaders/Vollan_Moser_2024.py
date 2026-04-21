import json
import warnings
from importlib import resources
from pathlib import Path

import numpy as np
import pynapple as nap
from scipy.io import loadmat

from .base import BaseExperiment, BaseSession


class VollanMoser2024Experiment(BaseExperiment):
    """ "
    Data from
        Left-right-alternating theta sweeps in the entorhinal-hippocampal spatial map (v1)
        Data: https://search.kg.ebrains.eu/instances/4080b78d-edc5-4ae4-8144-7f6de79930ea

    Data in `containing_folder` expected to be in the form:

    containing_folder/
        sharing_v4/
            sleep/
                ...
            navigation/
                lt/
                    ...
                mmaze/
                    ...
                of/
                    ...
                of_novel/
                    ...
                ww/
                    ....

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
            .joinpath("Vollan_Moser_2024.json")
            .open("r") as f
        ):
            data_paths = json.load(f)

        self.data_paths = data_paths
        self.session_class = VollanMoser2024Session

    def get_session(self, subject_id, session_name):
        if isinstance(subject_id, int):
            subject_id = str(subject_id)

        if "of_novel" in session_name:
            session_type = "of_novel"
        else:
            session_type = session_name.split("_")[0]
        session_index = session_name.split("_")[-1]

        mouse_dict = self.data_paths.get(subject_id)
        if mouse_dict is None:
            raise ValueError(
                f"No subject_id {subject_id}. Possible subject_ids are {self.data_paths.keys()}."
            )
        else:
            if session_type == "sleep":
                data_path = (
                    self.containing_folder
                    / f"sharing_v4/sleep/{subject_id}_{session_index}.mat"
                )
            else:
                data_path = (
                    self.containing_folder
                    / f"sharing_v4/navigation/{session_type}/{subject_id}_{session_index}.mat"
                )
            if not data_path.is_file():
                raise FileNotFoundError(
                    f"Cannot find data path {data_path}, which contains rat {subject_id}"
                )

            return VollanMoser2024Session(subject_id, session_name, data_path=data_path)


class VollanMoser2024Session(BaseSession):
    def __init__(self, subject_id, session_name, known_data_types=None, data_path=None):
        self.subject_id = subject_id
        self.session_name = session_name
        self.session_type = session_name.split("_")[0]
        self.data_path = data_path

        self.cache = {}
        self.known_data_types = known_data_types

        data = loadmat(data_path)
        correct_key = [key for key in data.keys() if "__" not in key][0]
        self.session_data = data[correct_key][0][0]

    def load_units(self) -> nap.TsGroup:
        # correct for sleep
        if self.session_type == "sleep":
            spike_data = self.session_data["units"]["spikeTimes"]
            metadata = None

        else:
            # correct for others
            all_units = self.session_data["units"][0]
            mec_units = all_units["mec"][0]
            hc_units = all_units["hc"][0]

            num_mec_units = len(mec_units)
            num_hc_units = len(hc_units)

            brain_region_per_unit = ["mec"] * num_mec_units + ["hc"] * num_hc_units
            spike_data = np.concat([hc_units["spikeTimes"], mec_units["spikeTimes"]])

            metadata = {"brain_region": brain_region_per_unit}

        spikes_np = [np.transpose(spike_train[0])[0] for spike_train in spike_data]
        spikes = nap.TsGroup(
            spikes_np,
            metadata=metadata,
        )

        return spikes

    def load_position(self) -> nap.TsdFrame:
        if self.session_type == "sleep":
            warnings.warn("Sleep sessions have no position data.")
            return None

        data_to_load = ["x", "y", "z", "hd", "theta", "speed"]

        data = [
            np.transpose(self.session_data[data_type])[0] for data_type in data_to_load
        ]

        timestamps = np.transpose(self.session_data["t"])[0]

        position = nap.TsdFrame(
            timestamps, d=np.transpose(np.vstack(data)), columns=data_to_load
        )

        return position
