#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Float32MultiArray
from tf2_ros import TransformBroadcaster
import RPi.GPIO as GPIO
import math

# -------- PIN CONFIG --------
ENA, IN1, IN2 = 18, 23, 24
ENB, IN3, IN4 = 17, 27, 22
L_PHA, L_PHB = 20, 21
R_PHA, R_PHB = 26, 19

# -------- ROBOT PARAMS --------
WHEEL_RADIUS = 0.035  # meters
WHEEL_BASE = 0.20     # meters
PPR = 20              # Pulses Per Revolution

class MotorEncoderBridge(Node):
    def __init__(self):
        super().__init__('motor_encoder_bridge')
        
        # ROS Setup
        self.cmd_sub = self.create_subscription(Twist, '/cmd_vel', self.cmd_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # State Variables
        self.l_ticks = 0
        self.r_ticks = 0
        self.last_l_dist = 0.0
        self.last_r_dist = 0.0
        self.x = 0.0
        self.y = 0.0
        self.th = 0.0 # yaw
        self.last_time = self.get_clock().now()
        
        # GPIO Setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup([IN1, IN2, IN3, IN4, ENA, ENB], GPIO.OUT)
        GPIO.setup([L_PHA, L_PHB, R_PHA, R_PHB], GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        self.pwm_l = GPIO.PWM(ENA, 1000)
        self.pwm_r = GPIO.PWM(ENB, 1000)
        self.pwm_l.start(0)
        self.pwm_r.start(0)

        GPIO.add_event_detect(L_PHA, GPIO.FALLING, callback=self.l_callback)
        GPIO.add_event_detect(R_PHA, GPIO.FALLING, callback=self.r_callback)

        # Update loop (20Hz for smoother SLAM)
        self.timer = self.create_timer(0.05, self.update_odometry)
        self.get_logger().info("Task 4: Odometry & TF Node Started")

    def l_callback(self, _):
        self.l_ticks += 1 if GPIO.input(L_PHB) == GPIO.HIGH else -1

    def r_callback(self, _):
        self.r_ticks += 1 if GPIO.input(R_PHB) == GPIO.HIGH else -1

    def cmd_callback(self, msg):
        v, w = msg.linear.x, msg.angular.z
        l_speed = v - (w * WHEEL_BASE / 2.0)
        r_speed = v + (w * WHEEL_BASE / 2.0)
        self.set_motor(l_speed, IN1, IN2, self.pwm_l)
        self.set_motor(r_speed, IN3, IN4, self.pwm_r)

    def set_motor(self, speed, in1, in2, pwm):
        direction = GPIO.HIGH if speed >= 0 else GPIO.LOW
        GPIO.output(in1, direction)
        GPIO.output(in2, not direction)
        pwm.ChangeDutyCycle(min(abs(speed) * 100, 100))

    def update_odometry(self):
        current_time = self.get_clock().now()
        
        # Calculate distance traveled by each wheel
        l_dist = (self.l_ticks / PPR) * (2 * math.pi * WHEEL_RADIUS)
        r_dist = (self.r_ticks / PPR) * (2 * math.pi * WHEEL_RADIUS)
        
        dl = l_dist - self.last_l_dist
        dr = r_dist - self.last_r_dist
        
        # Differential Drive Kinematics
        dc = (dl + dr) / 2.0  # distance center
        dth = (dr - dl) / WHEEL_BASE # change in heading
        
        # Update Pose
        self.x += dc * math.cos(self.th)
        self.y += dc * math.sin(self.th)
        self.th += dth
        
        # 1. Publish TF Transform (The "Bridge")
        t = TransformStamped()
        t.header.stamp = current_time.to_msg()
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.rotation.z = math.sin(self.th / 2.0)
        t.transform.rotation.w = math.cos(self.th / 2.0)
        self.tf_broadcaster.sendTransform(t)

        # 2. Publish Odom Message
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation = t.transform.rotation
        self.odom_pub.publish(odom)

        # Save for next iteration
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