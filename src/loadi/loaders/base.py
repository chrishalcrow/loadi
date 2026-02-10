import pynapple as nap
from typing import TypedDict

class PositionDict(TypedDict):
    Px: nap.Tsd
    Py: nap.Tsd

class BaseExperiment:

    def __init__(self, experiment_structure):
        self.data_paths = experiment_structure

    def _repr_html_(self):
        return self._generate_html(self.data_paths)

    def _generate_html(self, data):
        html = "<div style='font-family: monospace; margin-left: 20px;'>"
        
        for key, value in data.items():
            if isinstance(value, dict):
                # If the value is a dict, we nest another details tag
                html += f"""
                <details style="margin-bottom: 5px;">
                    <summary style="cursor: pointer; font-weight: bold;">
                        {key}
                    </summary>
                    {self._generate_html(value)}
                </details>
                """
            else:
                # If it's a leaf node, just show the key-value pair
                html += f"<p><strong>{key}</strong>, loadable data: {value}</p>"
        
        html += "</div>"
        return html

class BaseSession():

    def load_clusters(self) -> nap.TsGroup:
        pass
