from typing import Dict, Tuple
from bppy import *
import gymnasium as gym
import numpy as np
from time import sleep
from taxi_helper import *

# Global variables
env = gym.make("Taxi-v3", render_mode="human")

# Variables BP
class External(BEvent):
    pass


any_external = EventSet(lambda event: isinstance(event, External))
any_event = EventSet(lambda event: isinstance(event, BEvent))
external_input_event_set = EventSet(lambda event: isinstance(event, External) and event.name == "input_event")
input_event_set = EventSet(lambda event: isinstance(event, BEvent) and event.name == "input_event")
output_event_set = EventSet(lambda event: isinstance(event, BEvent) and event.name == "output_event")

def demo_taxi_two():
    env = gym.make("Taxi-v3", render_mode="human")
    env.reset()
    # print the environment in the console (text mode)
    env.render()
    sleep(2)


def demo_taxi_navigation():
    # create Taxi environment
    env = gym.make("Taxi-v3", render_mode="human")
    initial_obs = env.reset()
    print(f"initial observation: {initial_obs[0]}")
    num_steps = 10
    for s in range(num_steps + 1):
        print(f"step: {s} out of {num_steps}")
        # sample a random action from the list of available actions
        # TODO: how to get the list of available actions with probabilities?
        action = env.action_space.sample()
        print("Action: ", action_to_word(action))
        # perform this action on the environment
        observation = env.step(action)
        print(f"observation: {observation[0]}")
        env.render()
        sleep(1)

    # end this instance of the taxi environment
    env.close()

def init_state_dict_to_composite_state():
    state_dict: dict[int, tuple[int, int, int, int]] = {}
    for taxi_row in range(5):
        for taxi_col in range(5):
            for passenger_location in range(5):
                for destination in range(4):
                    gym_state = ((taxi_row * 5 + taxi_col) * 5 + \
                                 passenger_location) * 4 + destination
                    composite_state = (taxi_row, taxi_col, \
                                       passenger_location, destination)
                    state_dict[gym_state] = composite_state
    return state_dict


@b_thread
def start_simulation():
    global env
    initial_obs, info = env.reset()
    print(f"start_simulation: initial_obs: {initial_obs}, info: {info}", )
    external_input_event = External("input_event", {"state": initial_obs})
    b_program.enqueue_external_event(external_input_event)
    print("Start simulation: enqueued external_input_event", )
    #while True:
    #    yield {waitFor: All()}


@b_thread
def sensor():
    while True:
        print("sensor->wait for external_input_event_set")
        external_input_event = yield {waitFor: external_input_event_set}
        print("sensor->received external_input_event_set: ", external_input_event)

def odnn(state_dict, q_table):
    while True:
        # print("odnn->wait for input_event")
        input_event = yield {waitFor: input_event_set}
        # print("odnn->received input_event: ", input_event)
        # composite_state = q_table[input_event.data['state'][0]] # state is a tuple
        #print("odnn->current state taxi_row, taxi_col, passenger_location, #destination: ", composite_state)
        sleep(1)
        action = env.action_space.sample()
        yield {request: BEvent("output_event", {"action": action}),
               block: input_event_set }
        # print("odnn->requsted output event: ", action_to_word(action))

@b_thread
def actuator():
    while True:
        # print("actuator->wait for action")
        output_event = yield {waitFor: output_event_set}
        print("actuator->received action: ", \
              action_to_word(output_event.data['action']))
        observation = env.step(output_event.data['action'])
        # print("actuator->observation: ", observation)
        b_program.enqueue_external_event(External("input_event", {"state": observation}))

if __name__ == "__main__":
    q_table = np.load('11_31_29_08_2023_q_table.npy')
    state_dict = init_state_dict_to_composite_state()
    b_program = BProgram(
    bthreads = [start_simulation(), sensor()],
        event_selection_strategy=SimpleEventSelectionStrategy(),
        listener=PrintBProgramRunnerListener(),
    )
    b_program.run()

'''bthreads=[start_simulation(), sensor(), odnn(state_dict, q_table), actuator()],'''