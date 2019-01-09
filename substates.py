from RLUtilities.Maneuvers import AerialTurn
from RLUtilities.GameInfo import GameInfo

from rlbot.agents.base_agent import SimpleControllerState

import utils
import structs
import math
import time
import bezier
import numpy as np

def pick_state(master, agent, car, target, speed, hierarchy = None):
	if master.substate.expired:
		if hierarchy:
			for substate in hierarchy:
				if substate(master, agent, car, target, speed).available():
					if substate(master, agent, car, target, speed).name == master.substate.name:
						master.substate.update(master, agent, car, target, speed)
						return master.substate
					else:
						return substate(master, agent, car, target, speed)
		else: 
			hierarchy = [recover, dodge, move]
			return pick_state(master, agent, car, target, speed, hierarchy)
	master.substate.update(master, agent, car, target, speed)
	return master.substate


class move():
	def __init__(self, master = None, agent = None, car = None, target = None, speed = None):
		self.name = 'MOVE'
		self.master = master
		self.agent = agent
		self.car = car
		self.target = target
		self.speed = speed
		self.controls = SimpleControllerState()
		self.expired = False
		self.to_hit = []
		self.cur_hit = 0
		self.last_target_ang = structs.Rotator(0,0,0)
	
	def update(self, master = None, agent = None, car = None, target = None, speed = None):
		self.master = master
		self.agent = agent
		self.car = car
		self.target = target
		self.speed = speed

	def available(self):
		return True

	def step(self, tick):
		# if self.target == self.master.ball.location:
		# 	self.master.ball.step(tick)
		# 	self.target = self.master.ball.location

		
		# if self.agent.team == 0: print(utils.steer(self.target, self.car), utils.angle2D(self.target, self.car), self.target.tuple, self.car.location.tuple)
		
		# self.controls.yaw = utils.steer(self.target, self.car)
		self.controls.throttle, self.controls.boost = utils.throttle(self.car, self.speed)

		turn_radius = utils.turn_radius(self.car, self.target)
		angle_to_target = utils.angle2D(self.target, self.car)

		point = utils.point_on_circle(self.car, utils.sign(angle_to_target)*math.pi/2, turn_radius)#, self.car.rotation)
		circle = []
		for i in range(0, 366, 6):
			n = utils.point_on_circle(point, math.radians(i), turn_radius)#, point.rotation)
			circle.append(n.tuple)
		self.agent.renderer.draw_polyline_3d(circle, self.agent.renderer.red())
		
		
		# ball_prediction = self.agent.get_ball_prediction_struct()
		# if ball_prediction is not None:
		# 	# for i in range(0, ball_prediction.num_slices):
		# 	if self.target == self.master.ball.location:
		# 		self.target = structs.Vector3(ball_prediction.slices[10].physics.location)
		# 		turn_radius = utils.turn_radius(self.car, self.target)

		
		# goal_to_ball_uv = (self.agent.game_info.their_goal.location - self.agent.game_info.ball.location).normalize()
		# yaw = math.atan2(goal_to_ball_uv.x, goal_to_ball_uv.z) #math.atan((goal_to_ball_uv.x/(-goal_to_ball_uv.y)))#
		# pitch = 0#math.atan(math.hypot(goal_to_ball_uv.x, goal_to_ball_uv.y)/goal_to_ball_uv.z)

		# target_ang = structs.Rotator(pitch, yaw, 0)

		# circle_point = utils.point_on_circle(self.target, math.pi/2, turn_radius, target_ang)
		# circle = []
		# for i in range(0, 366, 6):
		# 	n = utils.point_on_circle(circle_point, math.radians(i), turn_radius)
		# 	circle.append(n.tuple)
		# self.agent.renderer.draw_polyline_3d(circle, self.agent.renderer.black())
		
		# x1 = point.x
		# y1 = point.y
		# x2 = circle_point.x
		# y2 = circle_point.y
		
		# gamma = -math.atan((y2-y1)/(x2-x1))
		# beta = math.asin((turn_radius-turn_radius)/math.sqrt((x2-x1)**2 + (y2-y1)**2))
		# alpha = gamma-beta

		# x3 = x1 - turn_radius*math.cos((math.pi/2)-alpha)
		# y3 = y1 - turn_radius*math.sin((math.pi/2)-alpha)
		# x4 = x2 + turn_radius*math.cos((math.pi/2)-alpha)
		# y4 = y2 + turn_radius*math.sin((math.pi/2)-alpha)

		# tang1 = structs.Vector3(x3, y3, 100)
		# tang2 = structs.Vector3(x4, y4, 100)
		
		# if self.last_target_ang != target_ang:
		# 	print('ye')
		# 	self.cur_hit = 0
		# 	self.last_target_ang = target_ang
		
		# self.to_hit = [tang1, tang2, self.agent.game_info.ball.location]
		
		# self.agent.renderer.draw_rect_3d(self.to_hit[0].tuple, 20, 20, True, self.agent.renderer.black())
		# self.agent.renderer.draw_rect_3d(self.to_hit[1].tuple, 20, 20, True, self.agent.renderer.black())


		# point_to_target = utils.distance2D(self.target, point)
		# if point_to_target < turn_radius:
		# 	#inside circle
		# 	if abs(utils.angle2D(self.target, self.car)) < math.pi/2:
		# 		to_target = utils.localize(self.target, self.car).normalize(turn_radius)
		# 		self.target = self.car.location - to_target
		# 		self.controls.boost = 0
		# 		self.controls.throttle = 0
		# 	else:
		# 		to_target = utils.localize(self.target, self.car).normalize(turn_radius)
		# 		self.target = self.car.location - to_target
		# 		self.controls.boost = 0
		# 		self.controls.handbrake = 1
		
		

		# point2 = structs.Vector3(x,y,z)
		
		# self.agent.renderer.draw_rect_3d(point.tuple, 10, 10, True, self.agent.renderer.blue())
		
		if utils.distance2D(point, self.target) < turn_radius:
			to_target = utils.localize(self.target, self.car).normalize(turn_radius)
			self.target = self.car.location - to_target
			self.controls.boost = False
			
		else:
			curve = utils.get_curve(self.car.location, self.target, utils.sign(angle_to_target), self.car.rotation)
			points = curve.evaluate_multi(np.linspace(0, 1.0, 100))

			'''
			USE OFFSET FROM GOAL TO BALL AS POINT IN CURVE
			'''
			
			
			
			
			curve_points = [[points[0][i], points[1][i]] for i in range(len(points[0]))]
			self.agent.renderer.draw_polyline_3d(curve_points, self.agent.renderer.green())
		
		self.controls.steer = utils.steer(self.target, self.car)
		self.agent.renderer.draw_rect_3d(self.target.tuple, 10, 10, True, self.agent.renderer.red())
		self.agent.renderer.draw_line_3d(self.car.location.flatten().tuple, self.target.flatten().tuple, self.agent.renderer.green())

		self.expired = True
		return self.controls

class recover():
	def __init__(self, master = None, agent = None, car = None, target = None, speed = None):
		self.name = 'RECOVER'
		self.master = master
		self.agent = agent
		self.car = car
		self.target = target
		self.speed = speed
		self.controls = SimpleControllerState()
		self.expired = False
		self.Ginfo = GameInfo(agent.index, agent.team)

	def update(self, master = None, agent = None, car = None, target = None, speed = None):
		self.master = master
		self.agent = agent
		self.car = car
		self.target = target
		self.speed = speed
		self.Ginfo = GameInfo(agent.index, agent.team)

	def available(self):
		return not self.car.has_wheel_contact

	def step(self, tick):
		self.Ginfo.read_packet(self.agent.packet)	
		action = AerialTurn(self.Ginfo.my_car)
		action.step(tick)
		action.controls.throttle = 1

		self.expired = action.finished
		self.expired = self.car.has_wheel_contact

		return action.controls

class dodge():
	def __init__(self, master = None, agent = None, car = None, target = None, speed = None):
		self.name = 'DODGE'
		self.master = master
		self.agent = agent
		self.car = car
		self.target = target
		self.speed = speed
		self.controls = SimpleControllerState()
		self.expired = False
		# self.agent.dodgeTimer = time.time()
	
	def update(self, master = None, agent = None, car = None, target = None, speed = None):
		self.master = master
		self.agent = agent
		self.car = car
		self.target = target
		self.speed = speed
		print(self.expired)

	def available(self):
		td = time.time() - self.agent.dodgeTimer
		if td > 2.2  and abs(utils.angle2D(self.target, self.car)) < 1 and utils.velocity2D(self.car) < self.speed and utils.distance2D(self.target, self.car.location) > (utils.velocity2D(self.car)*2.3):
			self.agent.dodgeTimer = time.time()
			return True
		return False

	def step(self, tick):
		cs = self.controls
		angle = utils.angle2D(self.target, self.car)
		td = time.time() - self.agent.dodgeTimer
		# cs.throttle, cs.boost = utils.throttle(self.car, self.speed)
		if td <= 0.1:
			cs.jump = True
			cs.pitch = -1
		elif td >= 0.1 and td <= 0.15:
			cs.jump = False
			cs.pitch = -1
		elif td > 0.15 and td < 1:
			cs.jump = True
			cs.yaw = utils.steer(angle)
			cs.pitch = -1
			self.expired = True
			self.agent.dodgeTimer = time.time()
		elif td > 2:
			self.expired = True
			self.agent.dodgeTimer = time.time()
		return cs

class shoot():
	def __init__(self, master = None, agent = None, car = None, target = None, speed = None):
		self.name = 'SHOOT'
		self.master = master
		self.agent = agent
		self.car = car
		self.target = target
		self.speed = speed
		self.controls = SimpleControllerState()
		self.expired = False
		# self.agent.dodgeTimer = time.time()
	
	def update(self, master = None, agent = None, car = None, target = None, speed = None):
		self.master = master
		self.agent = agent
		self.car = car
		self.target = target
		self.speed = speed

	def available(self):
		td = time.time() - self.agent.dodgeTimer
		if (utils.ballReady(self.master) and td > 2.2 and utils.distance2D(self.target,self.car.location) <= 270):
			self.agent.dodgeTimer = time.time()
			return True
		return False

	def step(self, tick):
		goal_angle = utils.angle2D(self.agent.game_info.their_goal.location, self.car)

		cs = self.controls
		# angle = utils.angle2D(self.target, self.car)
		td = time.time() - self.agent.dodgeTimer
		if td <= 0.1:
			cs.jump = True
			cs.pitch = -1
		elif td >= 0.1 and td <= 0.15:
			cs.jump = False
			cs.pitch = -1
		elif td > 0.15 and td < 1:
			cs.jump = True
			cs.yaw = math.sin(goal_angle)
			cs.pitch = -abs(math.cos(goal_angle))
		elif td > 1:
			self.expired = True
			self.agent.dodgeTimer = time.time()
		return cs

class default():
	def __init__(self, *args):
		self.name = 'DEFAULT'
		self.expired = True
		self.target_ang = structs.Rotator(0,0,0)

	def step(self, *args):
		return SimpleControllerState()
