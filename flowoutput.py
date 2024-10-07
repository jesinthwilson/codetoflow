import ast
import astor
import streamlit as st
from graphviz import Digraph

def generate_flowchart(code):
    dot = Digraph()
    last_non_empty_line = None
    last_for_end_node = None  # Track the end node of the for loop
    last_while_end_node = None  # Track the end node of the while loop
    indentation_levels = [0]  # Track indentation levels

    tree = ast.parse(code)

    def visit(node, parent=None):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id
                    if isinstance(node.value, ast.List):
                        value = astor.to_source(node.value).strip()
                        value = f"A list {var_name} is initialized with {value}"
                    else:
                        value = astor.to_source(node.value).strip()
                        value = f"{var_name} = {value}"
                    dot.node(var_name, value, shape='box', color='green')
                    if parent:
                        dot.edge(parent, var_name)
                    return var_name

        elif isinstance(node, ast.If):
            cond = astor.to_source(node.test).strip()
            condition_node = f"check_{id(node)}"
            dot.node(condition_node, f"check '{cond}'", shape='diamond', color='red')
            if parent:
                dot.edge(parent, condition_node)
            last_node_in_body = visit(node.body[0], parent=condition_node)
            if len(node.orelse) > 0:
                else_node = visit(node.orelse[0], parent=condition_node)
                dot.edge(condition_node, else_node, label='False')
            return last_node_in_body

        elif isinstance(node, ast.Expr):
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'print':
                content = astor.to_source(node.value.args[0]).strip() 
                print_node = f"print_{id(node)}"
                dot.node(print_node, f"'{content}' is printed", shape='box', color='blue')
                if parent:
                    dot.edge(parent, print_node)
                return print_node

        elif isinstance(node, ast.While):
            cond = astor.to_source(node.test).strip()
            while_node = f"while_{id(node)}"
            cond_display = f"{cond}"
            # Check if the condition is a comparison or a simple variable
            if isinstance(node.test, ast.Compare):
                left = astor.to_source(node.test.left).strip()
                right = astor.to_source(node.test.comparators[0]).strip()
                op = node.test.ops[0].__class__.__name__
                cond_display = f"{left} {op} {right}"
            dot.node(while_node, f"executes while loop until ({cond_display}) condition fails", shape='diamond', color='purple')
            if parent:
                dot.edge(parent, while_node)
            last_node_in_body = None
            for sub_node in node.body:
                last_node_in_body = visit(sub_node, parent=while_node)
            if last_node_in_body:
                dot.edge(last_node_in_body, while_node, label='loop back')
            return while_node

        elif isinstance(node, ast.For):
            if isinstance(node.iter, ast.Call) and node.iter.func.id == 'range':
                if len(node.iter.args) == 1:
                    start = '0'
                    stop = astor.to_source(node.iter.args[0]).strip()
                    step = '1'
                else:
                    start = astor.to_source(node.iter.args[0]).strip()
                    stop = astor.to_source(node.iter.args[1]).strip()
                    step = astor.to_source(node.iter.args[2]).strip() if len(node.iter.args) > 2 else '1'
                for_node = f"for_{id(node)}"
                dot.node(for_node, f"looping for from {start} to {stop} in intervals of {step}", shape='box', color='green')
                if parent:
                    dot.edge(parent, for_node)
                last_node_in_body = None
                for sub_node in node.body:
                    last_node_in_body = visit(sub_node, parent=for_node)
                if last_node_in_body:
                    dot.edge(last_node_in_body, for_node, label='loop back')
                return for_node

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'input':
                var_name = ''
                if node.args:
                    var_name = astor.to_source(node.args[0]).strip()
                input_node = f"input_{id(node)}"
                dot.node(input_node, f"'{var_name}' is taken as user input", shape='parallelogram', color='pink')
                if parent:
                    dot.edge(parent, input_node)
                return input_node

    # Add start node
    dot.node("start", "Start", shape='oval', color='black')

    last_node = "start"
    for node in ast.iter_child_nodes(tree):
        last_node = visit(node, parent=last_node)

    # Add stop node and connect the last node to the stop node
    dot.node("stop", "Stop", shape='oval', color='black')
    dot.edge(last_node, "stop")

    return dot

st.title('Python Flowchart Generator')

# Create two columns
left_column, right_column = st.columns([1,3])

with left_column:
    code = st.text_area('Paste your Python code here:')

if code:
    if st.button('Generate Flowchart'):
        with right_column:
            dot = generate_flowchart(code)
            st.graphviz_chart(dot.source)
