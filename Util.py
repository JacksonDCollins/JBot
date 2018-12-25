import math
from rlbot.utils.structures.game_data_struct import Vector3 as v3
from RLUtilities.LinearAlgebra import *
from RLUtilities.GameInfo import GameInfo
from RLUtilities.Simulation import Car, Input
GOAL_WIDTH = 1900
FIELD_LENGTH = 10280
FIELD_WIDTH = 8240
FIELD_HEIGHT = 2044
BALL_RADIUS = 92.75

class Vector3:
	def __init__(self, data):
		if isinstance(data, v3):
			self.data = [data.x, data.y, data.z]
		else:
			self.data = data
	def __add__(self,value):
		return Vector3([self.data[0]+value.data[0],self.data[1]+value.data[1],self.data[2]+value.data[2]])
	def __sub__(self,value):
		return Vector3([self.data[0]-value.data[0],self.data[1]-value.data[1],self.data[2]-value.data[2]])
	def __mul__(self,value):
		return (self.data[0]*value.data[0] + self.data[1]*value.data[1] + self.data[2]*value.data[2])
	def __str__(self):
		return f'{self.data[0]}, {self.data[1]}, {self.data[2]}'
	def magnitude(self):
		return math.sqrt((self.data[0]*self.data[0]) + (self.data[1] * self.data[1])+ (self.data[2]* self.data[2]))
	def normalize(self):
		mag = self.magnitude()
		if mag != 0:
			return Vector3([self.data[0]/mag, self.data[1]/mag, self.data[2]/mag])
		else:
			return Vector3([0,0,0])

	@property
	def x(self):
		return self.data[0]

	@property
	def y(self):
		return self.data[1]

	@property
	def z(self):
		return self.data[2]
	

class obj:
	def __init__(self, agent, data, local = None):
		self.location = Vector3([data.physics.location.x, data.physics.location.y, data.physics.location.z])
		self.velocity = Vector3([data.physics.velocity.x, data.physics.velocity.y, data.physics.velocity.z])
		self.rotation = Vector3([data.physics.rotation.pitch, data.physics.rotation.yaw, data.physics.rotation.roll])
		self.rvelocity = Vector3([data.physics.angular_velocity.x, data.physics.angular_velocity.y, data.physics.angular_velocity.z])
		self.matrix = self.rotator_to_matrix()
		self.local_location = Vector3([0,0,0])
		self.boost = 0

	def glocation(self):
		return [rmap(self.location.data[0],-FIELD_WIDTH/2, FIELD_WIDTH/2), rmap(self.location.data[1],-FIELD_LENGTH/2, FIELD_LENGTH/2), rmap(self.location.data[2], 0, FIELD_HEIGHT)]

	def gvelocity(self):
		return [self.velocity.data[0], self.velocity.data[1], self.velocity.data[2]]

	def grotation(self):
		return [rmap(self.rotation.data[0], -math.pi, math.pi), rmap(self.rotation.data[1], -math.pi, math.pi), rmap(self.rotation.data[2], -math.pi, math.pi)]

	def grvelocity(self):
		return [self.rvelocity.data[0], self.rvelocity.data[1], self.rvelocity.data[2]]

	def rotator_to_matrix(self):
		r = self.rotation.data
		CR = math.cos(r[2])
		SR = math.sin(r[2])
		CP = math.cos(r[0])
		SP = math.sin(r[0])
		CY = math.cos(r[1])
		SY = math.sin(r[1])

		matrix = []
		matrix.append(Vector3([CP*CY, CP*SY, SP]))
		matrix.append(Vector3([CY*SP*SR-CR*SY, SY*SP*SR+CR*CY, -CP*SR]))
		matrix.append(Vector3([-CR*CY*SP-SR*SY, -CR*SY*SP+SR*CY, CP*CR]))
		return matrix

def rmap(val, mmin, mmax):
	span = mmax - mmin
	scale = float(val-mmin)/ float(span)
	if scale < 0: print(val, mmin, mmax)
	return cap(0 + (scale * 1), 0, 1)

def nrmap(val, mmin, mmax, mi, ma):
	span = mmax - mmin
	scale = float(val-mmin)/ float(span)
	if scale < 0: print(val, mmin, mmax)
	return cap(mi + (scale * ma), mi, ma)

def quad(a,b,c):
	inside = (b**2) - (4*a*c)
	if inside < 0 or a == 0:
		return 0.1
	else:
		n = ((-b - math.sqrt(inside))/(2*a))
		p = ((-b + math.sqrt(inside))/(2*a))
		if p > n:
			return p
		return n

def timeZ(ball):
	rate = 0.97
	return quad(-325, ball.velocity.data[2] * rate, ball.location.data[2]-92.75)

def timeZCar(ball):
	rate = 0.97
	return quad(-325, ball.velocity.data[2] * rate, ball.location.data[2]-60)

def dpp(target_loc,target_vel,our_loc,our_vel):
	target_loc = toLocation(target_loc)
	our_loc = toLocation(our_loc)
	our_vel = toLocation(our_vel)
	d = distance2D(target_loc,our_loc)
	if d != 0:
		return (((target_loc.data[0] - our_loc.data[0]) * (target_vel.data[0] - our_vel.data[0])) + ((target_loc.data[1] - our_loc.data[1]) * (target_vel.data[1] - our_vel.data[1])))/d
	else:
		return 0
		
def future(ball,time):
	x = ball.location.data[0] + (ball.velocity.data[0] * time)
	y = ball.location.data[1] + (ball.velocity.data[1] * time)
	z = ball.location.data[2] + (ball.velocity.data[2] * time)
	return Vector3([x,y,z])

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

def angle2D(target_location, object_location):
	difference = toLocation(target_location) - toLocation(object_location)
	return math.atan2(difference.data[1], difference.data[0])

def angle3D(v1, v2):
	# req = toLocal(v2, v1)
	p = math.sin(v2.x - v1.rotation.x)

	y = math.sin(v2.y - v1.rotation.y )
	r = math.sin(v2.z - v1.rotation.z)

	angles = Vector3([p, y, r])

	return angles

def get_req_ypr(v1, v2):
	req_angles = angle3D(v1, v2)

	x = rotate(v1.rvelocity.x, v1.rotation.x, req_angles.x)
	y = rotate(v1.rvelocity.y, v1.rotation.y, req_angles.y)
	z = rotate(v1.rvelocity.z, v1.rotation.z, req_angles.z)
	return x,y,z

def rotate(car_angle_velocity, car_angle, angle):
	nangle = (car_angle - angle) % math.pi
	co = nrmap(nangle, 0, math.pi, 0, 1)
	return -co

def toLocation(target):
	if isinstance(target, Vector3):
		return target
	elif isinstance(target, list):
		return Vector3(target)
	else:
		return target.location

def toLocal(target, our_object):
	if isinstance(target, obj):
		return target.local_location
	else:
		return to_local(target, our_object)

def to_local(target_object, our_object):
	x = (toLocation(target_object) - our_object.location) * our_object.matrix[0]
	y = (toLocation(target_object) - our_object.location) * our_object.matrix[1]
	z = (toLocation(target_object) - our_object.location) * our_object.matrix[2]
	return Vector3([x,y,z])

def velocity2D(target_object):
	return math.sqrt(target_object.velocity.data[0]**2 + target_object.velocity.data[1]**2)

def distance2D(target_object, our_object):
	difference = toLocation(target_object) - toLocation(our_object)
	return math.sqrt(difference.data[0]**2 + difference.data[1]**2)

def ballReady(agent):
	ball = agent.ball
	if abs(ball.velocity.data[2]) < 100 and ball.location.data[2] < 250:
		if abs(ball.location.data[1]) < 5000:
			return True
	return False

def ballProject(agent):
	goal = Vector3([0,-sign(agent.team)*FIELD_LENGTH/2,100])
	goal_to_ball = (agent.ball.location - goal).normalize()
	difference = agent.me.location - agent.ball.location
	return difference * goal_to_ball

def cap(x, low, high):
	if x < low:
		return low
	elif x > high:
		return high
	else:
		return x

def steer(angle):
	final = ((10 * angle+sign(angle))**3) / 20
	return cap(final,-1,1)

def throttle(agent, tspeed):
	t = 0
	boost = False
	current_speed = velocity2D(agent.me)
	if tspeed > current_speed:
		t = 1
		if tspeed > 1400:
			boost = True
	elif tspeed < current_speed:
		t = 0

	return t, boost

def turn_radius(v):
    if v == 0:
        return 1
    return 1.0 / curvature(v)

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

def find_point_on_line(v1, v2, offset):
	# v1 = toLocation(v1)
	# v2 = toLocation(v2)

	# local = toLocal(v2, v1)

	local_offset = toLocation(v2) + Vector3([offset * (v1.x - v2.location.x), offset * (v1.y - v2.location.y), 0])
	return local_offset

def angle_line_car(x1,fy1,fcar):
	y1 = fy1.location
	car = fcar.location

	m1 = (y1.y-x1.y)/(y1.x-x1.y)
	c1 = x1.y -(m1*x1.x)

	point1 = car
	point2 = future(fcar, 1000)# + Vector3([car.normalize().x * .1, car.normalize().y * .1, car.normalize().z * .1])
	m2 = (point2.y-point1.y)/(point2.x-point1.y)
	c2 = point1.y - (m2*point1.x)

	x = (c2-c1)/(m1-m2)
	y = (m1*x) + c1

	point = Vector3([x,y,0])
	loc_point = toLocal(fcar, point)
	return angle2D(loc_point, fcar), point2