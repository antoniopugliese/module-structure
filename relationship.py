import ast

# lists the name of every function in the ast


class FuncLister(ast.NodeVisitor):
    def visit_FunctionDef(self, node):
        print(node.name)
        self.generic_visit(node)


# prints the name of the function whenever it is called
class CallLister(ast.NodeVisitor):
    def visit_Call(self, node):
      # print name of function called
        print(node.func.id)
        self.generic_visit(node)

# walks through every import statement (and does nothing)


class ImportEdge(ast.NodeVisitor):
    def visit_Import(self, node):
        # create edge
        self.generic_visit(node)
