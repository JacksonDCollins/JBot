from structs import Vector3, Rotator
from PID import PID
import math
import bezier
import numpy as np

TICK = 1.0/60.0
FIELD_LENGTH = 10280
FIELD_WIDTH = 8240
FIELD_HEIGHT = 2044
BALL_RADIUS = 92.75
RATE = 0.97
vals_twiddle = [4.6268015428221885, 0.7891930796964492, 0.2058911320946492]
pid = PID(vals_twiddle[0], vals_twiddle[1], vals_twiddle[2], setpoint=0, sample_time=(1.0/60.0), output_limits=(-1,1))

def localize(target, us):
	x = (target - us.location) * us.matrix[0]
	y = (target - us.location) * us.matrix[1]
	z = (target - us.location) * us.matrix[2]
	return Vector3(x,y,z)
	# return dot(target-us.location, us.theta)

def point_on_circle(location, angle, radius, rotator = Rotator(0,0,0)):
	if isinstance(location, Vector3):
		if not hasattr(location, 'rotation'):
			rotation = rotator
			location.rotation = rotation
		else:
			rotation = location.rotation
	else:
		rotation = location.rotation
		location = location.location

	x = location.x + radius*math.cos(rotation.yaw + angle)
	y = location.y + radius*math.sin(rotation.yaw + angle)
	z = location.z
	point = Vector3(x,y,z)
	point.rotation = rotation
	return point

def angle2D(target, us, local = False):
	if not local:
		dif = localize(target, us)
		return math.atan2(dif.y, dif.x)
	else:
		difference = us - target
		return math.atan2(difference.y, difference.x)

def angle3D(target, us):
	# req = toLocal(v2, v1)
	p = math.sin(target.pitch - us.rotation.pitch)
	y = math.sin(target.yaw - us.rotation.yaw)
	r = math.sin(target.roll - us.rotation.roll)

	angles = Rotator(p, y, r)

	return angles

def distance2D(target, us):
	difference = target - us
	return math.sqrt(difference.x**2 + difference.y**2)

def velocity2D(target_object):
	return math.sqrt(target_object.velocity.x**2 + target_object.velocity.y**2)

def cap(x, low, high):
	if x < low:
		return low
	elif x > high:
		return high
	else:
		return x

def steer(angle, car = None):
	if isinstance(angle, int) or isinstance(angle, float):
		return pid(-angle)
	else:
		angle = angle2D(angle, car)
		return pid(-angle)

def throttle(car, speed):
	t = 0
	boost = False
	current_speed = velocity2D(car)
	if speed > current_speed:
		t = 1
		if speed > 1400:
			boost = True
	elif speed < current_speed:
		t = 0
	return t, boost

def sign(x):
	if x <= 0:
		return -1
	else:
		return 1

def opp(x):
	if x == 0:
		return 1
	else:
		return 0

def find_point_on_line(v1, v2, offset):
	local_offset = v2 + Vector3(offset * (v1.x - v2.x), offset * (v1.y - v2.y), v2.z)
	return local_offset

def turn_radius(car, target = None):
	if target:
		steering = 1.0# abs(steer(target, car))
	else:
		steering = 1.0

	if velocity2D(car) == 0:
		return 0.00000001
	return steering / curvature(velocity2D(car))

# v is the magnitude of the velocity in the car's forward direction
def curvature(v):
    if 0.0 <= v < 500.0:
        return 0.006900 - 5.84e-6 * v
    elif 500.0 <= v < 1000.0:
        return 0.005610 - 3.26e-6 * v
    elif 1000.0 <= v < 1500.0:
        return 0.004300 - 1.95e-6 * v
    elif 1500.0 <= v < 1750.0:
        return 0.003025 - 1.10e-6 * v
    elif 1750.0 <= v < 2500.0:
        return 0.001800 - 0.40e-6 * v
    else:
        return 0.0

def ballReady(control):
	ball = control.ball
	if abs(ball.velocity.z) < 100 and ball.location.z < 250:
		if abs(ball.location.y) < 5000:
			return True
	return False

def ballProject(control):
	goal = control.agent.game_info.their_goal.location
	goal_to_ball = (control.ball.location - goal).normalize()
	difference = control.car.location - control.ball.location
	return difference * goal_to_ball

def future(ball,time):
	x = ball.location.x + (ball.velocity.x * time)
	y = ball.location.y + (ball.velocity.y * time)
	z = ball.location.z + (ball.velocity.y * time) - ball.velocity.y*(time*-RATE)
	return Vector3(x,y,z)

def dpp(target_loc,target_vel,our_loc,our_vel):
	target_loc = target_loc
	our_loc = our_loc
	our_vel = our_vel
	d = distance2D(target_loc,our_loc)
	if d != 0:
		return (((target_loc.x - our_loc.x) * (target_vel.x - our_vel.x)) + ((target_loc.y - our_loc.y) * (target_vel.y - our_vel.y)))/d
	else:
		return 0
	
def get_curve(points, ori, facing = Rotator(0,0,0), car = None):
	tpi = points.index('TP')

	direction = sign(angle2D(points[tpi-1], points[tpi+1], True))
	amp = abs(angle2D(points[tpi-1], points[tpi+1], True))

	mid_point = find_point_on_line(points[tpi-1], points[tpi+1], 0.5)
	
	angle_vec = point_on_circle(mid_point, ori*math.pi/2, 1, facing)

	angle = angle2D(mid_point, car)
	h = abs(distance2D(points[0],mid_point)/math.cos(angle))
	# print(h)

	turn_point = find_point_on_line(mid_point, angle_vec, h/amp)

	points[tpi] = turn_point

	x = [point.x for point in points]
	y = [point.y for point in points]
	nodes = np.asfortranarray([x,y])
	return nodes, bezier.Curve.from_nodes(nodes)

	

def map(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)

def rotate(v1,theta, dimension = 2):
	
	rotate_matrix = [[math.cos(theta), -math.sin(theta)],
					 [math.sin(theta), math.cos(theta)]]
	
	vector = v1[:dimension]
	
	rotated = [vector[0]*rotate_matrix[0][0] + vector[1]*rotate_matrix[1][0],
			   vector[0]*rotate_matrix[1][0] + vector[1]*rotate_matrix[1][1]]
	
	return Vector3(rotated[0], rotated[1], 0)
