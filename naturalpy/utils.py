import inspect
import importlib
import traceback
from typing import Callable, Any
from pathlib import Path
from promptpy import prebuilt

def get_info(function: Callable) -> tuple[str, str, str]:
    """Returns the name, signature, and doc-string of a function.
    
    Returns:
        (name, signature, spec):
            name: The name of the function.
            signature: The signature of the function.
            spec: The doc-string of the function."""
    name = function.__name__
    signature = f"{name}{inspect.signature(function)}"
    spec = function.__doc__ if function.__doc__ else ""
    spec = "\n".join(line.strip() for line in spec.strip().split("\n"))
    return name, signature, spec

def dummy_call(function: Callable) -> Any:
    """Calls a function, by providing None arguments to all of its required arguments, and returns it return value.
    
    Args:
        function: The function.
    
    Returns:
        out: The return value of the function when called with dummy None values.
    """
    params = inspect.signature(function).parameters
    args: list[Any] = []
    kwargs: dict[str, Any]= {}
    for name, param in params.items():
        if param.default == inspect.Parameter.empty:
            if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
                args.append(None)
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                kwargs[name] = None
    return function(*args, **kwargs)

module_name = "__implementation__"
file_path = Path(f"{module_name}.py")

def load(code: str, name: str, objs: list[Any]) -> Callable | str:
    """Dynamically loads a python function from a given code piece.
    
    Args:
        code: The code that contains the function definition.
        name: The name of the function.
        objs: A list of objects that should be overwritten in the module.
        
    Returns:
        out: The function object if the loading process was successful, else an error trace of the
        exception that occurred while loading.
    """
    file_path.write_text(prebuilt.clean_code(code))
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)  # type:ignore
        module = importlib.util.module_from_spec(spec)  # type:ignore
        spec.loader.exec_module(module)
    except Exception as e:
        trace = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        return f"Your implementation caused a syntax error:\n{trace}"
    finally:
        if file_path.is_file():
            file_path.unlink()
    if not hasattr(module, name):
        return f"Your implementation does contain a top level function called \"{name}\""
    for obj in objs:
        if hasattr(obj, "__name__") and obj.__name__ is not None:
            setattr(module, obj.__name__, obj)
    return getattr(module, name)
    
def wrap(wrapped: Callable) -> Callable:
    """Sets the documentation meta-data of an object to the documentation meta data of another object.

    Returns:
        wrapped: The wrapped function.
    """
    def decorator(wrapper: Callable) -> Callable:
        for attr in ("__name__", "__qualname__", "__module__", "__doc__", "__defaults__", "__annotations__"):
            if hasattr(wrapped, attr):
                setattr(wrapper, attr, getattr(wrapped, attr))
        return wrapper
    return decorator