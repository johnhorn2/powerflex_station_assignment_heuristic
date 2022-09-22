### Purpose

To best serve our fleet operators or "hikers" decide where to plug in vehicles optimally


#### Getting Started

Inspiration: https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker

In a terminal from the parent repo folder
```
docker build --rm -t streamlit .
docker run -v $(pwd):/home/code -p 8501:8501 streamlit 
```

to execute from the command line a series of simulations:
```
python3 -m src.utils.multi_run
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
