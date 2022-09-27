### Purpose

To best serve our fleet operators or "hikers" decide where to plug in vehicles optimally


#### Getting Started

Inspiration: https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker

In a terminal from the parent repo folder

## SQLite3 Prep
For better formatting and individual viewing of simulation run results first run this in terminal:
```
echo $HOME
```
now the directory returned is where you should place a file called:
```
touch {YOUR ECHO RESULTS ABOVE}/.sqliterc
```
and add the following lines for viewing ease:
```
.headers ON
.mode columns
```

Inspect results by executing in directory of test.db after the db has been built from a few runs
```
sqlite3 test.db
```

type cmd + D to exit the sqlite console


## Docker Build

First build the docker image
```
docker build --rm -t streamlit .
```

## Running Sims in Docker

If running an individual simulation for inspection
```
docker run -v $(pwd):/home/code -p 8080:8080 streamlit visualize_single_run.py --server.port 8080
```

If running the site SLA tool
```
docker run -v $(pwd):/home/code -p 8501:8501 streamlit visualize_multi_run.py
```






to execute from the command line a series of simulations use the following command
from the parent directory.
```
python3 -m src.utils.multi_run_cmd_line --n_repeats=1 --n_dcfc=1
python3 -m src.utils.multi_run_cmd_line  --n_dcfc=0  --n_repeats=1
```

click on the url in the terminal


#### How

We simulate:
- assets: vehicles, stations
- demand: walkins, reservations
- heuristics: if then logic on actions to take regarding where and when to charge vehicles

These three services talk to each other over a mock queue that contains python lists which act as routes.
These routes contain json messages that the other services pop msgs out of and serialize into objects

Although this repo uses a mockqueue, this queue is not event based so it is really like an api proxy
in that a servce does a get or post to the queue and the queue is an intermediary between services.
There isn't a subscribe or publish event based trigger. Ted mentioned we will be using http api calls
for Hertz to start so this should suffice for now.

##### Todo:
- fill in the methods on the heuristic 
- visualize results
- update documentation for flow diagrams on architecture
