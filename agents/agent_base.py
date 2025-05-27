
# agents/agent_base.py

class AgentBase:
    def __init__(self, name, permissions, tools):
        self.name = name
        self.permissions = permissions
        self.tools = tools

    def has_permission(self, action: str) -> bool:
        return self.permissions.get(action, False)

    def can_use_tool(self, tool_name: str) -> bool:
        return tool_name in self.tools
