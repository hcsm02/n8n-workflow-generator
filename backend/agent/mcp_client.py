"""
MCP 数据预加载器 (Pre-cache Strategy)

思路：服务器启动时，一次性通过 MCP 工具获取常用模板数据，缓存到内存中。
后续每次 LLM 调用直接使用缓存数据嵌入 prompt，不再逐次调工具。

同时保留原始 MCP 工具接口，供需要时手动调用（如未来的 advanced 模式）。
"""
import asyncio
import os
import json
from pathlib import Path
from langchain_mcp_adapters.client import MultiServerMCPClient

# 本地参考数据路径
BASE_DIR = Path("g:/github/n8n-workflow-generator")
REFERENCE_DIR = BASE_DIR / "reference" / "n8n"

class N8nMCPClient:
    """
    管理 n8n-mcp 连接，并在启动时预加载模板数据到缓存。
    """
    def __init__(self):
        self._client = None
        self.n8n_api_url = os.getenv("N8N_API_URL", "http://localhost:5678")
        self.n8n_api_key = os.getenv("N8N_API_KEY", "")
        
        # 缓存的参考数据
        self._cached_templates_summary = ""
        self._cached_rules = ""
        self._cached_patterns = ""
        self._is_loaded = False

    async def initialize(self):
        """初始化 MCP 客户端连接"""
        if self._client:
            return
        server_config = {
            "n8n-mcp": {
                "command": "npx",
                "args": ["-y", "n8n-mcp"],
                "transport": "stdio",
                "env": {
                    "MCP_MODE": "stdio",
                    "LOG_LEVEL": "error",
                    "DISABLE_CONSOLE_OUTPUT": "true",
                    "N8N_API_URL": self.n8n_api_url,
                    "N8N_API_KEY": self.n8n_api_key,
                    "PATH": os.environ.get("PATH", "")
                }
            }
        }
        self._client = MultiServerMCPClient(server_config)

    async def get_tools(self):
        """返回 LangChain 兼容的工具列表（供 advanced 模式使用）"""
        if not self._client:
            await self.initialize()
        return await self._client.get_tools()

    def load_local_reference_data(self):
        """
        从本地 reference/n8n 目录加载参考数据。
        这是最快最可靠的方式，不依赖 MCP 连接。
        """
        if self._is_loaded:
            return
        
        print("=== Loading local reference data ===")
        
        # 1. 加载生成规则
        rules_path = REFERENCE_DIR / "generation_rules.md"
        if rules_path.exists():
            self._cached_rules = rules_path.read_text(encoding="utf-8")
            print(f"  ✓ Rules loaded: {len(self._cached_rules)} chars")
        
        # 2. 加载金标准模式
        patterns = []
        pattern_dir = REFERENCE_DIR / "patterns"
        if pattern_dir.exists():
            for f in pattern_dir.glob("*.json"):
                content = f.read_text(encoding="utf-8")
                patterns.append(f"--- PATTERN: {f.name} ---\n{content}")
        self._cached_patterns = "\n\n".join(patterns)
        print(f"  ✓ Patterns loaded: {len(patterns)} files")
        
        # 3. 加载模板摘要（每个模板提取 name + nodes 列表即可，不需要完整 JSON）
        templates_summary = []
        template_dir = REFERENCE_DIR / "templates"
        if template_dir.exists():
            for f in template_dir.glob("*.json"):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    name = data.get("name", f.stem)
                    nodes = data.get("nodes", [])
                    node_types = [n.get("type", "unknown") for n in nodes]
                    templates_summary.append(
                        f"- {name}: {', '.join(node_types)}"
                    )
                except Exception as e:
                    print(f"  ✗ Failed to load {f.name}: {e}")
        self._cached_templates_summary = "\n".join(templates_summary)
        print(f"  ✓ Templates loaded: {len(templates_summary)} files")
        
        self._is_loaded = True
        print("=== Reference data loaded successfully ===")

    @property
    def rules(self) -> str:
        """获取缓存的生成规则"""
        if not self._is_loaded:
            self.load_local_reference_data()
        return self._cached_rules

    @property
    def patterns(self) -> str:
        """获取缓存的金标准模式"""
        if not self._is_loaded:
            self.load_local_reference_data()
        return self._cached_patterns

    @property
    def templates_summary(self) -> str:
        """获取缓存的模板摘要"""
        if not self._is_loaded:
            self.load_local_reference_data()
        return self._cached_templates_summary

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None

# 全局单例
mcp_client = N8nMCPClient()
