#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
import sys
import ftrobopy  # Import the ftrobopy module
import time
from TouchStyle import *


class FtcGuiApplication(TouchApplication):
    def __init__(self, args):
        TouchApplication.__init__(self, args)

        # create the empty main window
        w = TouchWindow("Pneumatic Grabber")

        txt_ip = os.environ.get('TXT_IP')  # try to read TXT_IP environment variable
        if txt_ip is None: txt_ip = "localhost"  # use localhost otherwise
        try:
            self.txt = ftrobopy.ftrobopy(txt_ip, 65000)  # try to connect to IO server
        except:
            self.txt = None

        vbox = QVBoxLayout()

        if not self.txt:
            # display error of TXT could no be connected
            # error messages is centered and may span
            # over several lines
            err_msg = QLabel("Error connecting IO server")  # create the error message label
            err_msg.setWordWrap(True)  # allow it to wrap over several lines
            err_msg.setAlignment(Qt.AlignCenter)  # center it horizontally
            vbox.addWidget(err_msg)  # attach it to the main output area
        else:
            # initialization went fine. So the main gui
            # is being drawn
            self.grab_button = QPushButton("Grab")  # create a button labeled "Toggle O1"
            self.grab_button.clicked.connect(self.on_grab_button_clicked)  # connect button to event handler
            # self.grab_button.setEnabled(False)
            vbox.addWidget(self.grab_button)  # attach it to the main output area

            # configure all TXT outputs to normal mode
            output_config = [self.txt.C_OUTPUT, self.txt.C_OUTPUT, self.txt.C_OUTPUT, self.txt.C_OUTPUT]
            input_config = [(self.txt.C_SWITCH, self.txt.C_DIGITAL),
                            (self.txt.C_SWITCH, self.txt.C_DIGITAL),
                            (self.txt.C_SWITCH, self.txt.C_DIGITAL),
                            (self.txt.C_SWITCH, self.txt.C_DIGITAL),
                            (self.txt.C_SWITCH, self.txt.C_DIGITAL),
                            (self.txt.C_SWITCH, self.txt.C_DIGITAL),
                            (self.txt.C_SWITCH, self.txt.C_DIGITAL),
                            (self.txt.C_SWITCH, self.txt.C_DIGITAL)]
            self.txt.setConfig(output_config, input_config)
            self.txt.updateConfig()
            self.motor_x = self.txt.motor(1)
            self.input_x = self.txt.input(1)
            self.pos_x = 0
            self.motor_z = self.txt.motor(2)
            self.input_z = self.txt.input(2)
            self.pos_z = 0

            self.valve_open = self.txt.output(7)
            self.valve_closed = self.txt.output(5)

            self.init_timer = QTimer(self)
            self.init_timer.timeout.connect(self.on_init_timer)
            self.init_timer.setSingleShot(True)
            self.init_timer.start(100)

        w.centralWidget.setLayout(vbox)
        w.show()
        self.exec_()

    # an event handler for our button (called a "slot" in qt)
    # it will be called whenever the user clicks the button
    def on_grab_button_clicked(self):
        for x in range(10):
            self.move_to_pos(0, 1175)
            self.toggle_grabber(True)
            self.move_to_pos(0, 1000)
            self.move_to_pos(1000, 100, 280, 512)
            self.move_to_pos(1000, 300)
            self.toggle_grabber(False)
            self.move_to_pos(1000, 100)

    def move_to_pos_x(self, position):
        self.move_to_pos(position, self.pos_z)

    def move_to_pos_z(self, position):
        self.move_to_pos(self.pos_x, position)

    def move_to_pos(self, target_pos_x, target_pos_z, speed_x=512, speed_z=512):
        distance_x = target_pos_x - self.pos_x
        distance_z = target_pos_z - self.pos_z
        # toggle the speed if going back
        if distance_x < 0:
            distance_x = -distance_x
            speed_x = -speed_x
        if distance_z < 0:
            distance_z = -distance_z
            speed_z = -speed_z
        if distance_x != 0:
            self.motor_x.setDistance(distance_x)
            self.motor_x.setSpeed(-speed_x)
        if distance_z != 0:
            self.motor_z.setDistance(distance_z)
            self.motor_z.setSpeed(-speed_z)

        motor_x_done = False
        motor_z_done = False
        while True:
            if not motor_x_done:
                # reset the position if it hits the input.
                input_hit = False
                if self.pos_x != 0 and self.input_x.state():
                    print("Reinitialized motor x")
                    input_hit = True
                    target_pos_x = 0
                if self.motor_x.finished() or input_hit:
                    self.motor_x.stop()
                    motor_x_done = True
            if not motor_z_done:
                # reset the position if it hits the input.
                input_hit = False
                if self.pos_z != 0 and self.input_z.state():
                    print("Reinitialized motor z")
                    input_hit = True
                    target_pos_z = 0
                if self.motor_z.finished() or input_hit:
                    self.motor_z.stop()
                    motor_z_done = True

            if motor_x_done and motor_z_done:
                break

        self.pos_x = target_pos_x
        self.pos_z = target_pos_z
        print("Moved to (x,z): (" + str(self.pos_x) + "," + str(self.pos_z) + ")")

    def on_init_timer(self):
        self.grab_button.setEnabled(False)
        self.toggle_grabber(False)

        self.motor_x.setSpeed(512)
        self.motor_z.setSpeed(512)
        x_done = False
        z_done = False

        while True:
            if not x_done and self.input_x.state():
                self.motor_x.stop()
                self.pos_x = 0
                print("Motor x initialized.")
                x_done = True

            if not z_done and self.input_z.state():
                self.motor_z.stop()
                self.pos_z = 0
                print("Motor z initialized.")
                z_done = True

            if x_done and z_done:
                break

        print("Model initialized.")
        self.grab_button.setEnabled(True)

    def toggle_grabber(self, grab):
        if grab:
            print("Closing grabber")
            valve_on = self.valve_closed
            valve_off = self.valve_open
        else:
            print("Opening grabber")
            valve_on = self.valve_open
            valve_off = self.valve_closed

        valve_on.setLevel(512)
        valve_off.setLevel(0)
        time.sleep(1.0)


if __name__ == "__main__":
    FtcGuiApplication(sys.argv)
