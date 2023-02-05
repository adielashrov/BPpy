from bppy import *
from bppy.model.event_selection.modifier_event_selection_strategy import ModifierEventSelectionStrategy
from bppy.model.sync_statement import request,waitFor,block,o_request,o_block
from bppy.model import b_modifier

def modifier_select(tickets):
    pass

def b_modifier(func):
    def wrapper(*args):
        while True:
            print("Enter b_modifier->wrapper")
            m = None
            f = func(*args)
            while True:
                try:
                    print("b_modifier->wrapper m:", m)
                    e = f.send(m)
                    print("b_modifier->wrapper received e:", e)
                    m = yield e
                    print("b_modifier->wrapper received next m:", m)
                    if m is None:
                        break
                except (KeyError, StopIteration):
                    m = yield None
                    break
    return wrapper

@b_thread
def move_forward():
    i = 0
    while i < 3:
        yield {request: BEvent("Accelerate", {'speed':5})}
        i = i + 1

@b_thread
def turn_right():
    i = 0
    while i < 3:
        yield {request: BEvent("TurnRight", {'angle': 20})}
        i = i + 1

def modify_proxy():
    lastEvent = yield {waitFor: BEvent("Accelerate", {'speed':5})}
    updated_speed = lastEvent.data['speed'] + 5
    yield {request: BEvent("Accelerate_tag", {'speed':updated_speed})}

def modify():
    i = 0
    while i < 3:
        lastEvent = yield {o_request: BEvent("Accelerate", {'speed': 5})}
        print("modify observed event", lastEvent)
        i = i + 1

if __name__ == "__main__":
    modify = b_modifier(modify)

    b_program = BProgram(bthreads=[move_forward(), turn_right(), modify()],
                         modifier=[modify()],
                         event_selection_strategy=ModifierEventSelectionStrategy(),
                         listener=PrintBProgramRunnerListener())
    b_program.run()
