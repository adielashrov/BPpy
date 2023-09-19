from math import sqrt
from bppy import *
from constraints_generation import *
import timeit

# Import libraries
import matplotlib.pyplot as plt
import numpy as np

random.seed(42)
x, y = Reals("x y")
found_solution_discrete = False
found_solution_solver = False

x_y_events = []


def generate_x_y_events(x_y_events, delta_param):
    x, y = -1.0, -1.0
    while x < 1.0:
        while y < 1.0:
            x_y_events.append(BEvent("set", {"x": x, "y": y}))
            y += delta_param
        y = -1.0
        x += delta_param


def z3_point_between_triangle_and_circle():
    x, y = Reals("x y")
    solver = Solver()
    solver.add(And(y > (-1 / sqrt(3)) * x + (1 / sqrt(3)), x ** 2 + y ** 2 < 1))
    if solver.check() == sat:
        model = solver.model()
        solution_x = model[x].as_fraction()  # Retrieve the values of the variables
        solution_y = model[y].as_fraction()
        # print(f"x = {float(solution_x)}, y = {float(solution_y)}")
        return solution_x, solution_y


def print_line_equations(line_equations):
    for line_equation in line_equations:
        print(line_equation)


def check_equations(point, line_equations):
    for line_equation in line_equations:
        if line_equation.get_m() >= 0:
            if (
                point.get_y()
                < line_equation.get_m() * point.get_x1() + line_equation.get_b()
            ):
                if point.get_x1() ** 2 + point.get_y() ** 2 <= 1:
                    return True
                return
        if (
            point.get_y()
            > line_equation.get_m() * point.get_x1() + line_equation.get_b()
        ):
            return
    pass


def check_equation(x, y, line_equation, discrete_mode=True):
    val = ""
    if line_equation.get_type() == "y":
        if is_almost_zero(line_equation.get_m()):
            if line_equation.get_b() >= 0:
                # y_above_b_discrete
                if y > line_equation.get_b():
                    val = f"{y} > {line_equation.get_b()}"
            else:
                if y < line_equation.get_b():
                    val = f"{y} < {line_equation.get_b()}"
        else:  # M is not zero
            if line_equation.get_m() < 0:
                if y > (line_equation.get_m() * x + line_equation.get_b()):
                    val = (
                        f"{y} > {line_equation.get_m()} * {x} + "
                        + f"{line_equation.get_b()}"
                    )
            else:  # M > 0
                if y < (line_equation.get_m() * x + line_equation.get_b()):
                    val = (
                        f"{y} < {line_equation.get_m()} * {x} + "
                        + f"{line_equation.get_b()}"
                    )
    else:  # line_equation.get_type() == "x"
        if line_equation.get_x1() >= 0:
            if x > line_equation.get_x1():
                val = f"{x} > {line_equation.get_x1()}"
        else:  # x1 < 0
            if x < line_equation.get_x1():
                val = f"{x} < {line_equation.get_x1()}"
    return val


def print_solution(str, event, m, b):
    solution_x = event[x].as_fraction()
    solution_y = event[y].as_fraction()
    print(f"{str} = {float(solution_x)}, y = {float(solution_y)}")


"""
Solver event selection experiment bThreads
"""


@b_thread
def y_above_top_line_solver(m, b):
    # print(f"y_above_top_line_solver: m={m}, b={b}")
    y_above_top_line_solver = And(y > m * x + b)
    yield {request: y_above_top_line_solver}


@b_thread
def y_below_line_solver(m, b):
    # print(f"x_y_below_line_solver: m={m}, b={b}")
    y_below_line_solver = And(y < m * x + b)
    yield {request: y_below_line_solver}


@b_thread
def y_above_b_solver(b):
    # print(f"y_above_b_solver: b={b}")
    y_above_b = And(y > b)
    yield {request: y_above_b}


@b_thread
def y_below_b_solver(b):
    # print(f"y_below_b_solver: b={b}")
    y_below_b = And(y < b)
    yield {request: y_below_b}


@b_thread
def x_above_x1_solver(x1):
    # print(f"x_above_x1_solver: x1={x1}")
    x_above_x1 = And(x > x1)
    yield {request: x_above_x1}


@b_thread
def x_below_x1_solver(x1):
    # print(f"x_below_x1_solver: x1={x1}")
    # x_below_x1 = And(x >= x1)
    x_below_x1 = And(x < x1)
    yield {request: x_below_x1}


@b_thread
def x_y_inside_circle_solver():
    x_y_outside_circle_constraint = And(x ** 2 + y ** 2 > 1)
    yield {block: x_y_outside_circle_constraint}


@b_thread
def find_equation_for_solution_solver(line_equations, x, y):
    # x_y_in_range = And(x >= -1)
    x_y_in_range = And(x >= -1, x <= 1, y >= -1, y <= 1)
    last_event = yield {waitFor: true}
    x = last_event[x].as_fraction()
    y = last_event[y].as_fraction()
    for line_equation in line_equations:
        solution = check_equation(x, y, line_equation, discrete_mode=False)
        if solution != "":
            print(line_equation)
            print(f"Found solution: {solution}")
            break


@b_thread
def generate_events_scenario(delta_param):
    requested_events = []
    x, y = -1.0, -1.0
    while x < 1.0:
        while y < 1.0:
            requested_events.append(BEvent("set", {"x": x, "y": y}))
            y += delta_param
        y = -1.0
        x += delta_param
    yield {request: requested_events}


@b_thread
def x_y_inside_circle_discrete():
    x_outside_of_circle = EventSet(lambda e: e.data["x"] ** 2 + e.data["y"] ** 2 >= 1)
    yield {waitFor: All(), block: x_outside_of_circle}


@b_thread
def y_above_top_line_discrete(m, b):
    # print(f"y_above_top_line_discrete: m={m}, b={b}")
    y_above_top_line_discrete_lst = list(
        filter(lambda e: e.data["y"] > (m * e.data["x"] + b), x_y_events)
    )
    last_event = yield {request: y_above_top_line_discrete_lst, waitFor: All()}


@b_thread
def y_below_top_line_discrete(m, b):
    # print(f"x_y_below_line_discrete: m={m}, b={b}")
    y_below_top_line_discrete_lst = list(
        filter(lambda e: e.data["y"] < (m * e.data["x"] + b), x_y_events)
    )
    yield {request: y_below_top_line_discrete_lst, waitFor: All()}


@b_thread
def y_above_b_discrete(b):
    # print(f"y_above_b_discrete: b={b}")
    y_above_b_events_lst = list(filter(lambda e: e.data["y"] > b, x_y_events))
    yield {request: y_above_b_events_lst, waitFor: All()}


@b_thread
def y_below_b_discrete(b):
    # print(f"y_below_b_discrete: b={b}")
    y_below_b_discrete_lst = list(filter(lambda e: e.data["y"] < b, x_y_events))
    yield {request: y_below_b_discrete_lst, waitFor: All()}


@b_thread
def x_above_x1_discrete(x1):
    # print(f"x_above_x1_discrete: x1={x1}")
    x_above_x1_discrete_lst = list(filter(lambda e: e.data["x"] > x1, x_y_events))
    yield {request: x_above_x1_discrete_lst, waitFor: All()}


@b_thread
def x_below_x1_discrete(x1):
    # print(f"x_below_x1_discrete: x1={x1}")
    x_below_x1_discrete_lst = list(filter(lambda e: e.data["x"] < x1, x_y_events))
    yield {request: x_below_x1_discrete_lst, waitFor: All()}


@b_thread
def find_equation_for_solution_discrete(line_equations):
    last_event = yield {waitFor: All()}
    x = last_event.data["x"]
    y = last_event.data["y"]
    for line_equation in line_equations:
        solution = check_equation(x, y, line_equation)
        if solution != "":
            print(line_equation)
            print(f"Found solution: {solution}")
            break


"""
Initialize the solver based example BProgram
"""


def solver_based_example(num_edges=3, radius=1):
    global found_solution_solver
    line_equations = create_all_line_equations(n=num_edges, r=radius)
    print_line_equations(line_equations)
    b_threads_list = initialize_bthreads_list(line_equations, discrete_mode=False)
    b_program = BProgram(
        bthreads=b_threads_list,
        event_selection_strategy=SMTEventSelectionStrategy(),
        listener=PrintBProgramRunnerListener(),
    )
    b_program.run()
    # found_solution_solver = b_program.get_found_solution()
    # print(f"Solver based example found solution:{found_solution_solver}")


def initialize_bthreads_list(line_equations, delta_param=0.1, discrete_mode=True):
    b_threads_list = []

    if discrete_mode:
        b_threads_list.append(x_y_inside_circle_discrete())
    else:
        b_threads_list.append(x_y_inside_circle_solver())

    for line_equation in line_equations:
        if line_equation.get_type() == "y":
            if is_almost_zero(line_equation.get_m()):
                if line_equation.get_b() >= 0:
                    if discrete_mode:
                        b_threads_list.append(y_above_b_discrete(line_equation.get_b()))
                    else:
                        b_threads_list.append(y_above_b_solver(line_equation.get_b()))
                else:
                    if discrete_mode:
                        b_threads_list.append(y_below_b_discrete(line_equation.get_b()))
                    else:
                        b_threads_list.append(y_below_b_solver(line_equation.get_b()))
            else:  # M is not zero
                if line_equation.get_m() < 0:
                    if discrete_mode:
                        b_threads_list.append(
                            y_above_top_line_discrete(
                                line_equation.get_m(), line_equation.get_b()
                            )
                        )
                    else:
                        b_threads_list.append(
                            y_above_top_line_solver(
                                line_equation.get_m(), line_equation.get_b()
                            )
                        )
                else:  # M > 0
                    if discrete_mode:
                        b_threads_list.append(
                            y_below_top_line_discrete(
                                line_equation.get_m(), line_equation.get_b()
                            )
                        )
                    else:
                        b_threads_list.append(
                            y_below_line_solver(
                                line_equation.get_m(), line_equation.get_b()
                            )
                        )
        else:  # line_equation.get_type() == "x"
            if line_equation.get_x1() >= 0:
                if discrete_mode:
                    b_threads_list.append(x_above_x1_discrete(line_equation.get_x1()))
                else:
                    b_threads_list.append(x_above_x1_solver(line_equation.get_x1()))
            else:  # x1 < 0
                if discrete_mode:
                    b_threads_list.append(x_below_x1_discrete(line_equation.get_x1()))
                else:
                    b_threads_list.append(x_below_x1_solver(line_equation.get_x1()))

    # if discrete_mode:
    #     b_threads_list.append(find_equation_for_solution_discrete(line_equations))
    # else:
    #    b_threads_list.append(find_equation_for_solution_solver(line_equations, x, y))

    return b_threads_list


"""
Initialize the discrete based example BProgram
"""


def discrete_event_example(num_edges=3, radius=1, delta_param=0.1):
    global found_solution_discrete
    global x_y_events
    generate_x_y_events(x_y_events, delta_param)
    line_equations = create_all_line_equations(n=num_edges, r=radius)
    print_line_equations(line_equations)
    b_threads_list = initialize_bthreads_list(line_equations, delta_param)
    b_program = BProgram(
        bthreads=b_threads_list,
        event_selection_strategy=SimpleEventSelectionStrategy(),
        listener=PrintBProgramRunnerListener(),
    )
    b_program.run()
    # found_solution_discrete = b_program.get_found_solution()
    # print(f"Discrete event example found solution:{found_solution_discrete}")


def extend_setup_with_variables(setup, n, r, delta):
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
    print(
        "num_of_edges\texecution_time_discrete\tdelta_param\tdiscrete_solved\texecution_time_solver\tsolver_solved"
    )
    for n in range(3, 50):
        delta = 0.1
        c_setup = extend_setup_with_variables(setup, n, 1, delta)
        # print("Started discrete event example")
        execution_time_discrete = timeit.timeit(
            "discrete_event_example(num_edges=n,radius=r,delta_param=d)",
            setup=c_setup,
            number=1,
        )
        while not found_solution_discrete:
            delta = delta / 10
            c_setup = extend_setup_with_variables(setup, n, 1, delta)
            execution_time_discrete = timeit.timeit(
                "discrete_event_example(num_edges=n,radius=r,delta_param=d)",
                setup=c_setup,
                number=1,
            )

        # print("Started solver based example")
        execution_time_solver = timeit.timeit(
            "solver_based_example(num_edges=n,radius=r)", setup=c_setup, number=1
        )
        print(
            f"{n}\t{execution_time_discrete}\t{delta}\t{found_solution_discrete}\t{execution_time_solver}\t{found_solution_solver}"
        )


def plotting_equations():

    # Creating vectors X and Y
    x = np.linspace(-2, 2, 100)
    y = x ** 2

    fig = plt.figure(figsize=(10, 5))
    # Create the plot
    plt.plot(x, y)

    # Show the plot
    plt.show()


if __name__ == "__main__":
    # discrete_event_example(10000, 1, 0.95)
    solver_based_example(3, 1)
# run_experiment()
