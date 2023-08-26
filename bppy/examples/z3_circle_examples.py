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
    # print(f"{str} = {float(solution_x)}, y = {float(solution_y)}")
    check_equations(solution_x, solution_y, m, b)


# Whatever is in block will be negated and added to the solver
@b_thread
def x_above_top_line_solver(m, b):
    x_below_top_line = And(y <= m * x + b)
    for i in range(1):
        last_event = yield {request: true, block: x_below_top_line}
        # print_solution("solution", last_event, m, b)


@b_thread
def x_inside_circle_solver():
    x_outside_of_circle = And(x ** 2 + y ** 2 >= 1)
    for i in range(1):
        last_event = yield {request: true, block: x_outside_of_circle}


@b_thread
def generate_events_scenario(line_equations, delta_param):
    requested_events = []
    x, y = -1.0, -1.0
    while x < 1.0:
        while y < 1.0:
            requested_events.append(BEvent("set", {"x": x, "y": y}))
            y += delta_param
        y = -1.0
        x += delta_param
    last_event = yield {request: requested_events}
    check_equations(Point(last_event.data["x"], last_event.data["y"]), line_equations)


@b_thread
def x_y_inside_circle_discrete():
    yield {block: EventSet(lambda e: e.data["x"] ** 2 + e.data["y"] ** 2 >= 1)}


@b_thread
def x_y_above_line_discrete(m, b):
    yield {block: EventSet(lambda e: e.data["y"] <= m * e.data["x"] + b)}


@b_thread
def x_y_below_line_discrete(m, b):
    yield {block: EventSet(lambda e: e.data["y"] >= m * e.data["x"] + b)}


@b_thread
def y_above_b_discrete(b):
    yield {block: EventSet(lambda e: e.data["y"] <= b)}


@b_thread
def y_below_b_discrete(b):
    yield {block: EventSet(lambda e: e.data["y"] >= b)}


@b_thread
def x_above_x1_discrete(x1):
    yield {block: EventSet(lambda e: e.data["x"] <= x1)}


@b_thread
def x_below_x1_discrete(x1):
    yield {block: EventSet(lambda e: e.data["x"] >= x1)}


def solver_based_example(num_edges=3, radius=1):
    global found_solution_solver
    m, b = create_line_equation(n=num_edges, r=radius)
    # print(f"num_edges = {num_edges}, radius = {radius}, m = {m}, b = {b}")
    b_program = BProgram(
        bthreads=[x_above_top_line_solver(m, b), x_inside_circle_solver()],
        event_selection_strategy=SMTEventSelectionStrategy(),
        listener=PrintBProgramRunnerListener(),
    )
    b_program.run()
    found_solution_solver = b_program.get_found_solution()


def initialize_bthreads_list(line_equations, delta_param=0.1):
    b_threads_list = []
    for line_equation in line_equations:
        if line_equation.get_type() == "y":
            if is_almost_zero(line_equation.get_m()):
                if line_equation.get_b() >= 0:
                    b_threads_list.append(y_above_b_discrete(line_equation.get_b()))
                else:
                    b_threads_list.append(y_below_b_discrete(line_equation.get_b()))
            else:  # M is not zero
                if line_equation.get_m() < 0:
                    b_threads_list.append(
                        x_y_above_line_discrete(
                            line_equation.get_m(), line_equation.get_b()
                        )
                    )
                else:  # M > 0
                    b_threads_list.append(
                        x_y_below_line_discrete(
                            line_equation.get_m(), line_equation.get_b()
                        )
                    )
        else:  # line_equation.get_type() == "x"
            if line_equation.get_x1() >= 0:
                b_threads_list.append(x_above_x1_discrete(line_equation.get_x1()))
            else:  # x1 < 0
                b_threads_list.append(x_below_x1_discrete(line_equation.get_x1()))

    b_threads_list.append(x_y_inside_circle_discrete())
    b_threads_list.append(generate_events_scenario(line_equations, delta_param))
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
    print(f"Discrete event example found soluton:{found_solution_discrete}")


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
    # run_experiment()
