"""
This is module a.
"""

from ..b import b_func

a = "this is file 'a'"


def a_func():
    inside_a_func = 'inside a_func()'
    b_func()
    print("a")
