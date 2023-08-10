from bppy import *
import gymnasium as gym
from time import sleep

# Global variables
env = gym.make("Taxi-v3", render_mode="human")
# Variables BP
class External(BEvent):
    pass


any_external = EventSet(lambda event: isinstance(event, External))
any_event = EventSet(lambda event: isinstance(event, BEvent))
input_event_set = EventSet(lambda event: isinstance(event, BEvent) and event.name == "input_event")
output_event_set = EventSet(lambda event: isinstance(event, BEvent) and event.name == "output_event")

def demo_taxi_two():
    env = gym.make("Taxi-v3", render_mode="human")
    env.reset()
    # print the environment in the console (text mode)
    env.render()
    sleep(2)


def action_to_word(action):
    if action == 0:
        return "Down"
    elif action == 1:
        return "Up"
    elif action == 2:
        return "Right"
    elif action == 3:
        return "Left"
    elif action == 4:
        return "Pickup"
    elif action == 5:
        return "Dropoff"


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

@b_thread
def start_simulation():
    global env
    initial_obs = env.reset()
    b_program.enqueue_external_event(External("input_event", {"state": initial_obs}))
    while True:
        print("start_simulation->Wait for any event")
        yield {waitFor: All()}

@b_thread
def actuator():
    while True:
        print("actuator->wait for action")
        output_event = yield {waitFor: output_event_set}
        print("actuator->received output_event: ", output_event)
        observation = env.step(output_event.data['action'])
        print("actuator->observation: ", observation)
        b_program.enqueue_external_event(External("input_event", {"state": observation}))

@b_thread
def sensor():
    while True:
        print("sensor->wait for input_event")
        input_event = yield {waitFor: input_event_set}
        print("sensor->received input_event: ", input_event)

def odnn():
    while True:
        print("odnn->wait for input_event")
        input_event = yield {waitFor: input_event_set}
        print("odnn->received input_event: ", input_event)
        action = env.action_space.sample()
        yield {request: BEvent("output_event", {"action": action})}
        print("odnn->requsted output event: ", action_to_word(action))

if __name__ == "__main__":
    b_program = BProgram(
        bthreads=[start_simulation(), sensor(), odnn(), actuator()],
        event_selection_strategy=SimpleEventSelectionStrategy(),
        listener=PrintBProgramRunnerListener(),
    )
    b_program.run()
