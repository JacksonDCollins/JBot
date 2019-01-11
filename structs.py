import math
import utils
import bezier
import numpy as np 

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
		self.their_goal = Goal(self.team, Vector3(0.0, utils.sign(utils.opp(self.team))*5120.0, 312.0))
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
	def __getitem__(self, key):
		return self.points[key]

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
	
	
class Path(bezier.Curve):
	def __init__(self, master, points, ori, facing = Vector3(0,0,0), car = None):
		nodes, degree = utils.get_curve(points, ori, facing, car)
		self.mnodes = nodes
		self.master = master
		super().__init__(nodes, degree)
	
	def get_path_points(self, linspace):
		points = self.evaluate_multi(linspace)
			
		return [[points[0][i], points[1][i]] for i in range(len(points[0]))]
	
	def on_path(self, location):
		point = np.asfortranarray([[location.x], [location.y]])
		# point = self.locate(point)
		# if point == None: 
		# 	return False
		# else:
		# 	return True

		candidates = [(0.0, 1.0, self.mnodes)]
		for _ in range(bezier._curve_helpers._MAX_LOCATE_SUBDIVISIONS + 1):
			next_candidates = []
			for start, end, candidate in candidates:
				if self.contains_nd(candidate, point.ravel(order="F")):
					midpoint = 0.5 * (start + end)
					left, right = bezier._curve_helpers.subdivide_nodes(candidate)
					next_candidates.extend(
						((start, midpoint, left), (midpoint, end, right))
					)
			candidates = next_candidates
		if not candidates:
			return False
			return None

		params = [(start, end) for start, end, _ in candidates]
		if np.std(params) > bezier._curve_helpers._LOCATE_STD_CAP:
			raise ValueError("Parameters not close enough to one another", params)

		s_approx = np.mean(params)
		
		s_approx = bezier._curve_helpers.newton_refine(self.mnodes, point, s_approx)
		# NOTE: Since ``np.mean(params)`` must be in ``[0, 1]`` it's
		#       "safe" to push the Newton-refined value back into the unit
		#       interval.
		if s_approx < 0.0:
			return True
			return 0.0

		elif s_approx > 1.0:
			return True
			return 1.0

		else:
			return True
			return s_approx
	
	def contains_nd(self, nodes, point):
		p = [[nodes[0][i], nodes[1][i]] for i in range(len(nodes[0]))]
		self.master.renderer.draw_polyline_3d(p, self.master.renderer.black())
		min_vals = np.min(nodes, axis=1)
		if not np.all(min_vals <= point):
			return False

		max_vals = np.max(nodes, axis=1)
		if not np.all(point <= max_vals):
			return False

		return True
		
class test(bezier.Curve):
	def __init__(self, nodes, degrees):
		super().__init__(nodes, degrees)
		
	
	def get_path_points(self):
		points = self.evaluate_multi(np.linspace(0.0, 1.0, 100))
			
		return [[points[0][i], points[1][i]] for i in range(len(points[0]))]