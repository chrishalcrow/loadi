To run

``` bash
git clone https://github.com/chrishalcow/loadi
cd loadi
```

Can be used to load data. E.g:

``` python
from loadi import NagelhusMoser2023Experiment
experiment = NagelhusMoser2023Experiment()
session = experiment.get_session('25387', '16', 'object')
units = session.load_units()
```

Looping works too!

``` python
for session in experiment:
    print(session.load_subject_position())
```