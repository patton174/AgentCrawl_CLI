import inspect
from typing import Callable, Dict, Any, List
from pydantic import BaseModel

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Callable] = {}
        self._schemas: List[Dict[str, Any]] = []

    def register(self, name: str = None, description: str = None):
        def decorator(func: Callable):
            tool_name = name or func.__name__
            tool_desc = description or inspect.getdoc(func) or "No description provided."
            
            self._tools[tool_name] = func
            
            # Simple schema generation (In real world, parse type hints)
            # For brevity, we assume kwargs only or define schemas manually
            schema = {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_desc,
                    "parameters": {
                        "type": "object",
                        "properties": self._generate_properties(func),
                        "required": self._get_required_params(func)
                    }
                }
            }
            self._schemas.append(schema)
            return func
        return decorator

    def _generate_properties(self, func: Callable) -> Dict[str, Any]:
        sig = inspect.signature(func)
        props = {}
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            param_type = "string"
            if param.annotation == int:
                param_type = "integer"
            elif param.annotation == bool:
                param_type = "boolean"
                
            props[param_name] = {
                "type": param_type,
                "description": f"Parameter {param_name}"
            }
        return props
        
    def _get_required_params(self, func: Callable) -> List[str]:
        sig = inspect.signature(func)
        required = []
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
        return required

    def get_schemas(self) -> List[Dict[str, Any]]:
        return self._schemas

    def execute(self, name: str, kwargs: Dict[str, Any]) -> Any:
        if name not in self._tools:
            raise ValueError(f"Tool {name} not found.")
        func = self._tools[name]
        return func(**kwargs)

# Global registry
registry = ToolRegistry()
