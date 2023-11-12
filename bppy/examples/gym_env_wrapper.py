import gymnasium as gym
import numpy as np
from flask import Flask, request, jsonify
from time import sleep
from taxi_helper import action_to_word

app = Flask(__name__)
env = gym.make("Taxi-v3")
initial_obs = env.reset()
print(f"initial observation: {initial_obs[0]}")

print(gym.__version__)

@app.route('/env_step', methods=['POST'])
def step():
    action = request.json['action']
    state, reward, terminated, truncated, info = env.step(action)
    action_mask = info["action_mask"]
    print(f"state: {state}")
    print(f"terminated: {terminated}")
    env.render()
    sleep(0.1)
    ret_value = jsonify({
        'state': str(state),
        'action_mask': str(action_mask),
        'terminated': str(terminated)
    })
    return ret_value

@app.route('/env_action', methods=['GET'])
def action():
    action = env.action_space.sample()
    action_word  = action_to_word(action)
    print("Action: ", action_word)
    ret_value = jsonify({
        'action': str(action)
    })
    return ret_value

@app.route('/env_reset', methods=['GET'])
def reset():
    initial_obs = env.reset()
    initial_state = initial_obs[0]
    initial_action_mask = initial_obs[1]["action_mask"]
    ret_value = jsonify({
        'state': str(initial_state),
        'action_mask': str(initial_action_mask)
    })
    return ret_value

@app.route('/get-example', methods=['GET'])
def get_request():
    # Your code to handle the "GET" request goes here
    return "This is a GET request response."

if __name__ == '__main__':
    app.run()
