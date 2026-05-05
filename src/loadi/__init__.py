from importlib.metadata import entry_points

from .loaders import (
    DandiExperiment,
    KanterMoser2025Experiment,
    KrupicBurton2023Experiment,
    NagelhusMoser2023Experiment,
    VollanMoser2024Experiment,
    WillsMuessig2023Experiment,
)


def __getattr__(name):
    # Search for installed plugins in the 'loadi.experiments' group
    plugins = entry_points(group="loadi.experiments")

    for ep in plugins:
        # Check if the requested name matches the plugin name
        if ep.name == name:
            return ep.load()

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
