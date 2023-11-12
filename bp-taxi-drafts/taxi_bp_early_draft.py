##################################################
###### A story of enhancing the taxi example #####
##################################################

#   +---------+
#    0 1 2 3 4
# 0 |R: | : :G|
# 1 | : | : : |
# 2 | : : : : |
# 3 | | : | : |
# 4 |Y| : |B: |
#   +---------+

# Taxi story - 
# Origin - green station
# Destination - red station
# Fuel - yellow station

##################################################
# Req 1 - Implement the sensor and actuator - we need the input/output events in other scenarios  
# possible_output_events could be: [down, up,right,left,pickup, Dropoff]

def sensor():
    while True:
        state = waitForCurrentStateFromEnv()
        yield { request: BEvent("InputEvent", {"state": state}) }
        
def actuator():
    while True:
        last_event = yield { waitFor: BEvent("OutputEvent", {"action": action})}
        env.step(last_event.data["action"])

def taxi_dnn():
    while True:
        state = yield { waitFor: AllInputEvents() }
        action = env.action_space.sample()
        possible_output_events = turnIntoVector(action)
        yield { request: possible_output_events, block: AllInputEvents() }


# Req 2 - When the fuel_low light is on, refuel in the Red station, and then proceed with the navigation to the passenger destination
def fuel_taxi_scenario():
    while True:
        yield { waitFor: BEvent("fuel_low") }
        yield { request: BEvent("req_new_destination", {"dest": "yellow"}) }
        while True:
            yield { waitFor: BEvent("InputEvent", {"state": (4,0)}) }
            yield { request: BEvent("fuel_taxi"), block: allEventsBesides("??") } # what to block ?
            yield { request: BEvent("end_new_destination", {"dest": "yellow"} ), block: allEventsBesides("???") }
            break

# Req 2.1 - Fuel sensor - version 2 - use break
def fuel_mode():
    while True:
        waitForExternalNotificationOnFuel()
        yield { request: BEvent("fuel_low"), block: AllInputEvents() }
        while True:
            yield { waitFor: BEvent("end_fuel", {"dest" : "yellow"}) }
            break


'''
# Req 4 - We would like to model an announcement by a b-thread on the current destination - v3
'''
def announce_new_destination():
    while True:
        last_event = yield { waitFor: BEvent("req_new_destination") }
        dest_stack.append(last_event.data["dest"])
        while len(dest_stack) > 0:
            last_event = yield { request: BEvent("start_new_dest", { "dest": dest_stack[len(dest_stack) - 1] } ),
                    waitFor: BEvent("req_new_destination")
                    block: allEventsBesides("start_new_dest") } # Repeating pattern the all_events besides. Simple solution - event set?
            if last_event.getType() == "req_new_destination" and updated_destination(last_event): 
                dest_stack.append(last_event.data["dest"])



'''
# Req 4.1 - to support the idea that one scenario is responsiable for navigation to new dest
# What about mutual exclusion?
'''
global dest_stack = []

'''
# Req 6 Now that there is a new destination
# A natuarl requirement will be to refelct this change in the current state
# We want to override the input from the sensor scenario
# We will use a proxy event - adujsted the sensor
'''
def sensor():
    while True:
        state = waitForCurrentStateFromEnv()
        yield { request: BEvent("InputEventProxy", {"state": state}) }

'''
TODO: Add support for the end_ navigation scenario
'''
def override_sensor():
    override_destination = False # This override and proxy scenario resemble the yield/restore scenarios from Aurora
    current_destination = null
    while True:
        last_event = yield { waitFor: [ BEvent("start_new_dest"), 
                                        BEvent("InputEventProxy") ]}
        if last_event.getType() == "start_new_dest":
            current_destination = last_event.data["dest"]
            override_destination = True
        else: # event is InputEventProxy
            if not override_destination: # pass as-is
                yield { request: BEvent("InputEvent", {"state": getState(last_event)}) }
            else: # override the current state
                yield { request: BEvent("InputEvent", {"state": updateEventDestination(last_event, current_destination)}) }
           

#   +---------+
#    0 1 2 3 4
# 0 |R: | : :G|
# 1 | : | : : |
# 2 | : :x: : |
# 3 | | : | : |
# 4 |Y| : |B: |
#   +---------+
'''
Req - Each square is responsiable for its own overrdie (when the destination is changed)
'''
def square_scenario_2_2():
    while True:
        last_event = yield { waitFor: BEvent("start_new_dest") }
        new_dest = last_event.data["dest"]
        while True:
            last_event = yield { waitFor: [ BEvent("InputEvent", {"state": (2,2)}) , BEvent("end_new_dest") ]}
            if check_if_end_new_dest(last_event, new_dest):
                break
            if new_dest == "green":
                last_event = yield { waitFor: [  BEvent("OutputEvent", {"action": "right"}), BEvent("OutputEvent", {"action": "up"}),  
                                                    BEvent("end_new_dest")  ], # best_practice - wait for an event that breaks mode 
                                        block: [    BEvent("OutputEvent", {"action": "left"}), 
                                                    BEvent("OutputEvent", {"action": "down"}),
                                                    BEvent("OutputEvent", {"action": "pickup"}),
                                                    BEvent("OutputEvent", {"action": "dropoff"})] } # or allOutputEventsBesides("right","up")
                if check_if_end_new_dest(last_event, new_dest):
                    break
            elif new_dest == "yellow":
                last_event = yield { waitFor: [  BEvent("OutputEvent", {"action": "left"}), BEvent("OutputEvent", {"action": "down"}),  
                                                    BEvent("end_new_dest")  ], # best_practice - wait for an event that breaks mode 
                                        block: [    BEvent("OutputEvent", {"action": "right"}), 
                                                    BEvent("OutputEvent", {"action": "up"}),
                                                    BEvent("OutputEvent", {"action": "pickup"}),
                                                    BEvent("OutputEvent", {"action": "dropoff"})] } # or allOutputEventsBesides("left","down")
                if check_if_end_new_dest(last_event, new_dest):
                    break
            else:
                print("You should select a new destination")
                


# Problem - if we allow non-determinisim in the override of directions by the square
# The taxi could be stuck in a livelock 
# For example, if sqaure (3,2) enables the output event up to reach the yellow destination 
# We can recive a cycle of (Down,up,Down) when we override and navigate to the yellow destination 
# Req 5.1 - Passenger forget luggage at source
def forget_luggage_sensor():
    while True:
        waitForExternalNotificationOnLuggage()
        yield { request: BEvent("forget_luggage"), block: AllInputEvents() }
        while True:
            yield { waitFor: BEvent("reached_new_destination", {"dest" : "green"}) }
            break
            
# Req 5 - Passenger forgot luggage at source - green
# Same pattern as the fuel scenario? 
def return_passenger_to_source_scenario():
    while True:
        yield { waitFor: BEvent("forget_luggage") }
        yield { request: BEvent("req_new_destination", {"dest": "green"}) }
        while True:
            yield { waitFor: BEvent("InputEvent", {"state": (0,4)}) }
            yield { request: BEvent("pickup_luggage"), block: allEventsBesides("??") } # what to block ?
            yield { request: BEvent("end_new_destination", {"dest": "green"} ), block: allEventsBesides("???") }
            break




# Req 4 - We would like to extract the navigation ending to a different scenario
def announce_end_destination():
    dest_stack = []
    while True:
        start_new_dest_event = yield { waitFor: BEvent("start_new_dest") }
       # we can check if the new_destination is less important and operate as a queue (and not as a system with interrupts).
        dest_stack.append(start_new_dest_event.data["dest"])
        while len(dest_stack) > 0:
            last_event = yield { waitFor: BEvent("req_end_destination") }
            if last_event.getType() == "req_end_destination" and
                last_event.data["dest"] == dest_stack[len(dest_stack) - 1]:
                dest_stack.pop()
                
                
'''
Scenarios for PPT and tasks
'''

    def scenario_2():
        while True:
             yield { waitFor: BEvent("InputEvent", {"state": (2,3)}) }
             yield { request: [BEvent("Left"),BEvent("Right")], 
                     block: [BEvent("Up")] }
             break