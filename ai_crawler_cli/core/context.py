from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json

class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None

class ContextManager(BaseModel):
    messages: List[Message] = Field(default_factory=list)
    system_prompt: str = "You are an AI crawler agent capable of executing tools, managing states, and planning tasks."
    max_tokens: int = 4000
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.messages and self.system_prompt:
            self.messages.append(Message(role="system", content=self.system_prompt))
            
    def add_message(self, role: str, content: str, **kwargs):
        msg = Message(role=role, content=content, **kwargs)
        self.messages.append(msg)
        self._prune_context()

    def get_context(self) -> List[Dict[str, Any]]:
        return [msg.model_dump(exclude_none=True) for msg in self.messages]

    def _estimate_tokens(self, text: str) -> int:
        # A simple estimation: 1 token ~= 4 chars
        return len(text) // 4

    def _prune_context(self):
        """Keep the system prompt and recent messages within the token limit."""
        if len(self.messages) <= 1:
            return
            
        total_tokens = sum(self._estimate_tokens(str(m.content)) for m in self.messages if m.content)
        
        # While total tokens exceed limit, pop the oldest message (after system prompt)
        while total_tokens > self.max_tokens and len(self.messages) > 2:
            removed = self.messages.pop(1)
            if removed.content:
                total_tokens -= self._estimate_tokens(str(removed.content))
                
    def save_state(self, path: str):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(exclude_none=True), f, indent=4, ensure_ascii=False)
            
    @classmethod
    def load_state(cls, path: str) -> 'ContextManager':
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return cls(**data)
