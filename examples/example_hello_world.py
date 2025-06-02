from gpt import model
from naturalpy import Config, implement

@implement
def hello_world() -> None:
    """Prints "Hello World!" in german."""
    return Config(model=model)  # type:ignore

hello_world()  # prints "Hallo Welt!"