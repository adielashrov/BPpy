import gymnasium as gym
import numpy as np
import random
from time import sleep

def demo_taxi_two():
    env = gym.make('Taxi-v3', render_mode="human")
    env.reset()
    # print the environment in the console (text mode)
    env.render()
    sleep(2)

def print_action(action):
    if action == 0:
        print("Down")
    elif action == 1:
        print("Up")
    elif action == 2:
        print("Right")
    elif action == 3:
        print("Left")
    elif action == 4:
        print("Pickup")
    elif action == 5:
        print("Dropoff")

def demo_taxi_navigation():

    # create Taxi environment
    env = gym.make("Taxi-v3", render_mode="human")
    initial_obs = env.reset()
    print(f"initial observation: {initial_obs[0]}")
    num_steps = 10
    for s in range(num_steps+1):
        print(f"step: {s} out of {num_steps}")

        # sample a random action from the list of available actions
        action = env.action_space.sample()
        print_action(action)
        # perform this action on the environment
        observation = env.step(action)
        print(f"observation: {observation[0]}")
        env.render()
        sleep(1)

    # end this instance of the taxi environment
    env.close()


if __name__ == '__main__':
    demo_taxi_navigation()