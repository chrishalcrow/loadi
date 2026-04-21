import inspect
import uuid
from importlib.metadata import entry_points
from pathlib import Path


class BaseExperiment:
    def __init__(self, experiment_structure):
        self.data_paths = experiment_structure
        self.session_class = BaseSession
        self.containing_folder = None

    def __repr__(self):
        return self._generate_terminal_tree(self.data_paths)

    def _repr_html_(self):
        # Create a unique prefix for this specific output to avoid CSS collisions
        uid = str(uuid.uuid4())[:8]

        # We define the CSS once at the top of the representation
        style = f"""
        <style>
            .nested-{uid} {{ font-family: monospace; }}
            .nested-{uid} .node {{ margin-bottom: 2px; position: relative; }}
            /* Hide the actual checkbox */
            .nested-{uid} .toggle-input {{ display: none; }}
            /* Style the arrow (the label) */
            .nested-{uid} .toggle-label {{
                cursor: pointer;
                user-select: none;
                display: inline-block;
                width: 15px;
                color: #888;
                font-size: 12px;
                transition: transform 0.1s;
            }}
            /* The Key Text: Independent of the toggle */
            .nested-{uid} .key-text {{
                font-weight: bold;
                cursor: text;
                user-select: text;
            }}
            /* The hidden content */
            .nested-{uid} .content {{
                display: none;
                margin-left: 18px;
                border-left: 1px solid #ddd;
                padding-left: 10px;
            }}
            /* Show content and rotate arrow when checkbox is checked */
            .nested-{uid} .toggle-input:checked ~ .content {{ display: block; }}
            .nested-{uid} .toggle-input:checked ~ .toggle-label {{  color: #333; }}
        </style>
        """
        return f'<div class="nested-{uid}">{style}{self._generate_html(self.data_paths, uid)}</div>'

    def _generate_html(self, data, uid):
        html = "<div>"
        for key, value in data.items():
            if isinstance(value, dict):
                node_id = str(uuid.uuid4())[:8]
                html += f'''
                <div class="node">
                    <input type="checkbox" id="{node_id}" class="toggle-input">
                    <span class="key-text">{key}</span>
                    <label for="{node_id}" class="toggle-label">▶</label>
                    <div class="content">{self._generate_html(value, uid)}</div>
                    
                </div>
                '''
            else:
                # Standard leaf node (indented to match the arrow spacing)
                html += f"""
                <div style="margin-left: 18px; margin-bottom: 2px;">
                    <span class="key-text">{key}</span>
                </div>
                """
        html += "</div>"
        return html

    def _generate_terminal_tree(self, data, indent=""):
        lines = []
        items = list(data.items())

        for i, (key, value) in enumerate(items):
            # Determine if this is the last item in the current nesting level
            is_last = i == len(items) - 1
            connector = "└── " if is_last else "├── "

            if isinstance(value, dict):
                # Header for a nested section
                lines.append(f"{indent}{connector}\033[1m{key}\033[0m")

                # Create the prefix for the next level
                next_indent = indent + ("    " if is_last else "│   ")
                lines.append(self._generate_terminal_tree(value, next_indent))
            else:
                # Leaf node
                lines.append(f"{indent}{connector}\033[1m{key}\033[0m")

        return "\n".join(lines)

    def get_session():
        pass

    def __iter__(self):
        # We delegate the iteration to our recursive helper
        return self._walk(self.data_paths, [])

    def _walk(self, current_node, path):
        if isinstance(current_node, list) or isinstance(current_node, str):
            yield self.get_session(*path)
        elif isinstance(current_node, dict):
            for key, value in current_node.items():
                yield from self._walk(value, path + [key])


class BaseSession:
    def __repr__(self):
        sig = inspect.signature(self.__class__.__init__)
        params = [p for p in sig.parameters if p != "self"]

        rows = ""
        for p in params:
            val = getattr(self, p, "None")
            if isinstance(val, Path):
                val = str(val)
            rows += f"{p: <15} {repr(val)}\n"

        return rows

    def _repr_html_(self):
        sig = inspect.signature(self.__class__.__init__)
        params = [p for p in sig.parameters if p != "self"]

        # Build a clean, courier-style list
        rows = []
        for p in params:
            val = getattr(self, p, "None")
            if isinstance(val, Path):
                val = str(val)
            rows.append(f"<strong>{p:.<15}</strong> {repr(val)}")

        return f"""
        <div style="font-family: 'Courier New', Courier, monospace;">
            {"<br>".join(rows)}
        </div>
        """
