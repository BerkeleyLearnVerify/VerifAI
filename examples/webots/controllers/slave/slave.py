"""
This controller gives to its robot the following behavior:
According to the messages it receives, the robot change its
behavior.
"""

from controller import Robot


class Enumerate(object):
    def __init__(self, names):
        for number, name in enumerate(names.split()):
            setattr(self, name, number)


class Slave (Robot):

    Mode = Enumerate('STOP MOVE_FORWARD AVOIDOBSTACLES TURN')
    timeStep = 32
    maxSpeed = 10.0
    mode = Mode.AVOIDOBSTACLES
    motors = []
    distanceSensors = []

    def boundSpeed(self, speed):
        return max(-self.maxSpeed, min(self.maxSpeed, speed))

    def initialization(self):
        self.mode = self.Mode.AVOIDOBSTACLES
        self.camera = self.getCamera('camera')
        self.camera.enable(4 * self.timeStep)
        self.receiver = self.getReceiver('receiver')
        self.receiver.enable(self.timeStep)
        self.motors.append(self.getMotor("left wheel motor"))
        self.motors.append(self.getMotor("right wheel motor"))
        self.motors[0].setPosition(float("inf"))
        self.motors[1].setPosition(float("inf"))
        self.motors[0].setVelocity(0.0)
        self.motors[1].setVelocity(0.0)
        for dsnumber in range(0, 2):
            self.distanceSensors.append(self.getDistanceSensor('ds' + str(dsnumber)))
            self.distanceSensors[-1].enable(self.timeStep)

    def run(self):
        while True:
            # Read the supervisor order.
            if self.receiver.getQueueLength() > 0:
                message = self.receiver.getData().decode('utf-8')
                self.receiver.nextPacket()
                print('I should ' + message + '!')
                if message == 'avoid obstacles':
                    self.mode = self.Mode.AVOIDOBSTACLES
                elif message == 'move forward':
                    self.mode = self.Mode.MOVE_FORWARD
                elif message == 'stop':
                    self.mode = self.Mode.STOP
                elif message == 'turn':
                    self.mode = self.Mode.TURN
            delta = self.distanceSensors[0].getValue() - self.distanceSensors[1].getValue()
            speeds = [0.0, 0.0]

            # Send actuators commands according to the mode.
            if self.mode == self.Mode.AVOIDOBSTACLES:
                speeds[0] = self.boundSpeed(self.maxSpeed / 2 + 0.1 * delta)
                speeds[1] = self.boundSpeed(self.maxSpeed / 2 - 0.1 * delta)
            elif self.mode == self.Mode.MOVE_FORWARD:
                speeds[0] = self.maxSpeed
                speeds[1] = self.maxSpeed
            elif self.mode == self.Mode.TURN:
                speeds[0] = self.maxSpeed / 2
                speeds[1] = -self.maxSpeed / 2
            self.motors[0].setVelocity(speeds[0])
            self.motors[1].setVelocity(speeds[1])

            # Perform a simulation step, quit the loop when
            # Webots is about to quit.
            if self.step(self.timeStep) == -1:
                break


controller = Slave()
controller.initialization()
controller.run()
