import substates
import math
import time
import utils
from structs import Vector3

def pick_state(agent):
	if agent.state == None:
		 return ATBA(agent)
	if agent.state.expired:
		hierarchy = [kickOff, defend, retreat, calcShoot, quickShoot]#, ATBA]
		for state in hierarchy:
			if state(agent).available():
				return state(agent)
	agent.state.update(agent)
	return agent.state

class retreat():
	def __init__(self, agent):
		self.name = 'RETREAT'
		self.action = None
		self.agent = agent
		self.car = self.agent.game_info.my_car
		self.ball = self.agent.game_info.ball
		self.hierarchy = [substates.recover, substates.dodge, substates.move]
		try:
			self.substate = agent.state.substate
		except:
			self.substate = substates.default()
		self.expired = False

		
	def update(self, agent):
		self.car = self.agent.game_info.my_car
		self.ball = self.agent.game_info.ball

	def available(self):
		goal = self.agent.game_info.my_goal.location
		if utils.distance2D(self.ball.location, goal) < utils.distance2D(self.car.location, goal):
			return True
		return False
	
	def execute(self):
		goal = self.agent.game_info.my_goal.location
		

		target =  utils.find_point_on_line(goal, self.ball.location, 1/3)
		speed = 2400

		if utils.distance2D(self.ball.location, goal) > utils.distance2D(self.car.location, goal) + utils.turn_radius(self.car) *1.5 :
			self.expired = True

		self.substate = substates.pick_state(self, self.agent, self.car, target, speed, self.hierarchy)# Drive(self.car, target, 2000)
		return self.substate.step(1.0/60.0)

class defend():
	def __init__(self, agent):
		self.name = 'DEFEND'
		self.action = None
		self.agent = agent
		self.car = self.agent.game_info.my_car
		self.ball = self.agent.game_info.ball
		self.hierarchy = [substates.recover, substates.dodge, substates.move]
		try:
			self.substate = agent.state.substate
		except:
			self.substate = substates.default()
		self.expired = False

			
	def update(self, agent):
		self.car = self.agent.game_info.my_car
		self.ball = self.agent.game_info.ball
	
	def available(self):
		goal = self.agent.game_info.my_goal.location
		if utils.sign(self.agent.team) * self.ball.location.y > 3000 and utils.distance2D(self.ball.location, goal) < utils.distance2D(goal, self.car.location):
			return True
		return False

	def execute(self):
		target = self.agent.game_info.my_goal.location
		speed = 2400

		if utils.distance2D(self.car.location, target) < 1000 or utils.distance2D(self.ball.location, target) > utils.distance2D(self.car.location, target):
			self.expired = True

		self.substate = substates.pick_state(self, self.agent, self.car, target, speed, self.hierarchy)# Drive(self.car, target, 2000)
		return self.substate.step(1.0/60.0)

class kickOff():
	def __init__(self, agent):
		self.name = 'KICKOFF'
		self.action = None
		self.agent = agent
		self.car = self.agent.game_info.my_car
		self.ball = self.agent.game_info.ball
		self.hierarchy = [substates.recover, substates.move]
		try:
			self.substate = agent.state.substate
		except:
			self.substate = substates.default()
		self.expired = False

	def update(self, agent):
		self.car = self.agent.game_info.my_car
		self.ball = self.agent.game_info.ball

	def available(self):
		if self.ball.location.x == self.ball.location.y:
			return True
		return False

	def execute(self):
		self.expired = self.available()

		target = self.ball
		angle_to_target = utils.angle2D(target.location, self.car)
		
		closest = target
		for boost in self.agent.game_info.boosts:
			if utils.distance2D(target.location, self.car.location) < utils.distance2D(boost.location, target.location):
				continue
			
			angle_to_boost = utils.angle2D(boost.location, self.car)
			angle_dif = angle_to_target - angle_to_boost

			if abs(angle_dif) < math.radians(15):
				if utils.distance2D(closest.location, self.car.location) > utils.distance2D(boost.location, self.car.location):
					closest = boost
					
		target = closest.location
		self.substate = substates.pick_state(self, self.agent, self.car, target, 2300, self.hierarchy)# Drive(self.car, target, 2000)
		
		return self.substate.step(1.0/60.0)

class ATBA():
	def __init__(self, agent):
		self.name = 'ATBA'
		self.action = None
		self.agent = agent
		self.car = self.agent.game_info.my_car
		self.ball = self.agent.game_info.ball
		self.hierarchy = [substates.recover, substates.shoot, substates.dodge, substates.move]
		try:
			self.substate = agent.state.substate
		except:
			self.substate = substates.default()
		self.expired = False

	
	def update(self, agent):
		self.car = self.agent.game_info.my_car
		self.ball = self.agent.game_info.ball

	def available(self):
		return True
	
	def execute(self):
		# print(self.car)
		self.substate = substates.pick_state(self, self.agent, self.car, self.ball.location, 2400, self.hierarchy)
		self.expired = True
		return self.substate.step(1.0/60.0)

class quickShoot():
	def __init__(self, agent):
		self.name = 'QUICKSHOOT'
		self.action = None
		self.agent = agent
		self.car = self.agent.game_info.my_car
		self.ball = self.agent.game_info.ball
		self.hierarchy = [substates.recover, substates.shoot, substates.dodge, substates.move]
		try:
			self.substate = agent.state.substate
		except:
			self.substate = substates.default()
		self.expired = False
	
	def update(self, agent):
		self.car = self.agent.game_info.my_car
		self.ball = self.agent.game_info.ball

	def available(self):
		return True
		# print(utils.ballProject(self), -(utils.distance2D(self.ball.location, self.car.location)/2))
		if utils.ballProject(self) > -(utils.distance2D(self.ball.location, self.car.location)/2):
			return True
		return False
	
	def execute(self):
		target = self.ball.location
		offset = (target.x / utils.FIELD_WIDTH) * math.pi
		x = target.x + 90 * abs(math.cos(offset)) * utils.sign(offset)
		y = target.y + 90 * abs(math.sin(offset)) * utils.sign(self.agent.team)
		# target = Vector3(x,y,target.z)

		
		

		self.substate = substates.pick_state(self, self.agent, self.car, target, 2400, self.hierarchy)
		self.expired = (not utils.ballProject(self) > -(utils.distance2D(self.ball.location, self.car.location)/2) or (calcShoot(self.agent).available()))
		return self.substate.step(1.0/60.0)

class calcShoot():
	def __init__(self, agent):
		self.name = 'CALCSHOOT'
		self.action = None
		self.agent = agent
		self.car = self.agent.game_info.my_car
		self.ball = self.agent.game_info.ball
		self.hierarchy = [substates.recover, substates.dodge, substates.move]
		try:
			self.substate = agent.state.substate
		except:
			self.substate = substates.default()
		self.expired = False
	
	def available(self):
		return False
		if utils.ballReady(self) and abs(self.ball.location.y) < 5050 and utils.ballProject(self) > 500 - (utils.distance2D(self.ball.location, self.car.location)/2):
			return True
		return False
	
	def update(self, agent):
		self.car = self.agent.game_info.my_car
		self.ball = self.agent.game_info.ball

	def execute(self):
		#getting the coordinates of the goalposts
		target_location = self.ball.location
		leftPost = self.agent.game_info.their_goal.left_post
		rightPost = self.agent.game_info.their_goal.right_post
		center = self.agent.game_info.their_goal.location

		

		self.substate = substates.pick_state(self, self.agent, self.car, target_location, 2400, self.hierarchy)
		if utils.ballReady(self) == False or abs(self.ball.location.y) > 5050:
			self.expired = True
		return self.substate.step(1.0/60.0)
