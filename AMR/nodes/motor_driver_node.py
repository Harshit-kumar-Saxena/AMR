#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float32MultiArray
import RPi.GPIO as GPIO
import math

# ======================================================
# CYTRON PIN CONFIG (PWM + DIR)
# ======================================================
PWM_L = 18      # Hardware PWM
DIR_L = 23

PWM_R = 17      # Software PWM
DIR_R = 27

# Encoder pins
L_PHA, L_PHB = 20, 21
R_PHA, R_PHB = 26, 19

# ======================================================
# ROBOT PARAMETERS
# ======================================================
WHEEL_RADIUS = 0.035
WHEEL_BASE   = 0.20
PPR          = 210

# ======================================================
# PWM CONFIG (SAFE FOR RPi.GPIO)
# ======================================================
MIN_PWM = 20
MAX_PWM = 130   

# Motor calibration gains
LEFT_GAIN  = 0.30   # Left motor slower
RIGHT_GAIN = 1.30   # Right motor faster

class MotorEncoderBridge(Node):

    def __init__(self):
        super().__init__('motor_encoder_bridge')

        # ---------------- ROS Interfaces ----------------
        self.cmd_sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_callback, 10)

        self.dist_pub = self.create_publisher(
            Float32MultiArray, '/wheel_distance', 10)

        # ---------------- Encoder State ----------------
        self.l_ticks = 0
        self.r_ticks = 0

        # ---------------- Target Speeds ----------------
        self.l_target = 0.0
        self.r_target = 0.0

        # ---------------- GPIO Setup ----------------
        GPIO.setmode(GPIO.BCM)

        GPIO.setup([PWM_L, DIR_L, PWM_R, DIR_R], GPIO.OUT)
        GPIO.setup([L_PHA, L_PHB, R_PHA, R_PHB],
                   GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # PWM setup (same as your working test)
        self.pwm_l = GPIO.PWM(PWM_L, 255)
        self.pwm_r = GPIO.PWM(PWM_R, 255)

        self.pwm_l.start(0)
        self.pwm_r.start(0)

        # ---------------- Encoder Interrupts ----------------
        GPIO.add_event_detect(L_PHA, GPIO.FALLING, callback=self.l_callback)
        GPIO.add_event_detect(R_PHA, GPIO.FALLING, callback=self.r_callback)

        # ---------------- Timers ----------------
        self.motor_timer = self.create_timer(0.02, self.update_motors)  # 50 Hz
        self.odom_timer  = self.create_timer(0.1, self.publish_distance)

        self.get_logger().info("✅ Cytron Motor Node Started (Calibrated Mode)")

    # ==================================================
    # Encoder callbacks
    # ==================================================
    def l_callback(self, _):
        self.l_ticks += 1 if GPIO.input(L_PHB) == GPIO.HIGH else -1

    def r_callback(self, _):
        self.r_ticks += 1 if GPIO.input(R_PHB) == GPIO.HIGH else -1

    # ==================================================
    # cmd_vel callback (NO PWM HERE)
    # ==================================================
    def cmd_callback(self, msg):
        v = msg.linear.x
        w = msg.angular.z

        self.l_target = v - (w * WHEEL_BASE / 2.0)
        self.r_target = v + (w * WHEEL_BASE / 2.0)

    # ==================================================
    # Motor update (fixed-rate, stable PWM)
    # ==================================================
    def update_motors(self):
        self.apply_motor(self.l_target, DIR_L, self.pwm_l, LEFT_GAIN)
        self.apply_motor(self.r_target, DIR_R, self.pwm_r, RIGHT_GAIN)

    # ==================================================
    # Motor control logic with per-motor gain
    # ==================================================
    def apply_motor(self, speed, dir_pin, pwm, gain):

        if abs(speed) < 0.01:
            pwm.ChangeDutyCycle(0)
            return

        # Direction
        GPIO.output(dir_pin, GPIO.HIGH if speed >= 0 else GPIO.LOW)

        # Base PWM from cmd_vel
        duty = abs(speed) * 100

        # Apply calibration gain
        duty *= gain

        # Clamp to valid range
        duty = max(MIN_PWM, min(duty, MAX_PWM))

        pwm.ChangeDutyCycle(duty)

    # ==================================================
    # Publish wheel distance
    # ==================================================
    def publish_distance(self):
        msg = Float32MultiArray()

        l_dist = (self.l_ticks / PPR) * (2 * math.pi * WHEEL_RADIUS)
        r_dist = (self.r_ticks / PPR) * (2 * math.pi * WHEEL_RADIUS)

        msg.data = [l_dist, r_dist]
        self.dist_pub.publish(msg)

    # ==================================================
    # Cleanup
    # ==================================================
    def destroy_node(self):
        self.pwm_l.stop()
        self.pwm_r.stop()
        GPIO.cleanup()
        super().destroy_node()


# ======================================================
# MAIN
# ======================================================
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
