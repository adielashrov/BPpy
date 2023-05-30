import gymnasium as gym
from time import sleep

environment = gym.make("FrozenLake-v1", render_mode="human",  is_slippery=False)
environment.reset()
environment.render()

sleep(10)