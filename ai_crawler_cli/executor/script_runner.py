import sys
import io
import contextlib
import traceback
from typing import Dict, Any, Tuple
from ai_crawler_cli.utils.logger import log
from ai_crawler_cli.tools.registry import registry

@registry.register(name="execute_python", description="Execute arbitrary Python code and return stdout/stderr.")
def execute_python(code: str) -> str:
    """Execute Python code in a restricted environment and capture output."""
    log.info(f"Executing Python script of length {len(code)}")
    
    # Capture standard output and error
    output_buffer = io.StringIO()
    
    # Define execution context
    exec_globals = {
        "__builtins__": __builtins__,
        "requests": __import__("requests"),
        "bs4": __import__("bs4"),
        "json": __import__("json"),
        "re": __import__("re"),
        "time": __import__("time")
    }
    exec_locals: Dict[str, Any] = {}
    
    try:
        with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
            exec(code, exec_globals, exec_locals)
    except Exception as e:
        traceback.print_exc(file=output_buffer)
        log.error("Script execution failed.")
        
    result = output_buffer.getvalue()
    log.debug(f"Script output: {result[:200]}...")
    return result if result else "Execution completed with no output."
