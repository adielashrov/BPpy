# Import math Library
from math import pi,sin,cos


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