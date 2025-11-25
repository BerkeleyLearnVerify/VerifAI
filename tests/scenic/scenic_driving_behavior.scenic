param map = localPath('Town01.xodr')
param carla_map = 'Town01'
param verifaiTimeBound = 100

model scenic.domains.driving.model

foo = VerifaiRange(0,0.01, timeSeries=True)

behavior TestBehavior():
    while True:
        val1 = foo.getSample()
        val2 = foo.getSample()
        assert val1 == val2
        take SetThrottleAction(foo.getSample())

ego = new Car on road, with behavior TestBehavior()
new Car behind ego by VerifaiRange(1,4)

terminate after 5 seconds
