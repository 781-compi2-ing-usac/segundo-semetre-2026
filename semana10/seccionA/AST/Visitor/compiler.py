from AST.Visitor.visitor import Visitor
from AST.Builder.builder import Builder
from AST.nodes import *
from AST.errors import CompilerError
from AST.symtable import SymTable
from AST.Structures.array_validator import ArrayValidator


class Compiler(Visitor):
    _phase = "compile"

    def __init__(self, builder: Builder):
        super().__init__()
        self.builder = builder
        self.symbol_table: SymTable = SymTable()
        self.builder.emit_main_header()

    def get_code(self) -> str:
        self.builder.emit_main_footer()
        return self.builder.get_code()

    def visit_node(self, node):
        raise NotImplementedError(
            f"visit_node not implemented for {type(node).__name__}"
        )

    def visit_type(self, node: TypeNode):
        return node.value

    def visit_primitive(self, node: PrimitiveNode):
        return node.value

    def visit_variable(self, node: VariableNode):
        var_info = self.symbol_table.get_symbol(node.name)
        if var_info is None:
            raise CompilerError(
                f"Undefined variable: {node.name}", node=node, phase=self._phase
            )

        if node.access:
            if var_info["type"] != "array":
                raise CompilerError(
                    f"Variable '{node.name}' is not an array", node=node, phase=self._phase
                )
            offset_reg = self._calculate_array_offset(node.access, var_info["shape"])
            temp = self.builder.new_temp()
            self.builder.build_array_load(
                temp, var_info["base"], offset_reg, var_info["element_type"]
            )
            return temp
        else:
            base = var_info["base"]
            type_name = var_info["type"]
            temp = self.builder.new_temp()
            self.builder.build_memory_load(temp, base, type_name=type_name)
            return temp

    def visit_arith_op(self, node: ArithOpNode):
        left = self.dispatch(node.left)
        right = self.dispatch(node.right)

        left_type = self._get_expr_type(node.left)

        temp = self.builder.new_temp()
        self.builder.build_arithmetic(node.op, temp, left, right, type_name=left_type)
        return temp

    def visit_rel_op(self, node: RelOpNode):
        left = self.dispatch(node.left)
        right = self.dispatch(node.right)

        left_type = self._get_expr_type(node.left)

        cond_temp = self.builder.new_temp()
        self.builder.build_comparison(
            node.op, cond_temp, left, right, type_name=left_type
        )

        ev_label = self.builder.new_label()
        ef_label = self.builder.new_label()
        self.builder.build_branch_cond(cond_temp, ev_label, ef_label)

        return ([ev_label], [ef_label])

    def visit_logic_op(self, node: LogicOpNode):
        if node.op == "&":
            left_ev, left_ef = self.dispatch(node.left)

            self.builder.emitLabels(left_ev)

            right_ev, right_ef = self.dispatch(node.right)

            return (right_ev, left_ef + right_ef)

        elif node.op == "|":
            left_ev, left_ef = self.dispatch(node.left)

            self.builder.emitLabels(left_ef)

            right_ev, right_ef = self.dispatch(node.right)

            return (left_ev + right_ev, right_ef)

        else:
            raise NotImplementedError(f"Logic operator '{node.op}' not implemented")

    def visit_if(self, node: IfNode):
        ev_labels, ef_labels = self.dispatch(node.condition)

        self.builder.emitLabels(ev_labels)

        self.dispatch(node.block)

        end_label = self.builder.new_label()
        self.builder.build_branch(end_label)

        self.builder.emitLabels(ef_labels)
        self.builder.build_branch(end_label)

        self.builder.emit_label(end_label)

        return None

    def visit_declaration(self, node: DeclarationNode):
        type_name = self.dispatch(node.var_type)

        if node.expression and isinstance(node.expression, ArrayNode):
            array_info = self.dispatch(node.expression)
            self.symbol_table.add_symbol(
                node.var_name,
                {
                    "base": array_info["base"],
                    "type": "array",
                    "element_type": array_info["element_type"],
                    "dimensions": array_info["dimensions"],
                    "shape": array_info["shape"],
                },
            )
        else:
            base = self.builder.emit_alloca(node.var_name, type_name)
            self.symbol_table.add_symbol(node.var_name, {"base": base, "type": type_name})

            if node.expression:
                if isinstance(node.expression, (RelOpNode, LogicOpNode)):
                    self._materialize_to_variable(node.expression, base, type_name)
                else:
                    value = self.dispatch(node.expression)
                    self.builder.build_memory_store(value, base, type_name=type_name)
        return None

    def visit_assignment(self, node: AssignmentNode):
        var_info = self.symbol_table.get_symbol(node.var_name)
        if var_info is None:
            raise CompilerError(
                f"Undefined variable: {node.var_name}", node=node, phase=self._phase
            )

        if node.access:
            if var_info["type"] != "array":
                raise CompilerError(
                    f"Variable '{node.var_name}' is not an array", node=node, phase=self._phase
                )
            offset_reg = self._calculate_array_offset(node.access, var_info["shape"])
            value = self.dispatch(node.expression)
            self.builder.build_array_store(
                value, var_info["base"], offset_reg, var_info["element_type"]
            )
        elif not node.access and isinstance(node.expression, ArrayNode):
            if var_info["type"] != "array":
                raise CompilerError(
                    f"Cannot assign array to non-array variable '{node.var_name}'",
                    node=node,
                    phase=self._phase,
                )
            array_info = self.dispatch(node.expression)
            self.symbol_table.update_symbol(
                node.var_name,
                {
                    "base": array_info["base"],
                    "type": "array",
                    "element_type": array_info["element_type"],
                    "dimensions": array_info["dimensions"],
                    "shape": array_info["shape"],
                },
            )
        else:
            if isinstance(node.expression, (RelOpNode, LogicOpNode)):
                self._materialize_to_variable(
                    node.expression, var_info["base"], var_info["type"]
                )
            else:
                value = self.dispatch(node.expression)
                self.builder.build_memory_store(
                    value, var_info["base"], type_name=var_info["type"]
                )
        return None

    def visit_block(self, node: BlockNode):
        prev_table = self.symbol_table
        self.symbol_table = SymTable(parent=prev_table)
        for statement in node.statements:
            self.dispatch(statement)
        self.symbol_table = prev_table
        return None

    def visit_print(self, node: PrintNode):
        if isinstance(node.expression, (RelOpNode, LogicOpNode)):
            ev_labels, ef_labels = self.dispatch(node.expression)
            end_label = self.builder.new_label()
            self.builder.emitLabels(ev_labels)
            self.builder.build_print("1", "int")
            self.builder.build_branch(end_label)
            self.builder.emitLabels(ef_labels)
            self.builder.build_print("0", "int")
            self.builder.build_branch(end_label)
            self.builder.emit_label(end_label)
        else:
            value = self.dispatch(node.expression)
            expr_type = self._get_expr_type(node.expression)
            self.builder.build_print(value, expr_type)
        return None

    def visit_while(self, node: WhileNode):
        loop_start = self.builder.new_label()
        # En LLVM IR, necesitamos un branch al inicio del loop
        self.builder.build_branch(loop_start)
        self.builder.emit_label(loop_start)

        ev_labels, ef_labels = self.dispatch(node.condition)

        self.builder.emitLabels(ev_labels)

        self.dispatch(node.block)

        self.builder.build_branch(loop_start)

        self.builder.emitLabels(ef_labels)

        return None

    def visit_function_declaration(self, node: FunctionDeclarationNode):
        raise NotImplementedError(
            "Function declaration not implemented in basic version"
        )

    def visit_function_call(self, node: FunctionCallNode):
        raise NotImplementedError("Function call not implemented in basic version")

    def visit_param(self, node: ParamNode):
        raise NotImplementedError("Param not implemented in basic version")

    def visit_return(self, node: ReturnNode):
        raise NotImplementedError("Return not implemented in basic version")

    def visit_array(self, node: ArrayNode):
        validator = ArrayValidator(phase=self._phase)
        array_info = validator.validate(node.array)

        element_type = array_info["element_type"]
        flat_elements = array_info["flat_elements"]
        shape = array_info["shape"]

        first_offset = None
        for elem in flat_elements:
            offset = self.builder.emit_alloca(f"_arr_{id(elem)}", element_type)
            self.builder.build_memory_store(elem.value, offset, type_name=element_type)
            if first_offset is None:
                first_offset = offset

        return {
            "base": first_offset,
            "element_type": element_type,
            "dimensions": array_info["dimensions"],
            "shape": shape,
        }

    def _get_expr_type(self, node) -> str:
        if isinstance(node, PrimitiveNode):
            return node.type
        elif isinstance(node, VariableNode):
            var_info = self.symbol_table.get_symbol(node.name)
            if var_info is not None:
                return var_info["type"]
            return "int"
        elif isinstance(node, ArithOpNode):
            return self._get_expr_type(node.left)
        return "int"

    def _materialize_to_variable(self, condition_node, base, type_name):
        ev_labels, ef_labels = self.dispatch(condition_node)
        end_label = self.builder.new_label()
        self.builder.emitLabels(ev_labels)
        self.builder.build_memory_store(1, base, type_name=type_name)
        self.builder.build_branch(end_label)
        self.builder.emitLabels(ef_labels)
        self.builder.build_memory_store(0, base, type_name=type_name)
        self.builder.build_branch(end_label)
        self.builder.emit_label(end_label)

    def _calculate_array_offset(self, indices, shape):
        if len(indices) == 1:
            index_reg = self.builder.new_temp()
            index_val = self.dispatch(indices[0])
            if self._is_literal(index_val):
                self.builder.build_load_immediate(index_reg, int(index_val))
            else:
                self.builder.build_load_immediate(index_reg, index_val)
            return index_reg

        partial_offset = self._calculate_array_offset(indices[:-1], shape[:-1])
        last_index = self.dispatch(indices[-1])
        dim_value = shape[-1]

        if self._is_literal(last_index):
            last_index_reg = self.builder.new_temp()
            self.builder.build_load_immediate(last_index_reg, int(last_index))
            last_index = last_index_reg

        dim_reg = self.builder.new_temp()
        self.builder.build_load_immediate(dim_reg, dim_value)

        temp_mul = self.builder.new_temp()
        self.builder.build_multiply(temp_mul, partial_offset, dim_reg)

        temp_add = self.builder.new_temp()
        self.builder.build_add(temp_add, temp_mul, last_index)

        return temp_add

    def _is_literal(self, value) -> bool:
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False
