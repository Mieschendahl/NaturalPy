from dataclasses import dataclass
from typing import Callable, Optional, TextIO
from promptpy import Model, Prompter, Option
from naturalpy.utils import get_info, load, wrap, dummy_call
from naturalpy.tester import Null, Tester

class ImplementationError(Exception):
    """A custom Exception for the Implementer class."""

@dataclass
class Config:
    """Represents a implementation configuration for the Implementer class.
    
    Attributes:
        mode: The model to be used for generating the implementation.
        doc: A doc-string that will overwrite the default doc-string of the function.
        sketch: A sketch of the function implemtation that should be passed to the model.
        functions: An optional list of functions that the model should use without implementing.
        max_attemps: Maximum number of attempts that the model has to generate a valid implementation.
        log_file: The file to save the implementation logs to, or None to not generate any logs.
            Use sys.stdout for printing to stdout.
        allow_injects: If the use can inject prompts before every model response.
        id: An id for the prompter.
    """
    model: Model
    doc: Optional[str] = None
    sketch: Optional[str] = None
    functions: Optional[list[Callable]] = None
    max_attempts: Optional[int] = None
    tester: Optional[Tester] = None
    log_file: Optional[TextIO] = None
    allow_injections: bool = False
    id: Optional[str] = None

class Implementer:
    """Implements function using LLMs."""
    
    def __init__(self, function: Callable, config: Config):
        """Implementer constructor. Throws an ImplementationError if the given function can not be implemented.
        
        Args:
            function: The function to implement via an LLM.
            config: Contains the implementation configuration.
        """
        self.function = function
        self.config = config
        if self.config.doc is not None:
            function.__doc__ = self.config.doc
        self.name, self.signature, self.doc = get_info(function)
        self.sketch = self.config.sketch
        self.functions = [] if self.config.functions is None else self.config.functions
        self.tester = self.config.tester
        self.max_attempts = self.config.max_attempts

        self.prompter = Prompter(model=self.config.model, log_file=self.config.log_file, allow_injections=self.config.allow_injections, id=self.config.id)\
            .add_message(
                "You are a python expert who should help the user implement a python function."
                "\nNever use libraries outside of python's standard library!",
                role="developer"
            )\
            .add_message(
                f"Please implement the function \"{self.name}\" for me:"
                f"\nSignature: {self.signature}"
                f"\nSpecification: {self.doc}"
            )
            
        if self.sketch is not None and self.sketch != "":
            sketch = "\n".join("    "+line.strip() for line in self.sketch.strip().split("\n"))
            self.prompter.add_message(
                "Here is a sketch of how the function should be implemented:\n"
                f"\ndef {self.signature}:\n{sketch}"
            )
            
        if len(self.functions) > 0:
            message = f"Use the following helper functions without defining them, I will later implement them for you:\n"
            for function in self.functions:                
                _, signature, spec = get_info(function)
                message += (
                    f"\nSignature: {signature}"
                    f"\nSpecification: {spec}"
                )
            self.prompter.add_message(message)

        self.implementation: Optional[Callable] = None
        self.implement()

    def implement(self, *messages: str) -> None:
        """Main loop for implementing functions.
        
        Args:
            messages: Any additional messages that should be passed to the Model for feedback purposes.
        """
        attempt = 0
        while True:
            if self.max_attempts is not None and attempt >= self.max_attempts:
                raise ImplementationError(f"The model failed to implement function \"{self.name}\" in {self.max_attempts} iterations")
            attempt += 1
            choice = self.prompter\
                .add_message(*messages)\
                .add_message(
                    "Think step by step about how to implement the function."
                    "\nAlso consider if the function can not be implemented because of an impossible specification."
                )\
                .add_response()\
                .get_choice(
                    Option(
                        "implement",  # label
                        "If you have found an implementation",  # condition
                        "Write your implementation and nothing else, not even examples",  # action
                        "I will give you feedback on whether your implementation is correct" # effect
                    ),
                    Option(
                        "impossible",  # label
                        "If you have found a reason why the function can not be implemented",  # condition
                        "Write your reason",  # action
                        "I will give you feedback on whether your reasoning is correct"  # effect
                    )
                )
            match choice:
                case "impossible", reason:
                    raise ImplementationError(
                        f"The LLM determined that the function \"{self.name}\" is impossible to implement because: {reason}"
                    )
                case "implement", code:
                    obj = load(code, self.name, self.functions)
                    if isinstance(obj, str):
                        self.prompter.add_message(obj)
                        continue
                    self.implementation = wrap(self.function)(obj)
                    errors = self.test_implementation()
                    if len(errors) > 0:
                        self.prompter.add_message(
                            "Your implementation contains mistakes:\n"
                            + "\n".join(f"{i+1}. {error}" for i, error in enumerate(errors))
                            )
                        continue
                    break
                
    def test_implementation(self) -> list[str]:
        """Tests the function implementation
            
        Returns:
            errors: A list of test error descriptions to be passed to the Implementer.
        """
        assert self.implementation is not None, "Can not test without an implementation."

        errors = []
        if self.tester is None:
            return errors
        
        for args in self.tester.runs_tests:
            call = f"{self.name}(" + ", ".join(repr(arg) for arg in args) + ")"
            try:
                self.implementation(*args)
            except Exception as e:
                errors.append(f"{call} raised an unexpected {type(e)} error")
        
        for args, expected, tolerance in self.tester.equals_tests:
            call = f"{self.name}(" + ", ".join(repr(arg) for arg in args) + ")"
            try:
                predicted = self.implementation(*args)
                if isinstance(tolerance, Null):
                    error = predicted != expected
                else:
                    error = abs(predicted - expected) > tolerance
                if error:
                    errors.append(f"{call} should return {expected!r} but returned {predicted} instead")
            except Exception as e:
                errors.append(f"{call} should return {expected!r} but raised {type(e)} instead")
                
        for args, expected in self.tester.raises_tests:
            call = f"{self.name}(" + ", ".join(repr(arg) for arg in args) + ")"
            try:
                predicted = self.implementation(*args)
                errors.append(f"{call} should raise {expected!r} but returned {predicted} instead")
            except Exception as e:
                if not isinstance(e, expected):
                    errors.append(f"{call} should raise {expected!r} but raised {type(e)} instead")
        return errors

def implement(function: Callable) -> Callable:
    """A decorator for automatically implementing functions using their signatures and doc-strings.
    Passes the function and the return value of the function to an Implementer.
    
    Args:
        function: The function to implement.
            The function should return ImplementationConfig object when called with dummy values.

    Returns:
        implemented: The implemented function.
    """
    config = dummy_call(function)
    assert isinstance(config, Config), "Function needs to return a ImplementationConfig object for implementation."
    return Implementer(function, config).implementation  # type:ignore