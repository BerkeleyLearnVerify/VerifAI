# Behavior Prediction Scenarios



## Intersection
01. Ego vehicle goes straight at 4-way intersection and must suddenly stop to avoid collision when adversary vehicle from oncoming parallel lane makes a left turn.
02. Ego vehicle makes a left turn at 4-way intersection and must suddenly stop to avoid collision when adversary vehicle from oncoming parallel lane goes straight.
03. Ego vehicle either goes straight or makes a left turn at 4-way intersection and must suddenly stop to avoid collision when adversary vehicle from perpendicular lane continues straight.
04. Ego vehicle either goes straight or makes a left turn at 4-way intersection and must suddenly stop to avoid collision when adversary vehicle from perpendicular lane makes a left turn.
05. Ego vehicle waits for an adversary vehicle to pass before performing a lane change to bypass a stationary vehicle waiting to make a left turn at a 4-way intersection.
06. Ego vehicle makes a left turn at 3-way intersection and must suddenly stop to avoid collision when adversary vehicle from perpendicular lane continues straight.

## Passing
01. Ego vehicle performs a lane change to bypass a slow adversary vehicle before returning to its original lane.
02. Advesary vehicle performs a lange change to bypass the ego vehicle before returning to its original lane.
03. Ego vehicle performs a lane change to bypass a slow adversary vehicle but cannot return to its original lane because the adversary accelerates. Ego vehicle must then slow down to avoid collision with leading vehicle in new lane.
04. Ego vehicle performs multiple lane changes to bypass two slow adversary vehicles. (TIP)
05. Ego vehicle performs multiple lane changes to bypass three slow adversary vehicles. (TIP)

## Roundabout
01. 

### NOTES
* TIP indicates Testing In-Progress.
* Run `python __main__.py --type {intersection/passing/roundabout} --number {01/02/...}` to run scenario.
