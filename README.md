### Purpose

To best serve our fleet operators or "hikers" decide where to plug in vehicles optimally


#### How

We simulate:
- assets: vehicles, stations
- demand: walkins, reservations
- heuristics: if then logic on actions to take regarding where and when to charge vehicles

These three services talk to each other over a mock queue that contains python lists which act as routes.
These routes contain json messages that the other services pop msgs out of and serialize into objects

##### Todo:
- fill in the methods on the heuristic 
- visualize results
- update documentation for flow diagrams on architecture
