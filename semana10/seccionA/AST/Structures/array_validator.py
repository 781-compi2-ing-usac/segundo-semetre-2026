from AST.nodes import ArrayNode, PrimitiveNode
from AST.errors import CompilerError


class ArrayValidator:
    def __init__(self, phase="compile"):
        self.phase = phase

    def validate(self, elements):
        if not elements:
            raise CompilerError("Array cannot be empty", phase=self.phase)

        element_type, flat_elements, shape = self._flatten_and_validate(elements)

        return {
            "element_type": element_type,
            "flat_elements": flat_elements,
            "shape": tuple(shape),
            "dimensions": len(shape),
        }

    def _flatten_and_validate(self, elements):
        flat_elements = []
        element_type = None
        shape = []

        for elem in elements:
            if isinstance(elem, ArrayNode):
                sub_type, sub_flat, sub_shape = self._flatten_and_validate(elem.array)
                if element_type is None:
                    element_type = sub_type
                    shape = sub_shape
                elif element_type != sub_type or shape != sub_shape:
                    raise CompilerError(
                        "All array elements must have the same type and dimensions",
                        phase=self.phase,
                    )
                flat_elements.extend(sub_flat)
            elif isinstance(elem, PrimitiveNode):
                if element_type is None:
                    element_type = elem.type
                    shape = []
                elif element_type != elem.type:
                    raise CompilerError(
                        f"All array elements must have the same type, got {element_type} and {elem.type}",
                        phase=self.phase,
                    )
                flat_elements.append(elem)
            else:
                raise CompilerError(
                    f"Unsupported element type in array: {type(elem).__name__}",
                    phase=self.phase,
                )

        return element_type, flat_elements, [len(elements)] + shape
