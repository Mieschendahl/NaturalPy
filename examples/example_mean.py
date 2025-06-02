from gpt import model
from naturalpy import Config, implement

@implement
def mean(ls: list[float]) -> float:
    """Returns the mean of a list of floats."""
    return Config(model=model)  # type:ignore

print(mean([1,2,3]))  # prints 2.0