# Import math Library
from math import pi, sin, cos

from z3 import is_and, is_or


class Point:
    def __init__(self, x, y):
        self.__x = x
        self.__y = y

    def get_x(self):
        return self.__x

    def get_y(self):
        return self.__y

    def __str__(self):
        return f"(x={self.get_x()}, y={self.get_y()})"


class Line_Equation:
    def __init__(self, m=0.0, b=0.0, type="y", x=None):
        self.__m = m
        self.__b = b
        self.__type = type
        self.__x = x

    def get_m(self):
        return self.__m

    def get_b(self):
        return self.__b

    def get_type(self):
        return self.__type

    def get_x1(self):
        return self.__x

    def __str__(self):
        if self.get_type() == "y":
            return f"(m={self.get_m()}, b={self.get_b()})"
        else:
            return f"(x={self.get_x1()})"


def create_line_equation(n=3, r=1):
    # calculate two adjacent points on the circle with radius r
    x_1, y_1 = r * cos(0), r * sin(0)
    x_2, y_2 = r * cos(2 * pi / n), r * sin(2 * pi / n)
    # calculate the slope of the line
    m = (y_2 - y_1) / (x_2 - x_1)
    # calculate the y-intercept of the line
    b = y_1 - m * x_1
    # return the slope and y-intercept
    return m, b


def is_almost_zero(value, epsilon=1e-9):
    return abs(value) < epsilon


def create_all_line_equations(n=3, r=1):
    points = []
    line_equations = []
    step_size = 2 * pi / n
    for i in range(n):
        points.append(Point(r * cos(i * step_size), r * sin(i * step_size)))

    for j in range(n):
        next_index = (j + 1) % n
        diff_x = points[next_index].get_x() - points[j].get_x()
        if is_almost_zero(diff_x):
            line_equations.append(Line_Equation(type="x", x=points[j].get_x()))
        else:
            m = (points[next_index].get_y() - points[j].get_y()) / diff_x
            b = points[j].get_y() - m * points[j].get_x()
            line_equations.append(Line_Equation(m, b))

    return line_equations


def count_constraints(expr):
    if is_and(expr) or is_or(expr):
        # For AND and OR expressions, recursively count constraints in sub-expressions
        count = 0
        for sub_expr in expr.children():
            count += count_constraints(sub_expr)
        return count
    else:
        # For atomic constraints, return 1
        return 1
