import gymnasium as gym
import numpy as np
import random
from time import sleep

# create Taxi environment
env = gym.make("Taxi-v3", render_mode="human")

# create a new instance of taxi, and get the initial state
for i in range(5):
    state = env.reset()
    print("Initial state:", state)
    s = env.render()  # Set the rendering backend to pyglet
    print(s)
    sleep(1)


sleep(10)
num_steps = 99
for s in range(num_steps+1):
    print(f"step: {s} out of {num_steps}")

    # sample a random action from the list of available actions
    action = env.action_space.sample()

    # perform this action on the environment
    env.step(action)

    # print the new state
    env.render()
    #s = env.render()  # Set the rendering backend to pyglet
    #print(s)

# end this instance of the taxi environment
env.close()