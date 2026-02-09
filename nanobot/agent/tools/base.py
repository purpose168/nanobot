"""智能体工具的基类。"""

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """
    智能体工具的抽象基类。
    
    工具是智能体可以用来与环境交互的能力，
    例如读取文件、执行命令等。
    """
    
    _TYPE_MAP = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称，用于函数调用。"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """工具功能的描述。"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """工具参数的 JSON Schema。"""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """
        使用给定参数执行工具。
        
        参数:
            **kwargs: 工具特定的参数。
        
        返回:
            工具执行的字符串结果。
        """
        pass

    def validate_params(self, params: dict[str, Any]) -> list[str]:
        """根据 JSON Schema 验证工具参数。如果有效则返回空错误列表。"""
        schema = self.parameters or {}
        if schema.get("type", "object") != "object":
            raise ValueError(f"Schema 必须是 object 类型，得到的是 {schema.get('type')!r}")
        return self._validate(params, {**schema, "type": "object"}, "")

    def _validate(self, val: Any, schema: dict[str, Any], path: str) -> list[str]:
        t, label = schema.get("type"), path or "parameter"
        if t in self._TYPE_MAP and not isinstance(val, self._TYPE_MAP[t]):
            return [f"{label} 应该是 {t}"]
        
        errors = []
        if "enum" in schema and val not in schema["enum"]:
            errors.append(f"{label} 必须是以下值之一 {schema['enum']}")
        if t in ("integer", "number"):
            if "minimum" in schema and val < schema["minimum"]:
                errors.append(f"{label} 必须 >= {schema['minimum']}")
            if "maximum" in schema and val > schema["maximum"]:
                errors.append(f"{label} 必须 <= {schema['maximum']}")
        if t == "string":
            if "minLength" in schema and len(val) < schema["minLength"]:
                errors.append(f"{label} 至少需要 {schema['minLength']} 个字符")
            if "maxLength" in schema and len(val) > schema["maxLength"]:
                errors.append(f"{label} 最多 {schema['maxLength']} 个字符")
        if t == "object":
            props = schema.get("properties", {})
            for k in schema.get("required", []):
                if k not in val:
                    errors.append(f"缺少必填参数 {path + '.' + k if path else k}")
            for k, v in val.items():
                if k in props:
                    errors.extend(self._validate(v, props[k], path + '.' + k if path else k))
        if t == "array" and "items" in schema:
            for i, item in enumerate(val):
                errors.extend(self._validate(item, schema["items"], f"{path}[{i}]" if path else f"[{i}]"))
        return errors
    
    def to_schema(self) -> dict[str, Any]:
        """将工具转换为 OpenAI 函数模式格式。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            }
        }
