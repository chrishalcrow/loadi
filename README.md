Download the repo

``` bash
git clone https://github.com/chrishalcow/loadi
cd loadi
```

Then install into your environment:

``` bash
pip install .
```

or run directly with `uv` from the loadi directory:

``` bash
uv run python
```

Can be used to load data. E.g:

``` python
from loadi import NagelhusMoser2023Experiment
experiment = NagelhusMoser2023Experiment()
session = experiment.get_session('27207', 'CA3_12', 'object moved')
units = session.load_units()
```

Looping will loop through every session in the experiment (might take a while!)

``` python
for session in experiment:
    print(session.load_subject_position())
```
