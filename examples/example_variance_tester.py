from gpt import model
from naturalpy import Config, Tester, implement
from example_mean import mean

@implement
def variance(ls: list[float]) -> float:
    """Returns the variance of a function."""
    tester = Tester()\
            .check([], equals=0)\
            .check([1], equals=0)\
            .check([1,2], equals=0.25)\
            .check([1,2,3], equals=2/3, tolerance=1e-9)
    return Config(model=model, functions=[mean], tester=tester)  # type:ignore

print(variance([1,2,3,4]))  # prints 1.25