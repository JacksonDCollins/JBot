import time
from Util import *

from RLUtilities.Maneuvers import AerialTurn, Drive

class moveSub:
	def __init__(self):
		self.name = 'move'
		self.expired = False
		self.action = None 

	def execute(self, agent, location, speed, cs, current_speed, angle, boost = False, *args, **vargs):
		# self.action = Drive(agent.game_info.my_car, vec3(vargs['t'].x, vargs['t'].y, vargs['t'].z), speed)

		# self.action.step(1.0/60.0)
		# return self.action.controls
		cs.steer = steer(angle)
		if not boost:
			if current_speed < speed:
				cs.throttle = 1.0
			elif current_speed - 50 > speed:
				cs.throttle = -1.0
			else:
				cs.throttle = 0
		else:
			cs.throttle, cs.boost = throttle(agent, speed)
		
		if 'n' in vargs:
			if vargs['n'] > 1:
				cs.handbrake = True
				cs.throttle = 1
				cs.boost = False

		self.expired = True
		return cs

class boostSub:
	def __init__(self):
		self.name = 'boost'
		self.expired = False

	def cavailable(self, agent, cond):
		if cond:
			agent.start = time.time()
			return True
		return False

	def available(self, agent, angle_to_target, current_speed, speed, target):
		td = time.time() - agent.start
		if td > 2.2  and abs(angle_to_target) < 1 and current_speed < speed and distance2D(target,agent.me) > (velocity2D(agent.me)*2.3):
			agent.start = time.time()
			return True
		return False

	def execute(self, agent, location, speed, cs, current_speed, angle, *args, **vargs):
		td = time.time() - agent.start
		if td <= 0.1:
			cs.jump = True
			cs.pitch = -1
		elif td >= 0.1 and td <= 0.15:
			cs.jump = False
			cs.pitch = -1
		elif td > 0.15 and td < 1:
			cs.jump = True
			cs.yaw = steer(angle)
			cs.pitch = -1
		elif td > 1:
			self.expired = True
			agent.start = time.time()

		return cs

class shotSub:
	def __init__(self):
		self.name = 'shot'
		self.expired = False

	def available(self, agent, target):
		td = time.time() - agent.start
		if (ballReady(agent) and td > 2.2 and distance2D(target,agent.me) <= 270):
			agent.start = time.time()
			return True
		return False

	def execute(self, agent, location, speed, cs, current_speed, angle, *args, **vargs):
		td = time.time() - agent.start
		if td <= 0.1:
			cs.jump = True
			cs.pitch = -1
		elif td >= 0.1 and td <= 0.15:
			cs.jump = False
			cs.pitch = -1
		elif td > 0.15 and td < 1:
			cs.jump = True
			try:
				cs.yaw = math.sin(vargs['goal_angle'])
				cs.pitch = -abs(math.cos(vargs['goal_angle']))
			except:
				pass
		elif td > 1:
			self.expired = True
			agent.start = time.time()
		return cs

class recoverSub:
	def __init__(self):
		self.name = 'recover'
		self.expired = False
		self.action = None
		
	def available(self, agent):
		return not agent.me.car.has_wheel_contact

	def execute(self, agent, location, speed, cs, *args, **vargs):
		if self.action == None:
			self.action = AerialTurn(agent.game_info.my_car)

		red = agent.renderer.create_color(255, 255, 30, 30)
		agent.renderer.draw_polyline_3d(self.action.trajectory, red)
		
		self.action.step(1.0 / 60.0)

		self.expired = self.action.finished

		return self.action.controls

		
		# loc = toLocal(location, agent.me)

		
		# # pitch_angle = angle2D(agent.me.rotation, nullvec)
		# # yaw_angle = angle2D(agent.me, location)
		# # roll_angle = angle2D(agent.me.rotation, nullvec)
		# future_time = timeZCar(agent.me)
		# future_loc = future(agent.me, future_time)
		# if abs(future_loc.x) > FIELD_WIDTH/2 or abs(future_loc.y) > FIELD_LENGTH/2:
		# 	print('wall')
		# 	des_ang = Vector3([math.pi/2, angle2D(agent.me, loc), math.pi/2])
		# else:
		# 	print('floor')
		# 	des_ang = Vector3([0, 0, 0])
		
		# # des_ang = find_landing_orientation(agent, 200)

		
		# # print(future_loc)
		# # print(AerialTurn)

		# cs.pitch, cs.yaw, cs.roll = get_req_ypr(agent.me, des_ang)
		# cs.throttle = 1
		# if agent.me.location.x < 60:
		# 	cs.jump = True

		# # print(agent.me.rotation)
		# self.expired = agent.me.car.has_wheel_contact

		
		# return cs