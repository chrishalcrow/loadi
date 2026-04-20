import json
from importlib import resources
from pathlib import Path

import numpy as np
import pynapple as nap
from pymatreader import read_mat

from .base import BaseExperiment, BaseSession


class WillsMuessig2023Experiment(BaseExperiment):
    """ "
    Data from
        Environment geometry alters subiculum boundary vector cell receptive fields in adulthood and early development
        Laurenz Muessig, Fabio Ribeiro Rodrigues, Tale L. Bjerknes, Benjamin W. Towse, Caswell Barry, Neil Burgess, Edvard I. Moser, May-Britt Moser, Francesca Cacucci & Thomas J. Wills
        Paper: https://www.nature.com/articles/s41467-024-45098-1 (https://doi.org/10.1038/s41467-024-45098-1)
        Data: https://rdr.ucl.ac.uk/articles/dataset/Subiculum_neuron_data_from_adult_and_developing_rats/24864732 (https://doi.org/10.5522/04/24864732)


    Data expected to be in the form:

    containing_folder/
        Position_data.mat
        Results.mat
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
            .joinpath("Wills_Muessing_2023.json")
            .open("r") as f
        ):
            data_paths = json.load(f)

        self.data_paths = data_paths
        self.session_class = WillsMuessig2023Session

    def get_session(self, subject_id, session_id, session_type):
        if isinstance(subject_id, int):
            subject_id = str(subject_id)

        if isinstance(session_id, int):
            session_id = str(session_id)

        mouse_dict = self.data_paths.get(subject_id)
        if mouse_dict is None:
            raise ValueError(
                f"No subject_id {subject_id}. Possible subjects are {self.data_paths.keys()}."
            )
        else:
            day_dict = mouse_dict.get(session_id)
            if day_dict is None:
                raise ValueError(
                    f"No session_id {session_id}. Possible session_ids are {mouse_dict.keys()}."
                )
            else:
                session_dict = day_dict.get(session_type)
                if session_dict is None:
                    raise ValueError(
                        f"No session_type called {session_type}. Possible sessions are {day_dict.keys()}."
                    )
                else:
                    return WillsMuessig2023Session(
                        subject_id,
                        session_id,
                        session_type,
                        known_data_types=session_dict,
                        containing_folder=self.containing_folder,
                    )


class WillsMuessig2023Session(BaseSession):
    def __init__(
        self,
        mouse,
        date,
        session,
        known_data_types: list = [],
        containing_folder: Path = Path(""),
    ):
        self.mouse = mouse
        self.date = date
        self.session = session

        self.cache = {}
        self.known_data_types = known_data_types

        self.position_data = read_mat(containing_folder / "Position_data.mat")
        self.spike_data = read_mat(containing_folder / "Results.mat")

    def _repr_html_(self):
        header_text = f"<b>Mouse</b> {self.mouse}, <b>Date</b> {self.date}, <b>Session</b> {self.session}<br />"
        streams_text = f"{self.known_data_types}"

        return header_text + streams_text

    def load_units(self) -> nap.TsGroup:
        mouseday_id = f"{self.mouse}_{self.date}"
        session_index = int(self.session.split("_")[-1])

        spike_mousedays = self.spike_data["#subsystem#"]["MCOS"][2]
        all_spike_trains = spike_mousedays[23]

        mouseday_id_per_cell = [cell_id.split(" ")[0] for cell_id in spike_mousedays[0]]

        cell_ids_per_mouseday = np.array(mouseday_id_per_cell) == mouseday_id

        unit_spike_trains = []
        for res_index, res in enumerate(cell_ids_per_mouseday):
            if res:
                unit_spike_trains.append(
                    all_spike_trains[2779 * session_index + res_index]
                )

        spikes = nap.TsGroup(unit_spike_trains)
        return spikes

    def load_position(self) -> nap.TsdFrame:
        position_sampling_rate = 50
        mouseday_id = f"{self.mouse}_{self.date}"
        session_index = int(self.session.split("_")[-1])

        actual_data = self.position_data["#subsystem#"]["MCOS"][2]

        mouseday_index = actual_data[0].index(mouseday_id)
        position = actual_data[2][session_index * 367 + mouseday_index]

        times = np.arange(
            0, len(position) / position_sampling_rate, 1 / position_sampling_rate
        )
        position = nap.TsdFrame(t=times, d=position, columns=["x", "y"])

        return position

    def load_direction(self) -> nap.TsdFrame:
        position_sampling_rate = 50
        mouseday_id = f"{self.mouse}_{self.date}"
        session_index = int(self.session.split("_")[-1])

        actual_data = self.position_data["#subsystem#"]["MCOS"][2]

        mouseday_index = actual_data[0].index(mouseday_id)
        direction = actual_data[3][session_index * 367 + mouseday_index]

        times = np.arange(
            0, len(direction) / position_sampling_rate, 1 / position_sampling_rate
        )
        direction = nap.TsdFrame(t=times, d=direction, columns=["x", "y"])

        return direction
