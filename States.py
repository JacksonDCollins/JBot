import math
import time
from Util import *
from substates import *
import Util
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState

from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3 as rlv3, Rotator



class kickOffShot:
	def __init__(self):
		self.expired = False
		self.name = 'kickOffShot'

	def available(self,agent):
		if agent.ball.location.x == 0.0 or agent.ball.location.y == 0.0:
			return True
		return False

	def execute(self, agent):
		self.substate = moveSub()
		agent.controller = kickOffController
		target_location = agent.ball.location
		local_ball = toLocal(agent.ball, agent.me)

		angle_to_ball = math.atan2(local_ball.data[1], local_ball.data[0])
		closest = target_location
		for i in agent.small_boosts:
			local_i = toLocal(i, agent.me)
			if distance2D(agent.me, agent.ball) < distance2D(agent.ball, i):
				continue
			# print(distance2D(i, agent.ball))

			angle_to_boost = math.atan2(local_i.data[1], local_i.data[0])
			angle = angle_to_boost - angle_to_ball
			if angle > -math.radians(15) and angle < math.radians(15):
				# print(distance2D([1,1,1], [2,2,2]))
				if distance2D(agent.me.location, closest) > distance2D(agent.me.location, i):
					closest = i
					target_location = closest

		# print(closest, agent.ball.location)
		target_speed = 5000

		if not agent.ball.location.x + agent.ball.location.y == 0.0:
			self.expired = True

		return agent.controller(agent, target_location, target_speed)

def kickOffController(agent, target_object,target_speed):
	location = toLocal(target_object, agent.me)
	controller_state = SimpleControllerState()
	angle_to_target = math.atan2(location.data[1], location.data[0])

	controller_state.steer = steer(angle_to_target)
	
	controller_state.throttle, controller_state.boost = throttle(agent, target_speed)


	return agent.make_data(controller_state)

class calcShot:
	def __init__(self):
		self.expired = False
		self.name = 'calcShot'

	def available(self,agent):
		if ballReady(agent) and abs(agent.ball.location.data[1]) < 5050 and ballProject(agent) > 500 - (distance2D(agent.ball,agent.me)/2):
			return True
		return False

	def execute(self,agent):
		agent.controller = calcController

		#getting the coordinates of the goalposts
		leftPost = Vector3([(GOAL_WIDTH/2)-BALL_RADIUS,sign(opp(agent.team))*FIELD_LENGTH/2,100])
		rightPost = Vector3([(-GOAL_WIDTH/2)+BALL_RADIUS,sign(opp(agent.team))*FIELD_LENGTH/2,100])
		center = Vector3([0, (FIELD_LENGTH/2)*sign(opp(agent.team)), 200])

		#time stuff that we don't worry about yet
		time_guess = 0
		bloc = future(agent.ball,time_guess)

		#vectors from the goalposts to the ball & to Gosling
		ball_left = angle2D(bloc,leftPost)
		ball_right = angle2D(bloc,rightPost)
		agent_left = angle2D(agent.me,leftPost)
		agent_right = angle2D(agent.me,rightPost)

		#determining if we are left/right/inside of cone
		if agent_left > ball_left and agent_right > ball_right:
			goal_target = rightPost
		elif agent_left > ball_left and agent_right < ball_right:
			goal_target = None
		elif agent_left < ball_left and agent_right < ball_right:
			goal_target = leftPost
		else:
			goal_target = None

		if goal_target != None:
			#if we are outside the cone, this is the same as Gosling's old code
			goal_to_ball = (agent.ball.location - goal_target).normalize()
			goal_to_agent = (agent.me.location - goal_target).normalize()
			difference = goal_to_ball - goal_to_agent
			error = cap(abs(difference.data[0])+ abs(difference.data[1]),1,10)
		else:
			goal_to_ball = (agent.ball.location - center).normalize()
			goal_to_agent = (agent.me.location - center).normalize()
			difference = goal_to_ball - goal_to_agent
			error = cap(abs(difference.data[0])+ abs(difference.data[1]),1,10)
			pass
			#if we are inside the cone, our line to follow is a vector from the ball to us (although it's still named 'goal_to_ball')
			goal_to_ball = (agent.me.location - agent.ball.location).normalize()
			error = cap( distance2D(bloc,agent.me) /1000,0,1)

		#this is measuring how fast the ball is traveling away from us if we were stationary
		ball_dpp_skew = cap(abs(dpp(agent.ball.location, agent.ball.velocity, agent.me.location, [0,0,0]))/80, 1,1.5)

		#same as Gosling's old distance calculation, but now we consider dpp_skew which helps us handle when the ball is moving
		target_distance =cap( (40 + distance2D(agent.ball.location,agent.me)* (error**2))/1.8, 0,4000)
		target_location = agent.ball.location + Vector3([(goal_to_ball.data[0]*target_distance) * ball_dpp_skew, goal_to_ball.data[1]*target_distance,0])

	   #this also adjusts the target location based on dpp
		ball_something = dpp(target_location,agent.ball.velocity, agent.me,[0,0,0])**2
		
		if ball_something > 100: #if we were stopped, and the ball is moving 100uu/s away from us
			ball_something = cap(ball_something,0,80)
			correction = agent.ball.velocity.normalize()
			correction = Vector3([correction.data[0]*ball_something,correction.data[1]*ball_something,correction.data[2]*ball_something])
			target_location += correction #we're adding some component of the ball's velocity to the target position so that we are able to hit a faster moving ball better
			#it's important that this only happens when the ball is moving away from us.

		
		#another target adjustment that applies if the ball is close to the wall
		extra = 4120 - abs(target_location.data[0])
		if extra < 0:
			# we prevent our target from going outside the wall, and extend it so that Gosling gets closer to the wall before taking a shot, makes things more reliable
			target_location.data[0] = cap(target_location.data[0],-4120,4120) 
			target_location.data[1] = target_location.data[1] + (-sign(agent.team)*cap(extra,-500,500))

		#getting speed, this would be a good place to modify because it's not very good
		local_loc = toLocal(target_location, agent.me)

		dist_to_point = distance2D(local_loc, agent.me)
		dist_to_ball = distance2D(agent.ball, agent.me)
		angle_to_point = angle2D(local_loc, agent.me)
		angle_to_ball = angle2D(toLocal(agent.ball, agent.me), agent.me)

		dist_dif = (dist_to_point - dist_to_ball)
		ang_dif =  abs(abs(angle_to_ball) - abs(angle_to_point))

		ang_from_line = abs(angle2D(toLocal(find_point_on_line(target_location, agent.ball, 1/10), agent.me), agent.me))
		
		co = abs(ang_dif - ang_from_line)
		speed = (2000 - (100*(1+ang_dif)**2))*(co/3)
		if agent.team == 1:
			agent.renderer.draw_rect_3d(find_point_on_line(target_location, agent.ball, 1/10).data, 10,10, True, agent.renderer.create_color(255,255,255,255))
			print(speed, ang_dif, ang_from_line, (co/3))

		#picking our rendered target color based on the speed we want to go
		colorRed = cap(int( (speed/2300) * 255),0,255)
		colorBlue =cap(255-colorRed,0,255)

		#see the rendering tutorial on github about this, just drawing lines from the posts to the ball and one from the ball to the target
		# agent.renderer.begin_rendering()
		agent.renderer.draw_line_3d(bloc.data, leftPost.data, agent.renderer.create_color(255,255,0,0))
		agent.renderer.draw_line_3d(bloc.data, rightPost.data, agent.renderer.create_color(255,0,255,0))

		agent.renderer.draw_line_3d(agent.ball.location.data,target_location.data, agent.renderer.create_color(255,colorRed,0,colorBlue))
		agent.renderer.draw_rect_3d(target_location.data, 10,10, True, agent.renderer.create_color(255,colorRed,0,colorBlue))

		if  ballReady(agent) == False:# or abs(agent.ball.location.data[1]) > 5050:
			self.expired = True
		return agent.controller(agent,target_location,abs(speed), co/3)

def calcController(agent, target_object,target_speed, n):
	location = toLocal(target_object,agent.me)
	controller_state = SimpleControllerState()
	angle_to_target = math.atan2(location.data[1],location.data[0])

	current_speed = velocity2D(agent.me)
	

	td = time.time() - agent.start
	if agent.substate.expired:
		if boostSub().cavailable(agent, (distance2D(agent.me, agent.ball) > 2000 and td > 5)):
			agent.substate = boostSub()
		else:
			agent.substate = moveSub()
			if recoverSub().available(agent):
				agent.substate = recoverSub()

	
	return agent.make_data(agent.substate.execute(agent, location, target_speed, controller_state, current_speed, angle_to_target, boost = True,  t = target_object, n = n))

class retreat:
	def __init__(self):
		self.expired = False
		self.name = 'retreat'

	def available(self, agent):
		goal = Vector3([0, sign(agent.team)*FIELD_LENGTH/2, 0])
		if distance2D(agent.ball, goal) < distance2D(agent.me, goal):
			return True
		return False

	def execute(self, agent):
		agent.controller = defenderController
		
		goal = Vector3([0, sign(agent.team)*FIELD_LENGTH/2, 100])

		target_loc = find_point_on_line(goal, agent.ball, 1/3)
		agent.renderer.draw_rect_3d(target_loc.data, 10,10, True, agent.colour)

		target_location = target_loc#Vector3([0, sign(agent.team)*FIELD_LENGTH/2, 0])
		# agent.renderer.draw_rect_3d(goal.data, 10,10, True, agent.renderer.create_color(255,100,50,100))

		# print(closest, agent.ball.location)
		target_speed = 2400

		if distance2D(agent.ball, goal) > distance2D(agent.me, goal) + 300:
			self.expired = True

		return agent.controller(agent, target_location, target_speed)

class defender:
	def __init__(self):
		self.expired = False
		self.name = 'defend'

	def available(self, agent):
		goal = Vector3([0, sign(agent.team)*FIELD_LENGTH/2, 0])
		if sign(agent.team) * agent.ball.location.y > 3000 and distance2D(agent.ball, goal) < distance2D(goal, agent.me):
			return True
		return False

	def execute(self, agent):
		agent.controller = defenderController
		target_location = Vector3([0, sign(agent.team)*FIELD_LENGTH/2, 0])
		goal = Vector3([0, sign(agent.team)*FIELD_LENGTH/2, 0])
		

		# print(closest, agent.ball.location)
		target_speed = 2400

		if distance2D(agent.me.location, target_location) < 1000 or distance2D(agent.ball, goal) > distance2D(agent.me, goal):
			self.expired = True

		return agent.controller(agent,target_location, target_speed)

def defenderController(agent, target_location, target_speed):
	controller_state = SimpleControllerState()
	location = toLocal(target_location, agent.me)
	angle_to_target = math.atan2(location.data[1], location.data[0])
	current_speed = velocity2D(agent.me)

	td = time.time() - agent.start
	if agent.substate.expired:
		if boostSub().cavailable(agent, (td > 2.2 and distance2D(location,agent.me) > (velocity2D(agent.me)*2.3) and abs(angle_to_target) < 1)):
			agent.substate = boostSub()
		else:
			agent.substate = moveSub()
			if recoverSub().available(agent):
				agent.substate = recoverSub()


	return agent.make_data(agent.substate.execute(agent, location, target_speed, controller_state, current_speed, angle_to_target, boost = True,  t = target_location))

class quickShot:
	def __init__(self):
		self.expired = False
		self.name = 'quickShot'

	def available(self,agent):
		if ballProject(agent) > -(distance2D(agent.ball,agent.me)/2):
			return True
		return False

	def execute(self,agent):
		agent.controller = shotController
		left_post = Vector3([(GOAL_WIDTH/2)-BALL_RADIUS,sign(opp(agent.team))*FIELD_LENGTH/2,100])
		right_post = Vector3([(-GOAL_WIDTH/2)+BALL_RADIUS,sign(opp(agent.team))*FIELD_LENGTH/2,100])
		
		ball_left = angle2D(agent.ball.location,left_post)
		ball_right = angle2D(agent.ball.location,right_post)

		our_left = angle2D(agent.me.location,left_post)
		our_right = angle2D( agent.me.location,right_post)

		offset = (agent.ball.location.data[0] / FIELD_WIDTH) * 3.14
		x = agent.ball.location.data[0] +90 * abs(math.cos(offset)) * sign(offset)
		y = agent.ball.location.data[1] + 90 * abs(math.sin(offset)) * sign(agent.team)
		target_location = toLocation([x,y,agent.ball.location.data[2]])

		location = toLocal(target_location,agent.me)
		angle_to_target = math.atan2(location.data[1],location.data[0])
		distance_to_target = distance2D(agent.me, target_location)
		
		tr = turn_radius(velocity2D(agent.me))
		co = abs(tr) - abs(angle_to_target)

		speedCorrection =  ((2+ abs(angle_to_target)**2) * 350)# - (co*300)
		speed = 2400 - speedCorrection

		if self.available(agent) == False:
			self.expired = True
		elif calcShot().available(agent) == True:
			self.expired = True

		return agent.controller(agent,target_location, speed)

def shotController(agent, target_object, target_speed):
	goal_local = toLocal([0,-sign(agent.team)*FIELD_LENGTH/2,100],agent.me)
	goal_angle = math.atan2(goal_local.data[1],goal_local.data[0])

	location = toLocal(target_object,agent.me)
	controller_state = SimpleControllerState()
	angle_to_target = math.atan2(location.data[1],location.data[0])

	current_speed = velocity2D(agent.me)

	td = time.time() - agent.start
	if agent.substate.expired:
		if shotSub().available(agent, target_object):
			agent.substate = shotSub()
		elif boostSub().available(agent, angle_to_target, current_speed, target_speed, location):
			agent.substate = boostSub()
		else:
			agent.substate = moveSub()
			if recoverSub().available(agent):
				agent.substate = recoverSub()


	#dodging

	return agent.make_data(agent.substate.execute(agent, location, target_speed, controller_state, current_speed, angle_to_target, boost = True, goal_angle = goal_angle, t = target_object))

class wait:
	def __init__(self):
		self.expired = False
		self.name = 'wait'

	def available(self, agent):
		if timeZ(agent.ball) > 1.5:
			return True

	def execute(self,agent):
		#taking a rough guess at where the ball will be in the future, based on how long it will take to hit the ground
		ball_future = future(agent.ball, timeZ(agent.ball))

		if agent.me.boost < 35: #if we are low on boost, we'll go for boot
			closest = 0
			closest_distance =  distance2D(agent.BOOSTS[0], ball_future) 

			#going through every large pad to see which one is closest to our ball_future guesstimation
			for i in range(1,len(agent.BOOSTS)):
				if distance2D(agent.BOOSTS[i], ball_future) < closest_distance:
					closest = i
					closest_distance =  distance2D(agent.BOOSTS[i], ball_future)

			target = agent.BOOSTS[closest]
			speed = 2300
		else:
			#if we have boost, we just go towards the ball_future position, and slow down just like in exampleATBA as we get close
			target = ball_future
			current = velocity2D(agent.me)
			ratio = distance2D(agent.me,target)/(current + 0.01)
			
			speed = cap(600 * ratio,0,2300)
		if speed <= 100:
			speed = 0

		if ballReady(agent):
			self.expired = True

		return frugalController(agent,target,speed)

def frugalController(agent,target,speed):
	controller_state = SimpleControllerState()
	location = toLocal(target,agent.me)
	angle_to_target = math.atan2(location.data[1],location.data[0])
	current_speed = velocity2D(agent.me)


	if agent.substate.expired:
		if boostSub().available(agent, angle_to_target, current_speed, speed, location):
			agent.substate = boostSub()
		else:
			agent.substate = moveSub()
			if recoverSub().available(agent):
				agent.substate = recoverSub()


	return agent.make_data(agent.substate.execute(agent, location, speed, controller_state, current_speed, angle_to_target, t = target))

class exampleATBA:
	def __init__(self):
		self.expired = False

	def execute(self, agent):
		target_location = agent.ball
		target_speed = velocity2D(agent.ball) + (distance2D(agent.ball, agent.me))

		return agent.controller(agent, target_location, target_speed)

def exampleController(agent, target_location, target_speed):
		location = toLocal(target_location, agent.me)
		controller_state = SimpleControllerState()
		angle_to_target = math.atan2(location.data[1], location.data[0])

		current_speed = velocity2D(agent.me)
		if angle_to_target > 0.1:
			controller_state.steer = controller_state.yaw = 1
		elif angle_to_target < -0.1:
			controller_state.steer = controller_state.yaw = -1
		else:
			controller_state.steer = controller_state.yaw = 0

		if target_speed > current_speed:
			controller_state.throttle = 1
			if target_speed > 1400 and agent.start > 2.2:
				controller_state.boost = True
		elif target_speed < current_speed:
			controller_state.throttle = 0

		time_difference = time.time() - agent.start
		if time_difference > 2.2 and distance2D(location, agent.me.location) > 3000 and abs(angle_to_target) < 1.3:
			agent.start = time.time()
		elif time_difference <= 0.1:
			controller_state.jump = True
			controller_state.pitch = -1
		elif time_difference >= 0.1 and time_difference <= 0.15:
			controller_state.jump = False
			controller_state.pitch = -1
		elif time_difference > 0.15 and time_difference < 1:
			controller_state.jump = True
			controller_state.yaw = controller_state.steer
			controller_state.pitch = -1

		return controller_state


class testEnviro:
	def __init__(self):
		self.expired = False
		self.name = 'none'

	def execute(self, agent, *args, **vargs):
		
		car_state = CarState(jumped=False, double_jumped=False, boost_amount=87, 
                     physics=Physics(location = rlv3(sign(agent.team)*1000, sign(agent.team)*3000, 0), velocity=rlv3(0,0,0), rotation=rlv3(0,1,0)))

		ball_state = BallState(Physics(location=rlv3(2000, 2000, 0), velocity=rlv3(0,0,0)))

		game_state = GameState(ball=ball_state, cars={agent.index: car_state})

		agent.set_game_state(game_state)
		self.expired = True