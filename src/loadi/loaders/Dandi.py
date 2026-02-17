import pynapple as nap
from .base import BaseSession, BaseExperiment
from dandi.dandiapi import DandiAPIClient
import h5py
from pynwb import NWBHDF5IO
import fsspec
from pathlib import Path
from importlib import resources
import json

import requests
def _load_nwb_files_in_dandiset(dandiset_id, version):

    url = f"https://api.dandiarchive.org/api/dandisets/{dandiset_id}/versions/{version}/assets/?page_size=100&glob=*.nwb"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch NWB files for dandiset {dandiset_id}: {response.status_code} {response.reason}"
        )
    data = response.json()
    nwb_files = []
    for asset in data["results"]:
        nwb_files.append(
            {
                "path": asset["path"],
                "size": asset["size"],
                "asset_id": asset["asset_id"],
            }
        )
    return nwb_files

class DandiExperiment(BaseExperiment):

    def __init__(
        self, 
        dandi_id = None
    ):
        
        self.dandi_id = dandi_id

        with resources.files('loadi.resources.dandi').joinpath(f'{dandi_id}.json').open('r') as f:
            self.data_paths = json.load(f)

        if False:
            nwb_files = _load_nwb_files_in_dandiset(dandi_id, 'draft')
            data_dict = {}
            for nwb_file in nwb_files:
                subject, session = nwb_file['path'].split('/')
                
                if data_dict.get(subject) is None:
                    data_dict[subject] = {}

                data_dict[subject][session] = ['units']

            self.data_paths = data_dict

    def get_session(self, subject_id, session_id):

        mouse_dict = self.data_paths.get(subject_id)
        if mouse_dict is None:
             raise ValueError(f"No subject called {subject_id}. Possible subjects are {self.data_paths.keys()}.")
        else:
             file_list = mouse_dict.get(session_id)
             if file_list is None:
                 raise ValueError(f"No session_id called {session_id}. Possible session_ids are {mouse_dict.keys()}.")
             else:
                 target_path = Path(subject_id) / session_id
                 return DandiSession(self.dandi_id, str(target_path))

class DandiSession(BaseSession):
        
    def __init__(self, dandiset_id, target_path):
        client = DandiAPIClient()
        dandiset = client.get_dandiset(dandiset_id, "draft")
        asset = dandiset.get_asset_by_path(target_path)
        s3_url = asset.get_content_url()
        fs = fsspec.filesystem("http")
        file = h5py.File(fs.open(s3_url, "rb"))
        io = NWBHDF5IO(file=file, load_namespaces=True)
        self.nwb = nap.NWBFile(io.read())

    def load_units(self) -> nap.TsGroup:
        return self.nwb['units']

