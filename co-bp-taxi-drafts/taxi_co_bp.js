/*
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

*/

/**
Req. 2:	When the taxi is at a certain state = (taxi_location, passenger_location,destination_location) 
		calculate the next best action to reach the Destination
		Ask for this action (Left,Right,Up,Down)
***/

// Business logic


ctx.bthread("MoveTaxiTowardsDestination", "EnvState", 
	function(state) {
		dnn_input = ConvertStateToDNNInput(state)
		possible_output_events = dnn(action)
		sync({
			request: possible_output_events, block: AllInputEvents()
		})
	}
})


/**
Req 3 - Passenger requests to pickup luggage from the red station
**/

bthread("PickupLuggageSensor", 
	function(){
		while(true){
			waitForExternalNotificationOnLuggage()
			sync({
				request: Event("pickup_luggage")
			})
			var ctxEndedEvent = CTX.ContextEndedEvent("ReachedRedStation");
			while(true) {
				var ball = bp.sync({waitFor: StateUpdate.ANY, interrupt: ctxEndedEvent}).ball;
			}
	}
)}

/**
Example for navigating a robot forward with co-bp
**/

	ctx.registerQuery('Robot', function (entity) {
		return entity.type==='Robot'
	})

	ctx.bthread('MoveForward', 'Robot',
	  function (robot) {
		while (true) {
			sync({ 	waitFor: InputEvent('FrontIsClear', robot.id)})
			sync({ 	request: Event('Forward', robot.id), 
					waitFor: Event('Left', robot.id)})
		}
	})
	