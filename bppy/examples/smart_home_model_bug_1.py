import time
from bppy import *
import numpy as np

# Fixate the random seed
np.random.seed(0)
# Bug here that we can solve with printing every synchronization point statements.
input_event_set = EventSet(lambda event: event.name == "input_event")
output_event_set = EventSet(lambda event: event.name == "output_event")
##################################################
# Req 1 - Implement the sensor and actuator - we need the input/output events in other scenarios
##################################################
def random_choice(probability):
    draw = np.random.random_sample()
    if draw > probability:
        return True
    return False


@b_thread
def audio_sensor():
    id = 0
    input_events = [
        BEvent("input_event", {"data": "sound_1"}),
        BEvent("input_event", {"data": "sound_2"}),
        BEvent("input_event", {"data": "sound_3"}),
    ]
    while True:
        time.sleep(0.2)
        requested_event = np.random.choice(input_events)
        requested_event.data["id"] = id
        last_event = yield {request: requested_event}
        print("Sensor requested: ", last_event)
        id += 1


@b_thread
def odnn_scenario():
    while True:
        input_event = yield {waitFor: input_event_set}
        data = input_event.data["data"]
        id = input_event.data["id"]
        last_event = yield {
            request: BEvent("output_event", {"data": data, "id": id}),
            block: input_event_set,
        }
        print("ODNN_requested:", last_event)


def audio_actuator():
    while True:
        output_event = yield {waitFor: output_event_set}
        print("Actuator received: ", output_event)


if __name__ == "__main__":
    b_program = BProgram(
        bthreads=[audio_sensor(), odnn_scenario(), audio_actuator()],
        event_selection_strategy=SimpleEventSelectionStrategy(),
        listener=PrintBProgramRunnerListener(),
    )
    b_program.run()
