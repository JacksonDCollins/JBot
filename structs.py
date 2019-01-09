import math
import utils

class Game():
	def __init__(self, BaseAgent, index, team):
		self.BaseAgent = BaseAgent
		self.index = index
		self.team = team
	
	def read_packet(self, BaseAgent, packet):
		self.BaseAgent = BaseAgent
		fieldInfo = BaseAgent.get_field_info()

		self.cars = []
		self.my_car = None
		self.their_cars = []
		for n, car in enumerate(packet.game_cars):
			lcar = Car(car)
			if n == self.index:
				self.my_car = lcar
			else:
				self.their_cars.append(lcar)
			self.cars.append(lcar)

		self.my_goal = Goal(self.team, Vector3(0.0, utils.sign(self.team)*5120.0, 312.0))
		self.their_goal = Goal(self.team, Vector3(0.0, utils.opp(utils.sign(self.team))*5120.0, 312.0))
		self.goals = [self.my_goal, self.their_goal]

		self.ball = Ball(packet.game_ball)

		self.boosts = []
		for n, boost in enumerate(packet.game_boosts):
			self.boosts.append(Boost(boost, n))
		
		for n, boost in enumerate(fieldInfo.boost_pads):
			cboost = [boosts for boosts in self.boosts if boosts.index == n][0]
			cboost.update(boost)

class Boost():
	def __init__(self, boost, n):
		self.index = n
		self.location = Vector3(0,0,0)
		self.is_full_boost = None
		self.is_active = boost.is_active
		self.timer = boost.timer
	
	def update(self, boost):
		self.location = Vector3(boost.location)
		self.is_full_boost = boost.is_full_boost

class Ball():
	def __init__(self, ball):
		self.location = Vector3(ball.physics.location)
		self.rotation = Rotator(ball.physics.rotation)
		self.velocity = Vector3(ball.physics.velocity)
		self.angular_velocity = Vector3(ball.physics.angular_velocity)
		self.latest_touch = ball.latest_touch
		self.drop_shot_info = ball.drop_shot_info

		r = self.rotation
		CR = math.cos(r.roll)
		SR = math.sin(r.roll)
		CP = math.cos(r.pitch)
		SP = math.sin(r.pitch)
		CY = math.cos(r.yaw)
		SY = math.sin(r.yaw)

		matrix = []
		matrix.append(Vector3(CP*CY, CP*SY, SP))
		matrix.append(Vector3(CY*SP*SR-CR*SY, SY*SP*SR+CR*CY, -CP*SR))
		matrix.append(Vector3(-CR*CY*SP-SR*SY, -CR*SY*SP+SR*CY, CP*CR))
		self.matrix = matrix

class Goal():
	def __init__(self, team_num, location):
		WIDTH = 1900
		self.team_num = team_num
		self.location = location
		self.left_post = Vector3(WIDTH/2,self.location.y,100)
		self.right_post = Vector3(-WIDTH/2,self.location.y,100)
		self.top_left = Vector3(WIDTH/2,self.location.y, 642.775)
		self.bottom_left = Vector3(WIDTH/2,self.location.y, 0)
		self.top_right = Vector3(-WIDTH/2,self.location.y, 642.775)
		self.bottom_right = Vector3(-WIDTH/2,self.location.y, 0)

class Car():
	def __init__(self, car):
		self.car = car
		self.location = Vector3(car.physics.location)
		self.rotation = Rotator(car.physics.rotation)
		self.velocity = Vector3(car.physics.velocity)
		self.angular_velocity = Vector3(car.physics.angular_velocity)
		self.score_info = car.score_info
		self.is_demolished = car.is_demolished
		self.has_wheel_contact = car.has_wheel_contact
		self.is_super_sonic = car.is_super_sonic
		self.is_bot = car.is_bot
		self.jumped = car.jumped
		self.double_jumped = car.double_jumped
		self.name = car.name
		self.team = car.team
		self.boost = car.boost

		r = self.rotation
		CR = math.cos(r.roll)
		SR = math.sin(r.roll)
		CP = math.cos(r.pitch)
		SP = math.sin(r.pitch)
		CY = math.cos(r.yaw)
		SY = math.sin(r.yaw)

		matrix = []
		matrix.append(Vector3(CP*CY, CP*SY, SP))
		matrix.append(Vector3(CY*SP*SR-CR*SY, SY*SP*SR+CR*CY, -CP*SR))
		matrix.append(Vector3(-CR*CY*SP-SR*SY, -CR*SY*SP+SR*CY, CP*CR))
		self.matrix = matrix

class Vector3():
	def __init__(self, *args):
		if len(args) == 3:
			self.points = [args[0], args[1], args[2]]
		elif len(args) == 1:
			self.points = [args[0].x, args[0].y, args[0].z]
	def __add__(self,value):
		return Vector3(self.points[0]+value.points[0],self.points[1]+value.points[1],self.points[2]+value.points[2])
	def __sub__(self,value):
		return Vector3(self.points[0]-value.points[0],self.points[1]-value.points[1],self.points[2]-value.points[2])
	def __mul__(self,value):
		return (self.points[0]*value.points[0] + self.points[1]*value.points[1] + self.points[2]*value.points[2])
	def mag(self):
		return math.sqrt(self.points[0]**2 + self.points[1]**2 + self.points[2]**2)
	def normalize(self, units = 1):
		mag = self.mag()
		if mag != 0:
			return Vector3((self.points[0]/mag)*units, (self.points[1]/mag)*units, (self.points[2]/mag)*units)
		else:
			return Vector3([0,0,0])
	def flatten(self):
		return Vector3(self.x, self.y, 0)	
	
	@property
	def x(self):
		return self.points[0]
	@property
	def y(self):
		return self.points[1]
	@property
	def z(self):
		return self.points[2]
	@property
	def tuple(self):
		return tuple(self.points)

class Rotator():
	def __init__(self, *args):
		if len(args) == 3:
			self.points = [args[0], args[1], args[2]]
		elif len(args) == 1:
			self.points = [args[0].pitch, args[0].yaw, args[0].roll]
	def __sub__(self,value):
		return Rotator(self.points[0]-value.points[0],self.points[1]-value.points[1],self.points[2]-value.points[2])
	def __eq__(self, value):
		return self.pitch == value.pitch and self.yaw == value.yaw and self.roll == value.roll
	@property
	def pitch(self):
		return self.points[0]
	@property
	def yaw(self):
		return self.points[1]
	@property
	def roll(self):
		return self.points[2]
	@property
	def tuple(self):
		return tuple(self.points)