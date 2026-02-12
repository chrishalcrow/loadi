from loadi import NagelhusMoser2023Experiment, KanterMoser2025Experiment
from loadi.loaders.base import BaseExperiment
from pathlib import Path

experiment_dict = {
    NagelhusMoser2023Experiment.__name__[:-10]: NagelhusMoser2023Experiment,
    KanterMoser2025Experiment.__name__[:-10]: KanterMoser2025Experiment,
}

def load_experiment(experiment_name : str, containing_folder : str | Path) -> BaseExperiment:
    if experiment_name in experiment_dict:
        return experiment_dict[experiment_name](containing_folder)
    else:
        raise ModuleNotFoundError(f'No experiment called {experiment_name}.')