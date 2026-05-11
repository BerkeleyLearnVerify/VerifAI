param map = localPath('Town01.xodr')
model scenic.simulators.newtonian.driving_model

foo = TimeSeries(VerifaiRange(0,0.01))

behavior TestBehavior():
    lastVal = None
    while True:
        newVal = foo.getSample()
        assert newVal != lastVal, (newVal, lastVal)
        lastVal = newVal
        take SetThrottleAction(newVal)

ego = new Car on road, with behavior TestBehavior()
new Car behind ego by VerifaiRange(1,4)

terminate after 5 seconds
