import json
from importlib import resources
from pathlib import Path

import h5py
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


def _decode_matlab_string(dataset: h5py.Dataset) -> str:
    values = np.asarray(dataset[()]).ravel()
    return "".join(chr(int(value)) for value in values if value).strip()


def _get_table_column(
    file: h5py.File,
    column_index: int,
) -> h5py.Dataset:
    mcos = file["#subsystem#/MCOS"]
    columns = file[mcos[0, 2]]
    return file[columns[column_index, 0]]


def _read_string_column(
    file: h5py.File,
    column_index: int,
) -> list[str]:
    column = _get_table_column(file, column_index)

    return [_decode_matlab_string(file[reference]) for reference in column[()].ravel()]


def load_spikes(
    path: Path,
    mouseday_id: str,
    session_index: int,
) -> list[np.ndarray]:
    with h5py.File(path, "r") as file:
        cell_ids = _read_string_column(file, column_index=0)
        spike_column = _get_table_column(file, column_index=23)
        spike_references = spike_column[()].ravel()

        cell_indices = [
            index
            for index, cell_id in enumerate(cell_ids)
            if cell_id.split(maxsplit=1)[0] == mouseday_id
        ]

        offset = session_index * len(cell_ids)

        return [
            np.asarray(file[spike_references[offset + cell_index]][()]).ravel()
            for cell_index in cell_indices
        ]


def load_spatial_data(
    path: Path,
    mouseday_id: str,
    session_index: int,
    column_index: int,
) -> np.ndarray:
    with h5py.File(path, "r") as file:
        mouseday_ids = _read_string_column(file, column_index=0)
        mouseday_index = mouseday_ids.index(mouseday_id)

        value_column = _get_table_column(file, column_index)
        value_references = value_column[()].ravel()

        value_index = session_index * len(mouseday_ids) + mouseday_index
        values = np.asarray(file[value_references[value_index]][()])

    if values.ndim == 2 and values.shape[0] == 2:
        values = values.T

    return values


class WillsMuessig2023Session(BaseSession):
    position_sampling_rate = 50

    def __init__(
        self,
        mouse: str,
        date: str,
        session: str,
        known_data_types: list[str] | None = None,
        containing_folder: Path = Path(),
    ) -> None:
        self.mouse = mouse
        self.date = date
        self.session = session
        self.cache = {}
        self.known_data_types = known_data_types or []

        self._position_path = containing_folder / "Position_data.mat"
        self._results_path = containing_folder / "Results.mat"

    def _repr_html_(self) -> str:
        header = (
            f"<b>Mouse</b> {self.mouse}, "
            f"<b>Date</b> {self.date}, "
            f"<b>Session</b> {self.session}<br />"
        )
        return header + str(self.known_data_types)

    @property
    def _mouseday_id(self) -> str:
        return f"{self.mouse}_{self.date}"

    @property
    def _session_index(self) -> int:
        return int(self.session.rsplit("_", maxsplit=1)[-1])

    def load_units(self) -> nap.TsGroup:
        spike_trains = load_spikes(
            path=self._results_path,
            mouseday_id=self._mouseday_id,
            session_index=self._session_index,
        )
        return nap.TsGroup(spike_trains)

    def _load_spatial_frame(self, column_index: int) -> nap.TsdFrame:
        values = load_spatial_data(
            path=self._position_path,
            mouseday_id=self._mouseday_id,
            session_index=self._session_index,
            column_index=column_index,
        )
        times = np.arange(len(values)) / self.position_sampling_rate

        return nap.TsdFrame(
            t=times,
            d=values,
            columns=["x", "y"],
        )

    def load_position(self) -> nap.TsdFrame:
        return self._load_spatial_frame(column_index=2)

    def load_direction(self) -> nap.TsdFrame:
        return self._load_spatial_frame(column_index=3)
