"""
This controller gives to its node the following behavior:
Listen the keyboard. According to the pressed key, send a
message through an emitter or handle the position of Robot1.
"""

from controller import Supervisor


class Driver (Supervisor):
    timeStep = 128
    x = 0.1
    z = 0.3
    translation = [x, 0.0, z]

    def initialization(self):
        self.emitter = self.getEmitter('emitter')
        robot = self.getFromDef('ROBOT1')
        self.translationField = robot.getField('translation')
        self.keyboard.enable(self.timeStep)
        self.keyboard = self.getKeyboard()

    def run(self):
        self.displayHelp()
        previous_message = ''

        # Main loop.
        while True:
            # Deal with the pressed keyboard key.
            k = self.keyboard.getKey()
            message = ''
            if k == ord('A'):
                message = 'avoid obstacles'
            elif k == ord('F'):
                message = 'move forward'
            elif k == ord('S'):
                message = 'stop'
            elif k == ord('T'):
                message = 'turn'
            elif k == ord('I'):
                self.displayHelp()
            elif k == ord('G'):
                translationValues = self.translationField.getSFVec3f()
                print('ROBOT1 is located at (' + str(translationValues[0]) + ',' + str(translationValues[2]) + ')')
            elif k == ord('R'):
                print('Teleport ROBOT1 at (' + str(self.x) + ',' + str(self.z) + ')')
                self.translationField.setSFVec3f(self.translation)

            # Send a new message through the emitter device.
            if message != '' and message != previous_message:
                previous_message = message
                print('Please, ' + message)
                self.emitter.send(message.encode('utf-8'))

            # Perform a simulation step, quit the loop when
            # Webots is about to quit.
            if self.step(self.timeStep) == -1:
                break

    def displayHelp(self):
        print(
            'Commands:\n'
            ' I for displaying the commands\n'
            ' A for avoid obstacles\n'
            ' F for move forward\n'
            ' S for stop\n'
            ' T for turn\n'
            ' R for positioning ROBOT1 at (0.1,0.3)\n'
            ' G for knowing the (x,z) position of ROBOT1'
        )


controller = Driver()
controller.initialization()
controller.run()
