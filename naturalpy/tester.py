from typing import Any, Self

class Null:
    """Custom class to signalize that no value was given."""
null = Null()

class Tester:
    """Represents tests for a given function."""
    
    def __init__(self):
        """Implementation constructor."""
        self.runs_tests = []
        self.equals_tests = []
        self.unequals_tests = []
        self.raises_tests = []

    def check(self, *args: Any, equals: Any = null, unequals: Any = null, tolerance: float | Null = null, raises: Exception | Null = null) -> Self:
        """Adds a test which will be checked during the implementation of a function.
        If no optional keyword arguments are given, then the test checks if the function runs without raising an exception.
        
        Args:
            args: The inputs to the function.
            equals: The expected output, if not null.
            unequals: The unexpected output, if not null.
            tolerance: A tolerance between the expected value and the predicted value, if not null.
            raises: A super class of the expected exception, if not null.
        
        Returns:
            self: The ImplementationTests.
        """
        if not isinstance(equals, Null):
            self.equals_tests.append((args, equals, tolerance))
        elif not isinstance(unequals, Null):
            self.unequals_tests.append((args, unequals, tolerance))
        elif not isinstance(raises, Null):
            self.raises_tests.append((args, raises))
        else:
            self.runs_tests.append(args)
        return self