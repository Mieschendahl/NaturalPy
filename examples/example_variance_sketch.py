from gpt import model
from naturalpy import Config, implement
from example_mean import mean

@implement
def variance(ls: list[float]) -> float:
    sketch = """
    # TODO: if ls is empty then return 0

    m = mean(ls)
    new_ls = [(e - m)**2 for e in ls]

    # TODO: return mean of new_ls
    """
    return Config(model=model, functions=[mean], sketch=sketch)  # type:ignore

print(variance([1,2,3,4]))  # prints 1.25