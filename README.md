To run

``` bash
git clone https://github.com/chrishalcow/loadi
cd loadi
```

Can be used to load data. E.g:

``` python
from loadi.loaders.Q0FG1X8 import Q0FG1X8Experiment
mosers_experiment = Q0FG1X8Experiment()
session = mosers_experiment.get_session('25387', '16', 'object')
clusters = session.load_clusters()
```

Then edit and run your script, e.g.

``` bash
uv run scripts/make_analyzer_junji.py
```

This script outputs an analyzer, which you can look at using

``` bash
uv run sigui path_to_analyzer
```
