import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster
import RPi.GPIO as GPIO
import math

# -------- PIN CONFIG (L298N style) --------
ENA, IN1, IN2 = 18, 23, 24
ENB, IN3, IN4 = 17, 27, 22

L_PHA, L_PHB = 20, 21
R_PHA, R_PHB = 26, 19

# -------- ROBOT PARAMS --------
WHEEL_RADIUS = 0.035  # meters
WHEEL_BASE = 0.20     # meters
PPR = 20              # Pulses Per Revolution (update if needed)

# -------- MOTOR GAINS --------
LEFT_GAIN  = 0.3
RIGHT_GAIN = 1.3

# -------- PWM LIMITS (RPi.GPIO rule) --------
MIN_PWM = 0
MAX_PWM = 130

class MotorEncoderBridge(Node):
    def __init__(self):
        super().__init__('motor_encoder_bridge')

        # ROS Setup
        self.cmd_sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        # State Variables
        self.l_ticks = 0
        self.r_ticks = 0
        self.last_l_dist = 0.0
        self.last_r_dist = 0.0
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0
        self.last_time = self.get_clock().now()

        # GPIO Setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([IN1, IN2, IN3, IN4, ENA, ENB], GPIO.OUT)
        GPIO.setup([L_PHA, L_PHB, R_PHA, R_PHB],
                   GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.pwm_l = GPIO.PWM(ENA, 1000)
        self.pwm_r = GPIO.PWM(ENB, 1000)
        self.pwm_l.start(0)
        self.pwm_r.start(0)

        GPIO.add_event_detect(L_PHA, GPIO.FALLING, callback=self.l_callback)
        GPIO.add_event_detect(R_PHA, GPIO.FALLING, callback=self.r_callback)

        # Update loop (20 Hz)
        self.timer = self.create_timer(0.05, self.update_odometry)
        self.get_logger().info("Odometry + Motor Node Started (with motor gains)")

    # ---------------- Encoder callbacks ----------------
    def l_callback(self, _):
        self.l_ticks += 1 if GPIO.input(L_PHB) == GPIO.HIGH else -1

    def r_callback(self, _):
        self.r_ticks += 1 if GPIO.input(R_PHB) == GPIO.HIGH else -1

    # ---------------- cmd_vel ----------------
    def cmd_callback(self, msg):
        v = msg.linear.x
        w = msg.angular.z

        l_speed = v - (w * WHEEL_BASE / 2.0)
        r_speed = v + (w * WHEEL_BASE / 2.0)

        self.set_motor(l_speed, IN1, IN2, self.pwm_l, LEFT_GAIN)
        self.set_motor(r_speed, IN3, IN4, self.pwm_r, RIGHT_GAIN)

    # ---------------- Motor control (GAIN APPLIED HERE) ----------------
    def set_motor(self, speed, in1, in2, pwm, gain):
        if abs(speed) < 0.001:
            pwm.ChangeDutyCycle(0)
            return

        direction = GPIO.HIGH if speed >= 0 else GPIO.LOW
        GPIO.output(in1, direction)
        GPIO.output(in2, not direction)

        duty = abs(speed) * 100 * gain
        duty = max(MIN_PWM, min(duty, MAX_PWM))

        pwm.ChangeDutyCycle(duty)

    # ---------------- Odometry ----------------
    def update_odometry(self):
        current_time = self.get_clock().now()

        l_dist = (self.l_ticks / PPR) * (2 * math.pi * WHEEL_RADIUS)
        r_dist = (self.r_ticks / PPR) * (2 * math.pi * WHEEL_RADIUS)

        dl = l_dist - self.last_l_dist
        dr = r_dist - self.last_r_dist

        dc = (dl + dr) / 2.0
        dth = (dr - dl) / WHEEL_BASE

        self.x += dc * math.cos(self.th)
        self.y += dc * math.sin(self.th)
        self.th += dth

        # TF
        t = TransformStamped()
        t.header.stamp = current_time.to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.rotation.z = math.sin(self.th / 2.0)
        t.transform.rotation.w = math.cos(self.th / 2.0)
        self.tf_broadcaster.sendTransform(t)

        # Odometry
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation = t.transform.rotation
        self.odom_pub.publish(odom)

        self.last_l_dist = l_dist
        self.last_r_dist = r_dist

    def destroy_node(self):
        self.pwm_l.stop()
        self.pwm_r.stop()
        GPIO.cleanup()
        super().destroy_node()

def main():
    rclpy.init()
    node = MotorEncoderBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()