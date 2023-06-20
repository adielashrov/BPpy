from math import sqrt
from bppy import *
import constraints_generation
import timeit

random.seed(42)
x, y = Reals('x y')
found_solution_discrete = False
found_solution_solver = False
def z3_point_between_triangle_and_circle():
    x, y = Reals('x y')
    solver = Solver()
    solver.add( And(y > (-1/sqrt(3))*x + (1/sqrt(3)), x**2+y**2 < 1) )
    if solver.check() == sat:
        model = solver.model()
        solution_x = model[x].as_fraction() # Retrieve the values of the variables
        solution_y = model[y].as_fraction()
        # print(f"x = {float(solution_x)}, y = {float(solution_y)}")
        return solution_x, solution_y

def check_equations(x, y, m, b):
    # print( float(y) , "?>?", float(m*x) + float(b) )
    # print( float(x**2+y**2) , "?<?", 1)
    pass

def print_solution(str, event, m, b):
    solution_x = event[x].as_fraction()
    solution_y = event[y].as_fraction()
    # print(f"{str} = {float(solution_x)}, y = {float(solution_y)}")
    check_equations(solution_x, solution_y, m, b)

# Whatever is in block will be negated and added to the solver
@b_thread
def x_above_top_line_solver(m,b):
    x_below_top_line = And(y <= m*x + b)
    for i in range(1):
        last_event = yield { request: true, block: x_below_top_line}
        # print_solution("solution", last_event, m, b)

@b_thread
def x_inside_circle_solver():
    x_outside_of_circle = And(x**2 + y**2 >= 1)
    for i in range(1):
        last_event = yield { request: true, block: x_outside_of_circle }

@b_thread
def generate_events_scenario(m,b,d):
    requested_events = []
    delta = d
    x, y = 0.0, 0.0
    while x < 1.0:
        while y < 1.0:
            requested_events.append(BEvent("set", {"x": x, "y": y}))
            y += delta
        y = 0.0
        x += delta

    last_event = yield {request: requested_events}
    check_equations(last_event.data["x"], last_event.data["y"], m, b)

@b_thread
def x_y_inside_circle_discrete():
    yield {block: EventSet(lambda e: e.data["x"]**2 + e.data["y"]**2 >= 1)}

@b_thread
def x_y_above_line_discrete(m, b):
    yield {block: EventSet(lambda e: e.data["y"] <= m * e.data["x"] + b)}

def solver_based_example(num_edges=3, radius=1):
    global found_solution_solver
    m, b = constraints_generation.create_line_equation(n=num_edges, r=radius)
    # print(f"num_edges = {num_edges}, radius = {radius}, m = {m}, b = {b}")
    b_program = BProgram(bthreads=[x_above_top_line_solver(m, b), x_inside_circle_solver()],
                         event_selection_strategy=SMTEventSelectionStrategy(),
                         listener=PrintBProgramRunnerListener())
    b_program.run()
    found_solution_solver = b_program.get_found_solution()

def discrete_event_example(num_edges=3, radius=1,delta=0.1):
    global found_solution_discrete
    m, b = constraints_generation.create_line_equation(n=num_edges, r=radius)
    # print(f"num_edges = {num_edges}, radius = {radius}, m = {m}, b = {b}")
    b_program = BProgram(bthreads=[ generate_events_scenario(m, b, delta),
                                   x_y_above_line_discrete(m,b),
                                   x_y_inside_circle_discrete() ],
                         event_selection_strategy=SimpleEventSelectionStrategy(),
                         listener=PrintBProgramRunnerListener())
    b_program.run()
    found_solution_discrete = b_program.get_found_solution()

def extend_setup_with_variables(setup,n,r,delta):
    setup += "n=" + str(n) + "\n"
    setup += "r=" + str(r) + "\n"
    setup += "d=" + str(delta) + "\n"
    return setup

def run_experiment():
    global delta
    setup = """
from __main__ import solver_based_example, discrete_event_example
found_solution_discrete = False
found_solution_solver = False
"""
    print("num_of_edges\texecution_time_discrete\tdelta\tdiscrete_solved\texecution_time_solver\tsolver_solved")
    for n in range(3, 50):
        delta = 0.1
        c_setup = extend_setup_with_variables(setup, n, 1, delta)
        # print("Started discrete event example")
        execution_time_discrete = timeit.timeit(
            'discrete_event_example(num_edges=n,radius=r,delta=d)',
            setup=c_setup, number=1)
        while not found_solution_discrete:
            delta = delta / 10
            c_setup = extend_setup_with_variables(setup, n, 1, delta)
            execution_time_discrete = timeit.timeit('discrete_event_example(num_edges=n,radius=r,delta=d)',setup=c_setup, number=1)

        # print("Started solver based example")
        execution_time_solver = timeit.timeit('solver_based_example(num_edges=n,radius=r)',setup=c_setup, number=1)
        print(f"{n}\t{execution_time_discrete}\t{delta}\t{found_solution_discrete}\t{execution_time_solver}\t{found_solution_solver}")

if __name__ == "__main__":
    run_experiment()
