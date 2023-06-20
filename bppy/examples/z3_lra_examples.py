from math import sqrt
from bppy import *


x, y = Reals('x y')

def z3_example():

    x, y = Reals('x y')
    # First example
    solve([x>=0, x<=10, y>=0, y<=10, y < x-3])

    # Second example
    solve([x>=0, x<=10, y>=0, y<=10, y < x-3, y>(4.5-0.65*x)])

    # Third example
    solve([x>=0, x<=4.546, y>=0, y<=10, y < x-3, y>(4.5-0.65*x)])


def z3_example_2():
    s = SolverFor("QF_NRA")
    x, y = Reals('x y')
    solve([x ** 2 + y ** 2 <= 1, -1.5*y <= 0.5*sqrt(3)*(x-1)])
    # print(s.check())

def z3__int_example_2():
    x, y = Ints('x y')
    s = Solver()
    s.add((x % 4) + 3 * (y / 2) > x - y)
    print(s.sexpr())

@b_thread
def x_range():
    x_range_constraint = And( x>=0, x<=10 )
    for i in range(3):
        yield { block: Not(And( x>=0, x<=10 ))}

@b_thread
def y_range():
    y_range_constraint = And(y >= 0, y <= 10)
    for i in range(3):
        #yield {request: y_range_constraint}
        yield {block: Not(y_range_constraint)}

@b_thread
def y_small_x():
    y_smaller_than_x = And(y < x - 3)
    for i in range(1):
        #yield {request: y_smaller_than_x}
        yield {request: true, block: Not(y_smaller_than_x)}


@b_thread
def y_large_x():
    y_larger_than_x = And(y > (4.5-0.65*x) )
    for i in range(1):
        #yield {request: y_larger_than_x}
        yield { block: Not(y_larger_than_x)}

@b_thread
def x_small_const():
    x_smaller_than_const = And(x < 4.546)
    for i in range(1):
        #yield {request: x_smaller_than_const}
        yield { block: Not(x_smaller_than_const)}

if __name__ == "__main__":
    # z3_example()
    z3_example_2()

    #b_program = BProgram(bthreads=[x_range(), y_range(), y_small_x(),
    #                               y_large_x(), x_small_const()],
    #                     event_selection_strategy=SMTEventSelectionStrategy(),
    #                     listener=PrintBProgramRunnerListener())
    #b_program.run()