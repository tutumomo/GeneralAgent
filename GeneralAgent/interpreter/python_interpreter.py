import re, io, os, sys
import pickle
import logging
from jinja2 import Template
from .interpreter import Interpreter
from GeneralAgent.utils import confirm_to_run
from functools import partial

default_import_code = """
import os, sys, math, time
from GeneralAgent import skills
"""

from GeneralAgent import skills
default_libs = ''
# default_libs = skills.get_current_env_python_libs()

# from GeneralAgent.tools import Tools

class PythonInterpreter(Interpreter):
    """
    Sync Python Interpreter: run python code in the interpreter. Not same namespace with the agent & Can Only run synchronous code
    """

    output_match_start_pattern = '```python\n'
    output_match_pattern = '```python\n(.*?)\n```'
    agent = None

    python_prompt_template = """
# Run python
- the code will be executed automatically when the code block is closed
- all global variables, functions will be saved, and can be used in the next run
- Available libraries: {{python_libs}}
- The following functions can be used in code (already implemented and imported for you):
```
{{python_funcs}}
```
- Example:
```python
result = 1 + 1
result
```
"""

    function_tools = []

    def __init__(self, 
                 agent = None,
                 serialize_path:str=None, 
                 libs: str=default_libs, 
                 import_code:str=None,
                 prompt_append='',
                 stop_wrong_count = 3
                 ):
        """
        Args:
            serialize_path (str): path to save the global variables, default None, which means not save, like './serialized.bin'
            libs ([str], optional): libraries can be to used. Defaults to skills.get_current_env_python_libs()
            import_code (str, optional): code to import. The tools used should be imported. Defaults to default_import_code.
            prompt_append: append to the prompt, custom prompt can be added here
            stop_wrong_count: stop running when the code is wrong for stop_wrong_count times
        """
        from GeneralAgent import skills
        self.globals = {}  # global variables shared by all code
        self.agent = agent
        self.python_libs = libs
        self.import_code = import_code or default_import_code
        self.serialize_path = serialize_path
        self.prompt_append = prompt_append
        # self.tools = tools or Tools([])
        self.globals = self.load()
        # count the number of times the code is wrong, and stop running when it reaches the threshold
        self.run_wrong_count = 0
        self.stop_wrong_count = stop_wrong_count

    def load(self):
        if self.serialize_path is None:
            return {}
        if os.path.exists(self.serialize_path):
            with open(self.serialize_path, 'rb') as f:
                data = pickle.loads(f.read())
                return data['globals']
        return {}

    def prompt(self, messages) -> str:
        from GeneralAgent import skills
        funtions = '\n\n'.join([skills.get_function_signature(x) for x in self.function_tools])
        variables = {
            'python_libs': self.python_libs,
            'python_funcs': funtions,
            'python_version': skills.get_python_version()
        }
        return Template(self.python_prompt_template).render(**variables) + self.prompt_append

    def save(self):
        if self.serialize_path is None:
            return
        save_globals = self._remove_unpickleable()
        # save
        with open(self.serialize_path, 'wb') as f:
            data = {'globals': save_globals}
            f.write(pickle.dumps(data))

    def _remove_unpickleable(self):
        save_globals = self.globals.copy()
        if '__builtins__' in save_globals:
            save_globals.__delitem__('__builtins__')
        keys = list(save_globals.keys())
        for key in keys:
            try:
                pickle.dumps(save_globals[key])
            except Exception as e:
                save_globals.__delitem__(key)
        return save_globals

    def output_parse(self, string) -> (str, bool):
        pattern = re.compile(self.output_match_pattern, re.DOTALL)
        match = pattern.search(string)
        assert match is not None
        if confirm_to_run():
            result, stop = self.run_code(match.group(1))
            result = '\nThe execution of the python code is completed, and the result is as follows:\n' + result + '\n'
            return result, stop
        else:
            return '', False

    def run_code(self, code):
        code = self.import_code + '\n' + code
        logging.debug(code)

        output = io.StringIO()
        sys.stdout = output

        try:
            if self.agent is not None:
                self.agent.run_level += 1
                if self.agent is not None:
                    self.globals['agent'] = self.agent
            for fun in self.function_tools:
                # partial function default is remote function
                if isinstance(fun, partial):
                    name = fun.args[0]
                else:
                    name = fun.__name
                self.globals[name] = fun
            result = exec_and_get_last_expression(self.globals, code)
            self.run_wrong_count = 0
            stop = False
            if self.agent is not None:
                stop = self.agent.run_level != 1
                self.agent.python_run_result = result
            if 'search_functions(' in code:
                stop = False
            # If result is None, return the terminal output
            if result is None:
                result = output.getvalue()
            self.save()
            return str(result), stop
        except Exception as e:
            logging.exception(e)
            import traceback
            error = traceback.format_exc()
            self.run_wrong_count += 1
            if self.run_wrong_count >= self.stop_wrong_count:
                raise e
            return error, False
        finally:
            sys.stdout = sys.__stdout__
            if self.agent is not None:
                self.agent.run_level -= 1

    def get_variable(self, name):
        if name in self.globals:
            return self.globals[name]
        else:
            logging.warning(f"Variable {name} not found")
            return None

    def set_variable(self, name, value):
        self.globals[name] = value


def exec_and_get_last_expression(globals_vars, code):
    # Compile the code into a code object, separating the last line if it's an expression
    code_lines = code.strip().split('\n')
    last_line = code_lines[-1]
    try:
        # Try to compile the last line as an expression
        last_expr = compile(last_line, '<string>', 'eval')
        # If successful, compile the rest of the code as exec
        main_code = compile('\n'.join(code_lines[:-1]), '<string>', 'exec')
        is_last_line_expression = True
    except SyntaxError:
        # If the last line is not an expression, compile the whole code as exec
        main_code = compile('\n'.join(code_lines), '<string>', 'exec')
        is_last_line_expression = False

    # Create a dictionary to serve as the local namespace
    # Execute the main body of the code
    exec(main_code, globals_vars)

    # If the last line was an expression, evaluate it and return the result
    if is_last_line_expression:
        last_expression_result = eval(last_expr, globals_vars)
        return last_expression_result
    else:
        # If the last line was not an expression, return None
        return None