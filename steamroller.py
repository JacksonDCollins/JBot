import math
import time
import numpy as np
from Util import *
from States import *

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.game_state_util import GameState
from rlbot.utils.game_state_util import BallState, CarState, Physics, Vector3 as rlv3, Rotator
from RLUtilities.GameInfo import GameInfo



class Steamroller(BaseAgent):
	def initialize_agent(self):
		#This runs once before the bot starts up
		self.game_info = GameInfo(self.index, self.team)
		self.me = None
		self.ball = None
		self.players = []
		self.start = time.time()
		self.state = kickOffShot()
		self.substate = moveSub()
		self.controller = kickOffController
		self.active = False
		self.per_goal_training = []
		self.lastgoal = 0
		self.owngoals = 0
		self.test = 0
		
	def checkState(self):
		self.test += 1
		if self.test > 1 and not self.test < 0:
			self.test = -500
			self.state = calcShot()
			testEnviro().execute(self)			
		# if self.me.car.has_wheel_contact:
		# 	self.state = wait()
		# 	self.substate = moveSub()
		# 	testEnviro().execute(self)

		if self.state.expired:
			if kickOffShot().available(self) == True:
				self.state = kickOffShot()
			elif retreat().available(self) == True:
				self.state = retreat()
				if defender().available(self) == True:
					self.state = defender()
			elif calcShot().available(self) == True:
				self.state = calcShot()
			elif quickShot().available(self) == True:
				self.state = quickShot()
			elif wait().available(self) == True:
				self.state = wait()
				if defender().available(self) == True:
					self.state = defender()
			else:
				self.state = calcShot()

	def get_output(self, game: GameTickPacket) -> SimpleControllerState:
		self.game_info.read_packet(game)
		self.renderer.begin_rendering()
		try: 
			draw_debug(self.renderer, game.game_cars[self.index], game.game_ball, f'{self.state.name}, {self.substate.name}')
		except:
			pass
		self.check_goal(game)
		self.preprocess(game)
		self.checkState()
		state =  self.state.execute(self)
		self.renderer.end_rendering()
		return state

	def check_goal(self, game):
		ginfo = game.game_info
		if not self.active == ginfo.is_round_active:
			print(self.active)
			self.active = ginfo.is_round_active
			if not self.active: #goal score - false
				self.state = kickOffShot()
				self.substate = moveSub()
				if game.game_cars[self.index].score_info.goals > self.lastgoal:
					self.lastgoal = game.game_cars[self.index].score_info.goals

					total_own_goals = 0
					for i in range(game.num_cars):
						if i != self.index:
							total_own_goals += game.game_cars[i].score_info.own_goals

					if total_own_goals > self.owngoals:
						self.owngoals = total_own_goals
					else:
						to_save = self.per_goal_training.copy()
						np.save(f'D:/rocketLeague/games/{game.game_cars[self.index].score_info.goals}-{len(self.per_goal_training)}-{time.time()}.npy', to_save)

			else:	#round start - True
				self.per_goal_training = []
				self.state = kickOffShot()

	def make_data(self, controller_state):
		cs = controller_state
		controller_vals = [rmap(cs.throttle, -1, 1), rmap(cs.steer, -1, 1), rmap(cs.pitch, -1, 1), rmap(cs.yaw, -1, 1), rmap(cs.roll, -1, 1), int(cs.jump == True), int(cs.boost == True), int(cs.handbrake == True)]
		me_vals = [self.me.glocation(), self.me.grotation(), [rmap(self.me.boost, 0, 100)]*3]
		player_vals = [[x.glocation(), x.grotation(), [rmap(x.boost, 0, 100)]*3] for x in self.players]
		ball_vals = [self.ball.glocation(), self.ball.grotation(), [rmap(self.ball.boost, 0, 100)]*3]
		# print(ball_vals)
		if self.active:
			vals = []
			vals.append(me_vals)
			for i in player_vals:
				vals.append(i)
			vals.append(ball_vals)
			self.per_goal_training.append([vals, controller_vals])
		# print(len(self.per_goal_training))
		return cs

	def preprocess(self, game):

		self.colour = self.renderer.create_color(255,self.team*255,0,opp(self.team)*255)
		self.me = obj(self, game.game_cars[self.index])
		self.me.car = game.game_cars[self.index]
		self.me.boost = game.game_cars[self.index].boost
		self.ball = obj(self, game.game_ball)
		self.ball.local_location = to_local(self.ball, self.me)

		self.BOOSTS = [Vector3(x.location) for x in self.get_field_info().boost_pads if x.is_full_boost]
		self.small_boosts = [Vector3(x.location) for x in self.get_field_info().boost_pads if not x.is_full_boost]
		self.players = []
		for i in range(game.num_cars):
			if i != self.index:
				car = game.game_cars[i]
				temp = obj(self, car)
				temp.index = i
				temp.team = car.team
				self.players.append(temp)

		# print(self.players[0].location, self.players[1].location)


def draw_debug(renderer, car, ball, action_display):
	
	# draw a line from the car to the ball
	# renderer.draw_line_3d(car.physics.location, ball.physics.location, renderer.white())
	# print the action that the bot is taking
	renderer.draw_string_3d(car.physics.location, 2, 2, action_display, renderer.white())
	# t = Vector3(car.physics.location) - Vector3([0,0,-20])
	# renderer.draw_string_3d((t.x,t.y,t.z), 2, 2, d, renderer.white())
	# renderer.end_rendering()
