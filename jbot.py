import utils
import states
import structs
import substates
import gc
import time
import math
from PID import PID

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from structs import Game
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3 as rlv3, Rotator

TEST = True

class Steamroller(BaseAgent):
	def initialize_agent(self):
		self.game_info = Game(self, self.index, self.team)
		self.state = None
		self.start = time.time()
		self.dodgeTimer = time.time()
		self.tcount = 0
		self.packet = None
		self.touch = 0

	def get_output(self, game: GameTickPacket) -> SimpleControllerState:
		self.renderer.begin_rendering()

		self.packet = game
		self.game_info.read_packet(self, game)
		self.state = states.pick_state(self)
		
		self.tcount += 1
		if time.time() - self.start >= 1:
			print(self.tcount)
			self.start = time.time()
			self.tcount = 0

		if TEST:
			if not self.game_info.ball.location.x == -1000.0:## if not self.touch == self.game_info.ball.latest_touch.time_seconds:
				self.touch = self.game_info.ball.latest_touch.time_seconds
				self.state = testState(self)

		controls = self.state.execute()
		self.renderer.draw_string_3d(self.game_info.my_car.location.tuple, 2, 2, f'{self.state.name}, {self.state.substate.name}', self.renderer.white())
		self.renderer.end_rendering()
		return controls

class Twiddle():
	def __init__(self):
		self.p = [0,0,0]
		self.dp = [1,1,1]
		self.best_err = None
		self.stage = 1
		self.first = True
		self.stage = 1
		self.cp = 0

	def calculate(self, err):
		if self.first:
			self.first = False
			return self.p

		if self.best_err == None:
			self.best_err = err

		if not self.first:
			if self.stage == 1:
				self.p[self.cp] += self.dp[self.cp]
				self.stage = 2
				return self.p
				
			if self.stage == 2:
				if err < self.best_err:
					self.best_err = err
					self.dp[self.cp] *= 1.1
					self.stage = 1
				else:
					self.p[self.cp] -= 2*self.dp[self.cp]
					self.stage = 3
					return self.p
				
			if self.stage == 3:
				if err < self.best_err:
					self.best_err = err
					self.dp[self.cp] *= 1.1
					self.stage = 1
				else:
					self.p[self.cp] += self.dp[self.cp]
					self.dp[self.cp] *= 0.9
					self.stage = 4


			if self.stage == 4:
				self.stage = 1
				self.cp += 1
				if self.cp >= 3:
					self.cp = 0
				self.best_err = None
				return self.p
				
		return self.p

	
class testState():
	def __init__(self, agent):
		self.name = 'TEST'
		self.action = None
		self.agent = agent
		self.car = self.agent.game_info.my_car
		self.ball = self.agent.game_info.ball
		self.hierarchy = [substates.move]
		self.substate = substates.default()
		self.expired = False
	
	def update(self, agent):
		self.car = self.agent.game_info.my_car
		self.ball = self.agent.game_info.ball


	def execute(self):
		
		car_state = CarState(jumped=False, double_jumped=False, boost_amount=87, 
                     physics=Physics(location = rlv3(1000, 2000, 20), velocity=rlv3(0,0,0), rotation=rlv3(0,0,0), angular_velocity=rlv3(0,0,0)))

		ball_state = BallState(Physics(location=rlv3(-1000, -1100, 100), velocity=rlv3(0,0,0), rotation=rlv3(0,0,0), angular_velocity=rlv3(0,0,0)))

		game_state = GameState(ball=ball_state, cars={self.agent.index: car_state})

		self.agent.set_game_state(game_state)
		self.expired = True
	
		self.substate = substates.pick_state(self, self.agent, self.car, self.ball.location, 2300, self.hierarchy)# Drive(self.car, target, 2000)
		return self.substate.step(1.0/60.0)