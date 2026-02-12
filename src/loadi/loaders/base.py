import pynapple as nap
from typing import TypedDict

class PositionDict(TypedDict):
    Px: nap.Tsd
    Py: nap.Tsd

class BaseExperiment:

    def __init__(self, experiment_structure):
        self.data_paths = experiment_structure
        self.session_class = BaseSession
        self.containing_folder = None

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
    
    def get_session():
        pass
        
    def __iter__(self):
        # We delegate the iteration to our recursive helper
        return self._walk(self.data_paths, [])

    def _walk(self, current_node, path):
        if isinstance(current_node, list):
            yield self.get_session(*path)
        elif isinstance(current_node, dict):
            for key, value in current_node.items():
                yield from self._walk(value, path + [key])

class BaseSession():

    def load_units(self) -> nap.TsGroup:
        pass
