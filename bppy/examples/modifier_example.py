from bppy import *
from bppy.model.event_selection.modifier_event_selection_strategy import \
    ModifierEventSelectionStrategy
from bppy.model.sync_statement import request, waitFor, block, o_request, \
    o_block
from bppy.model import b_modifier


def modifier_select(tickets):
    pass


def b_modifier(func):
    def wrapper(*args):
        while True:
            # print("Enter b_modifier->wrapper")
            m = None
            f = func(*args)
            while True:
                try:
                    # print("b_modifier->wrapper m:", m)
                    e = f.send(m)
                    # print("b_modifier->wrapper received e:", e)
                    m = yield e
                    # print("b_modifier->wrapper received next m:", m)
                    if m is None:
                        break
                except (KeyError, StopIteration):
                    m = yield None
                    break

    return wrapper


@b_thread
def move_forward():
    i = 0
    while i < 1:
        yield {request: BEvent("Accelerate", {'speed': 5}),
               block: BEvent("TurnRight", {'angle': 20})}
        i = i + 1


@b_thread
def turn_right():
    i = 0
    while i < 1:
        yield {request: BEvent("TurnRight", {'angle': 20})}
        i = i + 1


def modify_proxy():
    lastEvent = yield {waitFor: BEvent("Accelerate", {'speed': 5})}
    updated_speed = lastEvent.data['speed'] + 5
    yield {request: BEvent("Accelerate_tag", {'speed': updated_speed})}


def modify_function(observed_events):
    return BEvent("Accelerate", {'speed': 5})


def modify():
    i = 0
    while i < 1:
        print("before modify thread yield...")
        observed_events = yield {o_request: BEvent("Accelerate", {'speed': 5}),
                                 o_block: BEvent("TurnRight", {'speed': 5})}
        print("modify was notified on observed_events", observed_events)
        mod_event = modify_function(observed_events)
        # no returned value because we are only interested to update ESM
        yield {mod_event: mod_event}
        print("modify->proceeding to next synchronization point")
        i = i + 1


def example_without_modifier(bthreads=[]):
    b_program = BProgram(bthreads=bthreads, modifier=[],
                         event_selection_strategy=ModifierEventSelectionStrategy(),
                         listener=PrintBProgramRunnerListener())
    b_program.run()


def example_with_modifier(bthreads=[], modifier=[]):
    b_program = BProgram(bthreads=bthreads, modifier=modifier,
                         event_selection_strategy=ModifierEventSelectionStrategy(),
                         listener=PrintBProgramRunnerListener())
    b_program.run()


if __name__ == "__main__":
    modify_enabled = False
    modify = b_modifier(modify)
    modify_instance = modify()

    if modify_enabled:
        example_with_modifier(
            bthreads=[move_forward(), turn_right(), modify_instance],
            modifier=modify_instance)
    else:
        example_without_modifier(bthreads=[move_forward(), turn_right()])
