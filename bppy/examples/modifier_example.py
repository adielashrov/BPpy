from bppy import *
from bppy.model.event_selection.modifier_event_selection_strategy import \
    ModifierEventSelectionStrategy
from bppy.model.sync_statement import request, waitFor, block, o_request, \
    o_block


@b_thread
def move_forward():
    i = 0
    while i < 1:
        yield {request: BEvent("Accelerate", {'speed': 5}),
               block: BEvent("TurnRight", {'angle': 20})}
        i = i + 1
    print("Leaving move_forward b_thread...")

@b_thread
def turn_right():
    i = 0
    while i < 1:
        yield {request: BEvent("TurnRight", {'angle': 20})}
        i = i + 1
    print("Leaving turn_right b_thread...")


def modify_proxy():
    lastEvent = yield {waitFor: BEvent("Accelerate", {'speed': 5})}
    updated_speed = lastEvent.data['speed'] + 5
    yield {request: BEvent("Accelerate_tag", {'speed': updated_speed})}


def modify_function(modify_arguments):
    return BEvent("Accelerate", {'speed': 100})


def modify():
    i = 0
    while i < 1:
        print("Before modify thread yield...")
        modify_arguments = yield {o_request: BEvent("Accelerate", {'speed': 5}),
                                 o_block: BEvent("TurnRight", {'speed': 20})}
        print(f"Modify was notified, modify_arguments: {modify_arguments}")
        m_event = modify_function(modify_arguments)
        # no returned value because we are only interested to update ESM
        lastEvent = yield {mod_event: m_event}
        print("Modify->proceed to next yield")
        print(f"lastEvent: {lastEvent}")
        i = i + 1
    print("Leaving modify b_thread...")



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
    modify_enabled = True
    modify = b_thread(modify)
    modify_instance = modify()

    if modify_enabled:
        example_with_modifier(
            bthreads=[move_forward(), turn_right()],
            modifier=[modify_instance])
    else:
        example_without_modifier(bthreads=[move_forward(), turn_right()])
