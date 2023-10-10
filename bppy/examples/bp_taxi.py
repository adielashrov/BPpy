from typing import Dict, Tuple
from bppy import *
import gymnasium as gym
import numpy as np
from time import sleep
from taxi_helper import *

# Setup a random seed
np.random.seed(0)

# Global variables
env = gym.make("Taxi-v3", render_mode="human")

# Variables BP
class External(BEvent):
    pass

any_external = EventSet(lambda event: isinstance(event, External) and event.name == "ex_input_event")
any_event = EventSet(lambda event: isinstance(event, BEvent))
all_events_except_input_and_output = EventSet(lambda event: isinstance(event, BEvent) and event.name != "input_event" and event.name != "output_event")
input_event_set = EventSet(lambda event: isinstance(event, BEvent) and event.name == "input_event")
input_event_proxy_set = EventSet(lambda event: isinstance(event, BEvent) and event.name == "input_event_proxy")
input_event_proxy_set_or_start_new_destination = EventSet(lambda event: isinstance(event, BEvent) and (event.name == "input_event_proxy" or event.name == "start_new_destination"))
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

def location_to_string(location):
    if location == 0:
        return "Red"
    elif location == 1:
        return "Green"
    elif location == 2:
        return "Yellow"
    elif location == 3:
        return "Blue"
    elif location == 4:
        return "InTaxi"

@b_thread
def start_simulation(state_dict):
    global env
    state, info = env.reset()
    taxi_row, taxi_col, passenger_location, original_destination = state_dict[state] # destination
    print(f"start_simulation: start_passenger_location: "
          f"{location_to_string(passenger_location)}", )
    external_input_event = External("ex_input_event", {"state": state})
    b_program.enqueue_external_event(external_input_event)
    print("Start simulation: enqueued external_input_event", )
    while True:
        yield {waitFor: All()}


@b_thread
def sensor():
    id = 0
    while True:
        # print("sensor->wait for external_input_event_set")
        external_event = yield {waitFor: any_external}
        # print("sensor->received external_input_event: ", external_event)
        yield {request: BEvent("input_event_proxy", {"state": external_event.data['state'], "id": id}),
               block: any_external}
        id += 1

def odnn(state_dict, q_table):
    while True:
        # print("odnn->wait for input_event")
        input_event = yield {waitFor: input_event_set}
        # print("odnn->received input_event: ", input_event)
        state = input_event.data['state']
        action = np.argmax(q_table[state])
        output_event = BEvent("output_event",
                              {"action": action,
                                    "id": input_event.data['id']})
        yield {request: output_event,
               block: all_events_except_input_and_output }
        # print("odnn->requested output event: ", action_to_word(action))
        # composite_state = q_table[input_event.data['state'][0]] # state is a tuple
        # print("odnn->current state taxi_row, taxi_col, passenger_location, #destination: ", composite_state)
@b_thread
def actuator():
    while True:
        # print("actuator->wait for output_event")
        output_event = yield {waitFor: output_event_set}
        action = output_event.data['action']
        # print("actuator->received action: ", action_to_word(action))
        next_state, reward, terminated, truncated, info = env.step(action)
        # print("actuator->state: ", next_state)
        if terminated:
            print("actuator->terminated episode")
            state, info = env.reset()
            print(f"actuator: initial state: {state}, info: {info}", )
            external_input_event = External("ex_input_event", {"state": state})
            b_program.enqueue_external_event(external_input_event)
        else:
            b_program.enqueue_external_event(External("ex_input_event", {"state": next_state}))


'''The following scenario identifies the passenger was picked up by the taxi'''
def identify_passenger_pickup(state_dict):
    while True:
        passenger_picked_up = False
        output_event = yield {waitFor: output_event_set}
        previous_action = action_to_word(output_event.data['action'])
        input_event = yield {waitFor: input_event_set}
        current_passenger_location = extract_passenger_location_from_input_event(input_event,
                                                                      state_dict)
        # print(f"previous_action: {previous_action}, "
        #       f"current_passenger_location: {current_passenger_location}")
        if previous_action == "Pickup" and current_passenger_location == 4:
            passenger_picked_up = True
            yield {request: BEvent("passenger_picked_up")}
            while passenger_picked_up:
                yield {waitFor: BEvent("passenger_dropped_off")}
                passenger_picked_up = False


def extract_passenger_location_from_input_event(input_event, state_dict):
    state = input_event.data['state']
    composite_state = state_dict[state]
    passenger_location = composite_state[2]
    return passenger_location


'''The following bthread notifies that the passenger has forgotten her luggage at
 the original passenger location
 Precondition: the passenger was picked up by the taxi
 '''
def forgot_luggage_sensor():
    forgot_luggage_state = False
    while True:
        yield {waitFor: BEvent("passenger_picked_up")}
        while not forgot_luggage_state:
            '''draw number in random 0.1'''
            if np.random.rand() < 0.1:
                forgot_luggage_state = True
                yield {request: BEvent("forgot_luggage") }
                while forgot_luggage_state:
                    yield {waitFor: BEvent("pickup_luggage")}
                    forgot_luggage_state = False


def forgot_luggage_scenario(state_dict):
    input_event = yield {waitFor: input_event_set}
    passenger_original_location = extract_passenger_location_from_input_event(input_event, state_dict)
    while True:
        yield {waitFor: BEvent("forgot_luggage")}
        yield {request: BEvent("start_new_destination", {"dest": passenger_original_location})}
        yield {waitFor: BEvent("passenger_dropped_off")}

'''This method extracts the state from the input event
It then converts it to the composite state tuple
'''
def extract_state_from_input_event(input_event, state_dict):
    state = input_event.data['state']
    composite_state = state_dict[state]
    return composite_state



def update_event_destination(input_event, new_destination):
    taxi_row, taxi_col, passenger_location, original_destination = extract_state_from_input_event(input_event, state_dict)
    new_gym_state = ((taxi_row * 5 + taxi_col) * 5 + \
                 passenger_location) * 4 + new_destination
    return new_gym_state

def override_sensor():
    override_destination = False  # This override and proxy scenario resemble the yield/restore scenarios from Aurora
    current_destination = None
    while True:
        last_event = yield {waitFor: input_event_proxy_set_or_start_new_destination}
        if last_event.name == "start_new_destination":
            current_destination = last_event.data["dest"]
            override_destination = True
        else:  # event is input_event_proxy
            if not override_destination:  # pass as-is
                state = last_event.data['state']
            else:  # override the current state
                state = update_event_destination(last_event, current_destination)
            id = last_event.data['id']
            yield {request: BEvent("input_event",
                                   {"state": state, "id": id})}


'''The following bthread overrides the navigation to the 
passenger destination
We will now navigate to the passenger original location

def override_navigation_to_passenger_location():
    override_navigation = False
    while True:
        # wait for the original passenger location
        # wait for the forgot luggage event
        # navigate to the original passenger location
        # How do we achieve this?
        # We override the input_event - turns into a proxy event
        pass

'''


if __name__ == "__main__":
    q_table = np.load('11_31_29_08_2023_q_table.npy')
    state_dict = init_state_dict_to_composite_state()
    b_program = BProgram(
    bthreads = [start_simulation(state_dict), sensor(), override_sensor(), identify_passenger_pickup(state_dict),
                forgot_luggage_sensor(), forgot_luggage_scenario(state_dict), odnn(state_dict, q_table), actuator()],
        event_selection_strategy=SimpleEventSelectionStrategy(),
        listener=PrintBProgramRunnerListener(),
    )
    b_program.run()