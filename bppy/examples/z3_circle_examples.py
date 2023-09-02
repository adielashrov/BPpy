from math import sqrt
from bppy import *
from constraints_generation import *
import timeit

random.seed(42)
x, y = Reals("x y")
found_solution_discrete = False
found_solution_solver = False


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


def check_equations(point, line_equations):
    # print( float(y) , "?>?", float(m*x) + float(b) )
    # print( float(x**2+y**2) , "?<?", 1)
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


def print_solution(str, event, m, b):
    solution_x = event[x].as_fraction()
    solution_y = event[y].as_fraction()
    print(f"{str} = {float(solution_x)}, y = {float(solution_y)}")
    # check_equations(solution_x, solution_y, m, b)


# Whatever is in block will be negated and added to the solver
# TODO: refactor the names of the bthreads
@b_thread
def y_above_top_line_solver(m, b):
    print(f"y_above_top_line_solver: m={m}, b={b}")
    y_above_top_line_solver = And(y > m * x + b)
    yield {request: y_above_top_line_solver}


@b_thread
def y_below_line_solver(m, b):
    print(f"x_y_below_line_solver: m={m}, b={b}")
    y_below_line_solver = And(y < m * x + b)
    yield {request: y_below_line_solver}


@b_thread
def y_above_b_solver(b):
    print(f"y_above_b_solver: b={b}")
    y_above_b = And(y > b)
    yield {request: y_above_b}


@b_thread
def y_below_b_solver(b):
    print(f"y_below_b_solver: b={b}")
    y_below_b = And(y < b)
    yield {request: y_below_b}


@b_thread
def x_above_x1_solver(x1):
    print(f"x_above_x1_solver: x1={x1}")
    x_above_x1 = And(x > x1)
    yield {request: x_above_x1}


@b_thread
def x_below_x1_solver(x1):
    print(f"x_below_x1_solver: x1={x1}")
    # x_below_x1 = And(x >= x1)
    x_below_x1 = And(x < x1)
    yield {request: x_below_x1}


@b_thread
def x_y_inside_circle_solver():
    x_outside_of_circle = And(x ** 2 + y ** 2 >= 1)
    yield {block: x_outside_of_circle}


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
    last_event = yield {request: requested_events}


@b_thread
def x_y_inside_circle_discrete():
    x_outside_of_circle = EventSet(lambda e: e.data["x"] ** 2 + e.data["y"] ** 2 >= 1)
    yield {block: x_outside_of_circle}


@b_thread
def y_above_top_line_discrete_with_bug(m, b):
    print(f"y_above_top_line_discrete: m={m}, b={b}")
    y_above_top_line_discrete = EventSet(lambda e: e.data["y"] > m * e.data["x"] + b)
    if isinstance(y_above_top_line_discrete, Iterable):
        print("y_above_top_line_discrete is iterable")
    yield {request: y_above_top_line_discrete}


@b_thread
def y_above_top_line_discrete(m, b):
    print(f"y_above_top_line_discrete: m={m}, b={b}")
    y_below_top_line_discrete = EventSet(lambda e: e.data["y"] <= m * e.data["x"] + b)
    if isinstance(y_below_top_line_discrete, Iterable):
        print("y_below_top_line_discrete is iterable")
    yield {block: y_below_top_line_discrete}


@b_thread
def x_y_below_line_discrete(m, b):
    yield {request: EventSet(lambda e: e.data["y"] < m * e.data["x"] + b)}


@b_thread
def y_above_b_discrete(b):
    yield {request: EventSet(lambda e: e.data["y"] > b)}


@b_thread
def y_below_b_discrete(b):
    yield {request: EventSet(lambda e: e.data["y"] < b)}


@b_thread
def x_above_x1_discrete(x1):
    yield {request: EventSet(lambda e: e.data["x"] > x1)}


@b_thread
def x_below_x1_discrete(x1):
    yield {request: EventSet(lambda e: e.data["x"] < x1)}


def solver_based_example(num_edges=3, radius=1):
    global found_solution_solver
    line_equations = create_all_line_equations(n=num_edges, r=radius)
    b_threads_list = initialize_bthreads_list(line_equations, discrete_mode=False)
    b_program = BProgram(
        bthreads=b_threads_list,
        event_selection_strategy=SMTEventSelectionStrategy(),
        listener=PrintBProgramRunnerListener(),
    )
    b_program.run()
    found_solution_solver = b_program.get_found_solution()
    print(f"Solver based example found solution:{found_solution_solver}")


def initialize_bthreads_list(line_equations, delta_param=0.1, discrete_mode=True):
    b_threads_list = []
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
                            x_y_below_line_discrete(
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

    if discrete_mode:
        b_threads_list.append(x_y_inside_circle_discrete())
    else:
        b_threads_list.append(x_y_inside_circle_solver())

    if discrete_mode:
        b_threads_list.append(generate_events_scenario(delta_param))

    return b_threads_list


def discrete_event_example(num_edges=3, radius=1, delta_param=0.1):
    global found_solution_discrete
    line_equations = create_all_line_equations(n=num_edges, r=radius)
    b_threads_list = initialize_bthreads_list(line_equations, delta_param)
    b_program = BProgram(
        bthreads=b_threads_list,
        event_selection_strategy=SimpleEventSelectionStrategy(),
        listener=PrintBProgramRunnerListener(),
    )
    b_program.run()
    found_solution_discrete = b_program.get_found_solution()
    print(f"Discrete event example found solution:{found_solution_discrete}")


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


if __name__ == "__main__":
    discrete_event_example(3, 1, 0.1)
    # solver_based_example(3, 1)
# run_experiment()
