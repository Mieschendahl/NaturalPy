from gpt import model
from naturalpy import Config, implement
from example_mean import mean

@implement
def variance(ls: list[float]) -> float:
    """Returns the variance of a function."""
    return Config(model=model, functions=[mean])  # type:ignore

print(variance([1,2,3,4]))  # prints 1.25