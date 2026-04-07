import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from rclpy.qos import QoSProfile, ReliabilityPolicy
from geometry_msgs.msg import Twist
from std_msgs.msg import Int32MultiArray, Bool, Int8, String, Float32MultiArray
import time
import queue
from std_srvs.srv import Trigger
from rcl_interfaces.msg import SetParametersResult


class Drive(Node):
    def __init__(self):
        super().__init__("LLC")

        #Rover State variables
        self.state = False                         # Decides which mode rover is in: True -> Autonomous & False -> Manual
        self.rover_direction = "ArmForward"
        self.mode = 0

        #joystick maping
        self.mode_up_button = 5                     # Buttons that cycle through the modes 0 -> 1 -> 2 -> 3 -> 4(up)
        self.mode_down_button = 4                   # Buttons that cycle through the modes 4 -> 3 -> 2 -> 1 -> 0(down)
        self.fb_axis = 1                            # To move rover forward-back
        self.lr_axis = 3                            # To move rover left-right
        self.autonomous_btn = 0                     # Autonomous button switches between manual and autonomous
        self.change_dir_button = 7

        
        #normal steer_drive
        self.drive_ctrl = [0, 0]                    # Drive fb and lr axes

        #autonomous variables
        self.autonomous_vel = 0                     # Velocity of wheels in autonomous mode
        self.autonomous_omega = 0                   # Omega of wheels in autonomous mode

        #code variable
        self.debug = False                          # Debug variable to print debug messages
        self.pwm_msg = Int32MultiArray()            # PWM message to be published
        self.pwm_msg.data = [0] * 4                 # PWM values for 8 motors
        self.init_dir = [1, 1, 1, 1]                # Initial direction of the motors [FL,FR,RR,RL]
        self.last_time = 0
        self.cooldown_period = 0.3                  # Cooldown period for toggling between button
        self.drive_multipliers = [35,80,120,160,205,255]# Different speed modes for the rover
        self.qsize = 3                              # Size of the queue for smoothing
        self.vel_prev = queue.Queue(self.qsize)     # Queue to store previous velocities for smoothing
        self.omega_prev = queue.Queue(self.qsize)   # Queue to store previous omegas for smoothing
        self.joy_callback_last_time = time.time()   # variable for watchdog
        

        #ROS2 specific variables
        self.qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)

        #subscribers
        self.joy_sub = self.create_subscription(Joy, "/joy", self.joy_callback,self.qos)
        self.rpm_sub = self.create_subscription(Twist, "/motion", self.autonomous_callback,self.qos)

        #publishers
        self.pwm_pub = self.create_publisher(Int32MultiArray, "/motor_pwm", self.qos)
        self.state_pub = self.create_publisher(Bool, "/state", self.qos)
        self.mode_pub = self.create_publisher(Int8, "/mode", self.qos)
        self.config_pub = self.create_publisher(String, "/config", self.qos)
        self.vel_pub = self.create_publisher(Float32MultiArray, "/vel", self.qos)

        self.timer = self.create_timer(0.1, self.timer_callback)
        

    def joy_callback(self, joy: Joy):               # Check all the joy inputs and perform required functions
        self.joy_callback_last_time = time.time()
        if not self.state:   # Enters this when rover is in manual mode  
            if joy.buttons[self.change_dir_button] and (time.time() - self.last_time) > self.cooldown_period:
                if self.rover_direction == "ArmForward":
                    self.rover_direction = "ZedForward"
                else:
                    self.rover_direction = "ArmForward"
                self.last_time = time.time()

            if joy.buttons[self.mode_up_button] and (time.time() - self.last_time) > self.cooldown_period:
                if self.mode < 5:
                    self.mode += 1
                self.last_time = time.time()

            if joy.buttons[self.mode_down_button] and (time.time() - self.last_time) > self.cooldown_period:
                if self.mode > 0:
                    self.mode -= 1
                self.last_time = time.time()

            if self.rover_direction == "ZedForward" :
                self.drive_ctrl = [joy.axes[self.fb_axis], joy.axes[self.lr_axis]]
            else: 
                self.drive_ctrl = [-joy.axes[self.fb_axis], joy.axes[self.lr_axis]]

        if joy.buttons[self.autonomous_btn] and (time.time() - self.last_time) > self.cooldown_period: 
            if self.state:
                self.state = False
            else:
                self.state = True
            self.last_time = time.time()

    def autonomous_callback(self, msg: Twist):
        if self.state: 
            self.autonomous_vel = msg.linear.x 
            self.autonomous_omega = msg.angular.z

    def timer_callback(self):
        if time.time() - self.joy_callback_last_time > 0.7:
            self.pwm_msg.data = [0,0,0,0]
            self.pwm_pub.publish(self.pwm_msg)
            self.get_logger().warn("run joy launch")
            return
        
        print()
        self.get_logger().info(f"Rover Direction : {self.rover_direction}")

        state_msg = Bool()
        state_msg.data = self.state
        self.state_pub.publish(state_msg)

        self.mode_pub.publish(Int8(data=self.mode))

        if self.state:
            self.config_pub.publish(String(data="AUTO"))
            self.get_logger().warn("Autonomous Mode")
        else:
            self.config_pub.publish(String(data="MANUAL"))
            print("Manual Mode")

        if self.state:
            self.get_logger().info(f"auto vel is : {self.autonomous_vel}")
            self.get_logger().info(f"auto omega is : {self.autonomous_omega}")


        else:
            print(f"Mode :{self.mode}")

        self.drive()
        for i in range (4):
            self.pwm_msg.data[i] = (self.pwm_msg.data[i]) * (self.init_dir[i])
        self.pwm_pub.publish(self.pwm_msg)
            

    def drive(self):
        velocity = -self.autonomous_vel if self.state else self.drive_multipliers[self.mode] * self.drive_ctrl[0]
        omega = self.autonomous_omega if self.state else self.drive_multipliers[self.mode] * self.drive_ctrl[1]
        print(f"velocity: {velocity}")
        print(f"omega: {omega}")

        avg_velocity = avg_omega = 0

        if self.vel_prev.full() and self.omega_prev.full():
            avg_velocity = sum(self.vel_prev.queue) / self.qsize
            avg_omega = sum(self.omega_prev.queue) / self.qsize
            self.vel_prev.get() 
            self.omega_prev.get()
        
        self.vel_prev.put(velocity, True, 2)
        self.omega_prev.put(omega, True, 2)

        # For GUI visualization
        vel_msg = Float32MultiArray()
        vel_msg.data = [float(avg_velocity), float(avg_omega)]
        self.vel_pub.publish(vel_msg)
        if avg_velocity == 0:
            self.pwm_msg.data[0] = int(avg_velocity + avg_omega)
            self.pwm_msg.data[1] = int(avg_velocity - avg_omega)
            self.pwm_msg.data[2] = int(avg_velocity - avg_omega)
            self.pwm_msg.data[3] = int(avg_velocity + avg_omega)
        elif avg_velocity > 0: 
            if avg_omega >= 0 :
                self.pwm_msg.data[0] = int(avg_velocity + avg_omega)
                self.pwm_msg.data[1] = int(avg_velocity)
                self.pwm_msg.data[2] = int(avg_velocity)
                self.pwm_msg.data[3] = int(avg_velocity + avg_omega)
            elif avg_omega < 0: 
                self.pwm_msg.data[0] = int(avg_velocity)
                self.pwm_msg.data[1] = int(avg_velocity - avg_omega)
                self.pwm_msg.data[2] = int(avg_velocity - avg_omega)
                self.pwm_msg.data[3] = int(avg_velocity)
        elif avg_velocity < 0: 
            if avg_omega >= 0 :
                self.pwm_msg.data[0] = int(avg_velocity)
                self.pwm_msg.data[1] = int(avg_velocity - avg_omega)
                self.pwm_msg.data[2] = int(avg_velocity - avg_omega)
                self.pwm_msg.data[3] = int(avg_velocity)
            elif avg_omega < 0: 
                self.pwm_msg.data[0] = int(avg_velocity - avg_omega)
                self.pwm_msg.data[1] = int(avg_velocity)
                self.pwm_msg.data[2] = int(avg_velocity)
                self.pwm_msg.data[3] = int(avg_velocity - avg_omega)

    def debug_print(self,msg):
        if self.debug:
            print(msg)

def main(args=None):
    rclpy.init(args=args)
    node = Drive()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
