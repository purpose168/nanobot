"""Shell 命令执行工具。"""

import asyncio
import os
import re
from pathlib import Path
from typing import Any

from nanobot.agent.tools.base import Tool


class ExecTool(Tool):
    """用于执行 shell 命令的工具。"""
    
    def __init__(
        self,
        timeout: int = 60,
        working_dir: str | None = None,
        deny_patterns: list[str] | None = None,
        allow_patterns: list[str] | None = None,
        restrict_to_workspace: bool = False,
    ):
        self.timeout = timeout
        self.working_dir = working_dir
        self.deny_patterns = deny_patterns or [
            r"\brm\s+-[rf]{1,2}\b",          # rm -r, rm -rf, rm -fr
            r"\bdel\s+/[fq]\b",              # del /f, del /q
            r"\brmdir\s+/s\b",               # rmdir /s
            r"\b(format|mkfs|diskpart)\b",   # 磁盘操作
            r"\bdd\s+if=",                   # dd
            r"\b(shutdown|reboot|poweroff)\b",  # 系统电源
            r":\(\)\s*\{.*\};\s*:",          # fork 炸弹
        ]
        self.allow_patterns = allow_patterns or []
        self.strict_to_workspace = restrict_to_workspace
    
    @property
    def name(self) -> str:
        return "exec"
    
    @property
    def description(self) -> str:
        return "执行 shell 命令并返回其输出。请谨慎使用。"
    
    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "要执行的 shell 命令"
                },
                "working_dir": {
                    "type": "string",
                    "description": "命令的可选工作目录"
                }
            },
            "required": ["command"]
        }
    
    async def execute(self, command: str, working_dir: str | None = None, **kwargs: Any) -> str:
        cwd = working_dir or self.working_dir or os.getcwd()
        guard_error = self._guard_command(command, cwd)
        if guard_error:
            return guard_error
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return f"错误：命令在 {self.timeout} 秒后超时"
            
            output_parts = []
            
            if stdout:
                output_parts.append(stdout.decode("utf-8", errors="replace"))
            
            if stderr:
                stderr_text = stderr.decode("utf-8", errors="replace")
                if stderr_text.strip():
                    output_parts.append(f"STDERR:\n{stderr_text}")
            
            if process.returncode != 0:
                output_parts.append(f"\nExit code: {process.returncode}")
            
            result = "\n".join(output_parts) if output_parts else "(无输出)"
            
            # 截断过长的输出
            max_len = 10000
            if len(result) > max_len:
                result = result[:max_len] + f"\n... (已截断，还有 {len(result) - max_len} 个字符)"
            
            return result
            
        except Exception as e:
            return f"执行命令时出错：{str(e)}"

    def _guard_command(self, command: str, cwd: str) -> str | None:
        """针对潜在破坏性命令的最佳努力安全防护。"""
        cmd = command.strip()
        lower = cmd.lower()

        for pattern in self.deny_patterns:
            if re.search(pattern, lower):
                return "错误：命令被安全防护阻止（检测到危险模式）"

        if self.allow_patterns:
            if not any(re.search(p, lower) for p in self.allow_patterns):
                return "错误：命令被安全防护阻止（不在允许列表中）"

        if self.restrict_to_workspace:
            if "..\\" in cmd or "../" in cmd:
                return "错误：命令被安全防护阻止（检测到路径遍历）"

            cwd_path = Path(cwd).resolve()

            win_paths = re.findall(r"[A-Za-z]:\\[^\\\"']+", cmd)
            posix_paths = re.findall(r"/[^\s\"']+", cmd)

            for raw in win_paths + posix_paths:
                try:
                    p = Path(raw).resolve()
                except Exception:
                    continue
                if cwd_path not in p.parents and p != cwd_path:
                    return "错误：命令被安全防护阻止（路径在工作目录之外）"

        return None
