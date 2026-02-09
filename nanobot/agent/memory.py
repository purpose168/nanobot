"""用于智能体持久化记忆的记忆系统。"""

from pathlib import Path
from datetime import datetime

from nanobot.utils.helpers import ensure_dir, today_date


class MemoryStore:
    """
    智能体的记忆系统。
    
    支持每日笔记（memory/YYYY-MM-DD.md）和长期记忆（MEMORY.md）。
    """
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.memory_dir = ensure_dir(workspace / "memory")
        self.memory_file = self.memory_dir / "MEMORY.md"
    
    def get_today_file(self) -> Path:
        """获取今天的记忆文件路径。"""
        return self.memory_dir / f"{today_date()}.md"
    
    def read_today(self) -> str:
        """读取今天的记忆笔记。"""
        today_file = self.get_today_file()
        if today_file.exists():
            return today_file.read_text(encoding="utf-8")
        return ""
    
    def append_today(self, content: str) -> None:
        """将内容追加到今天的记忆笔记。"""
        today_file = self.get_today_file()
        
        if today_file.exists():
            existing = today_file.read_text(encoding="utf-8")
            content = existing + "\n" + content
        else:
            # 为新的一天添加标题
            header = f"# {today_date()}\n\n"
            content = header + content
        
        today_file.write_text(content, encoding="utf-8")
    
    def read_long_term(self) -> str:
        """读取长期记忆（MEMORY.md）。"""
        if self.memory_file.exists():
            return self.memory_file.read_text(encoding="utf-8")
        return ""
    
    def write_long_term(self, content: str) -> None:
        """写入长期记忆（MEMORY.md）。"""
        self.memory_file.write_text(content, encoding="utf-8")
    
    def get_recent_memories(self, days: int = 7) -> str:
        """
        获取最近 N 天的记忆。
        
        参数:
            days: 要回溯的天数。
        
        返回:
            组合的记忆内容。
        """
        from datetime import timedelta
        
        memories = []
        today = datetime.now().date()
        
        for i in range(days):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            file_path = self.memory_dir / f"{date_str}.md"
            
            if file_path.exists():
                content = file_path.read_text(encoding="utf-8")
                memories.append(content)
        
        return "\n\n---\n\n".join(memories)
    
    def list_memory_files(self) -> list[Path]:
        """列出所有记忆文件，按日期排序（最新的在前）。"""
        if not self.memory_dir.exists():
            return []
        
        files = list(self.memory_dir.glob("????-??-??.md"))
        return sorted(files, reverse=True)
    
    def get_memory_context(self) -> str:
        """
        获取智能体的记忆上下文。
        
        返回:
            格式化的记忆上下文，包括长期和最近的记忆。
        """
        parts = []
        
        # 长期记忆
        long_term = self.read_long_term()
        if long_term:
            parts.append("## 长期记忆\n" + long_term)
        
        # 今天的笔记
        today = self.read_today()
        if today:
            parts.append("## 今天的笔记\n" + today)
        
        return "\n\n".join(parts) if parts else ""
