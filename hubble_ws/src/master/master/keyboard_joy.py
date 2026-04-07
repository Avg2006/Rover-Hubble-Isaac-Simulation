import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
import pygame
import time
from std_msgs.msg import String, Int8
from rclpy.qos import QoSProfile, ReliabilityPolicy


class KeyboardJoy(Node):
    def __init__(self):
        super().__init__('keyboard_joy')

        self.qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
        
        self.pub = self.create_publisher(Joy, '/joy', self.qos)
        self.config_sub = self.create_subscription(String,'/config',self.config_cb,self.qos)
        self.mode_sub = self.create_subscription(Int8,'/mode',self.mode_cb,self.qos)
        self.timer = self.create_timer(0.05, self.loop)

        pygame.init()
        pygame.display.set_mode((200, 200))  # required
        pygame.display.set_caption("Keyboard Joy")

        self.axes = [0.0] * 8
        self.buttons = [0] * 12

        self.fb_axis = 1  
        self.front_key = pygame.K_w
        self.back_key = pygame.K_s
        self.lr_axis = 3
        self.left_key = pygame.K_a
        self.right_key = pygame.K_d

        self.steer_gear_1_key = pygame.K_u
        self.steer_gear_2_key = pygame.K_i
        self.steer_gear_3_key = pygame.K_o
        self.steer_gear_4_key = pygame.K_p

        self.drive_gear_1_key = pygame.K_j
        self.drive_gear_2_key = pygame.K_k
        self.drive_gear_3_key = pygame.K_l
        self.drive_gear_4_key = pygame.K_SEMICOLON

        self.mode_up_button = 5
        self.mode_up_key = pygame.K_e
        self.mode_down_button = 4
        self.mode_down_key = pygame.K_q

        self.change_steer_mode_key = pygame.K_LSHIFT
        self.change_steer_mode_button = 6

        self.rotinplace_key = pygame.K_r
        self.rotinplace_button = 2
        self.parrallel_button = 3

        self.drive_gear = 4
        self.steer_gear = 4

        self.in_rotinplace = False
        self.config = "ACKERMANN"
        self.in_rotinplace_pressed = False

        self.last_time = 0
        self.cooldown_period = 0.3

        self.mode = 0


    def config_cb(self, msg):
        self.config = msg.data

    def mode_cb(self, msg):
        self.mode = msg.data

    def loop(self):
        

        print("<==================================================================>")
        self.get_logger().info('Reading keyboard input...')
        print("\n\n\n")
        print("\t\t\t\t\t\tpress W/S to go Forward/Backward")
        print("\t\t\t\t\t\tpress A/D to go Left/Right")
        if self.config == "ROTINPLACE":
            self.in_rotinplace = True
            print("in Rot In Place config\t\t\t\tto get back: R")
        elif self.config == "ACKERMANN":
            self.in_rotinplace = False
            print(f"Current Steering Mode: {self.config}\t\tto change mode: Left Shift")
        else:
            self.in_rotinplace = False
            print(f"Current Steering Mode: {self.config}\t\t\tto change mode: Left Shift")
        print(f"Steer Gear: {self.steer_gear}\t\t\t\t\tto change steer gear: U/I/O/P")
        print(f"Drive Gear: {self.drive_gear}\t\t\t\t\tto change drive gear: J/K/L/;")
        print(f"Mode: {self.mode}\t\t\t\t\t\tto change drive mode: Q/E")
        print("\n\n\n")

        pygame.event.pump()
        keys = pygame.key.get_pressed()
        # Reset
        self.axes = [0.0] * 8
        self.buttons = [0] * 12

        #drive gears
        if keys[self.drive_gear_1_key]:
            self.drive_gear = 1
        elif keys[self.drive_gear_2_key]:
            self.drive_gear = 2
        elif keys[self.drive_gear_3_key]:
            self.drive_gear = 3
        elif keys[self.drive_gear_4_key]:
            self.drive_gear = 4

        #steer gears
        if keys[self.steer_gear_1_key]:
            self.steer_gear = 1
        elif keys[self.steer_gear_2_key]:
            self.steer_gear = 2
        elif keys[self.steer_gear_3_key]:
            self.steer_gear = 3
        elif keys[self.steer_gear_4_key]:
            self.steer_gear = 4

        # Forward/Backward
        if keys[self.front_key]:
            if self.drive_gear == 1:
                self.axes[self.fb_axis] = -0.25
            elif self.drive_gear == 2:
                self.axes[self.fb_axis] = -0.5
            elif self.drive_gear == 3:
                self.axes[self.fb_axis] = -0.75
            elif self.drive_gear == 4:
                self.axes[self.fb_axis] = -1.0
        if keys[self.back_key]:
            if self.drive_gear == 1:
                self.axes[self.fb_axis] = 0.25
            elif self.drive_gear == 2:
                self.axes[self.fb_axis] = 0.5
            elif self.drive_gear == 3:
                self.axes[self.fb_axis] = 0.75
            elif self.drive_gear == 4:
                self.axes[self.fb_axis] = 1.0

        # Left/Right
        if keys[self.left_key]:
            if self.steer_gear == 1:
                self.axes[self.lr_axis] = 0.25
            elif self.steer_gear == 2:
                self.axes[self.lr_axis] = 0.5
            elif self.steer_gear == 3:
                self.axes[self.lr_axis] = 0.75
            elif self.steer_gear == 4:
                self.axes[self.lr_axis] = 1.0
        if keys[self.right_key]:
            if self.steer_gear == 1:
                self.axes[self.lr_axis] = -0.25
            elif self.steer_gear == 2:
                self.axes[self.lr_axis] = -0.5
            elif self.steer_gear == 3:
                self.axes[self.lr_axis] = -0.75
            elif self.steer_gear == 4:
                self.axes[self.lr_axis] = -1.0

        # Mode Up/Down
        if keys[self.mode_up_key]:
            self.buttons[self.mode_up_button] = 1
        if keys[self.mode_down_key]:
            self.buttons[self.mode_down_button] = 1 

        #change steer mode
        if keys[self.change_steer_mode_key]:
            self.buttons[self.change_steer_mode_button] = 1

        # rotinplace
        if keys[self.rotinplace_key] and (time.time() - self.last_time) > self.cooldown_period:
            if not self.in_rotinplace:
                self.in_rotinplace_pressed = True
                self.last_time = time.time()
            elif self.in_rotinplace and (time.time() - self.last_time) > self.cooldown_period:
                self.in_rotinplace_pressed = True
                self.last_time = time.time()
        
        if not self.in_rotinplace and self.in_rotinplace_pressed: 
            self.buttons[self.rotinplace_button] = 1 
            self.in_rotinplace_pressed = False
        elif self.in_rotinplace and self.in_rotinplace_pressed:
            self.buttons[self.parrallel_button] = 1
            self.in_rotinplace_pressed = False


        print("<==================================================================>")

        joy = Joy()
        joy.axes = self.axes
        joy.buttons = self.buttons
        self.pub.publish(joy)


def main():
    rclpy.init()
    node = KeyboardJoy()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
