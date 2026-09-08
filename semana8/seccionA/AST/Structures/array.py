class ArrayType:
    """Static type information for an array or matrix."""

    def __init__(self, element_type, shape):
        self.element_type = element_type
        self.shape = tuple(shape)

    @property
    def dimensions(self):
        return len(self.shape)

    def accessed_type(self, access_count):
        if access_count > self.dimensions:
            raise TypeError(
                f"Array access has {access_count} dimensions, "
                f"but the array has {self.dimensions}"
            )

        remaining_shape = self.shape[access_count:]
        if not remaining_shape:
            return self.element_type
        return ArrayType(self.element_type, remaining_shape)

    def is_compatible_with(self, other):
        if not isinstance(other, ArrayType):
            return False
        if self.element_type != other.element_type:
            return False
        if self.dimensions != other.dimensions:
            return False
        return all(
            expected_size is None or expected_size == actual_size
            for expected_size, actual_size in zip(self.shape, other.shape)
        )

    def __eq__(self, other):
        return (
            isinstance(other, ArrayType)
            and self.element_type == other.element_type
            and self.shape == other.shape
        )

    def __repr__(self):
        return f"ArrayType({self.element_type}, {self.shape})"

    def __str__(self):
        dimensions = "".join(
            f"[{'' if size is None else size}]" for size in self.shape
        )
        return f"{self.element_type}{dimensions}"


class ArrayAccessError(Exception):
    """Raised when an array access is invalid during interpretation."""


class ArrayValue:
    """Runtime value that preserves nested array structure."""

    def __init__(self, values):
        self.values = list(values)

    def get(self, indexes):
        current = self

        for depth, index in enumerate(indexes):
            if not isinstance(current, ArrayValue):
                raise ArrayAccessError(
                    f"Too many indexes for array at dimension {depth + 1}"
                )
            current = current._get_at(index, depth)

        return current

    def set(self, indexes, value):
        if not indexes:
            raise ArrayAccessError("An array assignment requires an index")

        current = self
        for depth, index in enumerate(indexes[:-1]):
            if not isinstance(current, ArrayValue):
                raise ArrayAccessError(
                    f"Too many indexes for array at dimension {depth + 1}"
                )
            current = current._get_at(index, depth)

        if not isinstance(current, ArrayValue):
            raise ArrayAccessError("Too many indexes for array assignment")
        current._set_at(indexes[-1], value, len(indexes) - 1)

    def _get_at(self, index, depth):
        self._validate_index(index)
        if index < 0 or index >= len(self.values):
            raise ArrayAccessError(
                f"Array index {index} is out of bounds at dimension {depth + 1}"
            )
        return self.values[index]

    def _set_at(self, index, value, depth):
        self._validate_index(index)
        if index < 0 or index >= len(self.values):
            raise ArrayAccessError(
                f"Array index {index} is out of bounds at dimension {depth + 1}"
            )
        self.values[index] = value

    @staticmethod
    def _validate_index(index):
        if type(index) is not int:
            raise ArrayAccessError(
                f"Array index must be int, got {type(index).__name__}"
            )

    def to_python(self):
        return [
            value.to_python() if isinstance(value, ArrayValue) else value
            for value in self.values
        ]

    def __str__(self):
        return str(self.to_python())

    def __repr__(self):
        return f"ArrayValue({self.values!r})"
