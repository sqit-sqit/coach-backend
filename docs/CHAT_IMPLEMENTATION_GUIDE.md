# 🚀 Chat Implementation Guide

## 📋 **Overview**

This guide documents how chat functionality is implemented across different applications in the Coach system.

## 🎯 **Current Chat Implementations**

### 1. **Values Chat** ✅ (Working)
**Location:** `app/modules/values/service_chat.py`
**Architecture:** Simple functions
**Key Functions:**
- `chat_with_ai()` - Returns full response
- `stream_chat_with_ai()` - Returns generator for streaming
- `load_personality()` - Loads personality from file
- `save_chat_message()` - Saves to database

**Endpoints:**
- `POST /values/chat/{user_id}` - Regular chat
- `POST /values/chat/{user_id}/stream` - Streaming chat

**Database Models:**
- `ValuesSession`
- `ValuesChatMessage`
- `ValuesSummary`

### 2. **Human Design Chat** ✅ (Working)
**Location:** `app/modules/hd/service_chat.py`
**Architecture:** `HDChatService(BaseChatService)`
**Key Functions:**
- `chat_with_hd_ai()` - Wrapper for compatibility
- `stream_chat_with_hd_ai()` - Wrapper for streaming
- `load_hd_personality()` - Loads personality with HD data

**Endpoints:**
- `POST /hd/chat` - Start chat
- `POST /hd/chat/{chat_session_id}` - Regular chat
- `POST /hd/chat/{chat_session_id}/stream` - Streaming chat

**Database Models:**
- `HDSession`
- `HDChatMessage`
- `HDSummary`

### 3. **Spiral Chat** ✅ (Fixed)
**Location:** `app/modules/spiral/service_chat_simple.py`
**Architecture:** Simple functions (copied from Values)
**Key Functions:**
- `chat_with_spiral_ai()` - Returns full response
- `stream_chat_with_spiral_ai()` - Returns generator for streaming
- `load_spiral_personality()` - Loads personality with context
- `save_chat_message()` - Saves to database

**Endpoints:**
- `POST /spiral/chat/{session_id}/stream` - Streaming chat
- `POST /spiral/chat/{session_id}/start` - Start chat

**Database Models:**
- `SpiralSession`
- `SpiralChatMessage`
- `SpiralSummary`

## 🔧 **Implementation Patterns**

### **Pattern 1: Simple Functions (Values, Spiral)**
```python
def chat_with_ai(user_message: str, history: list[dict], context: dict, user_id: str) -> str:
    # Load personality
    system_prompt = load_personality(context)
    
    # Prepare messages
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})
    
    # Call OpenAI
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(...)
    
    # Save to database
    save_chat_message(db, session_id, "user", user_message)
    save_chat_message(db, session_id, "assistant", response)
    
    return response
```

### **Pattern 2: Service Classes (Human Design)**
```python
class HDChatService(BaseChatService):
    def __init__(self):
        super().__init__("hd")
    
    def _load_personality(self, context_data: dict) -> str:
        return load_hd_personality(context_data)
    
    def _get_start_message(self) -> str:
        return "Start the Human Design conversation..."
```

## 📊 **Database Schema**

### **Values Tables:**
- `values_sessions` - User sessions
- `values_chat_messages` - Chat messages
- `values_summaries` - Session summaries

### **HD Tables:**
- `hd_sessions` - User sessions
- `hd_chat_messages` - Chat messages
- `hd_summaries` - Session summaries

### **Spiral Tables:**
- `spiral_sessions` - User sessions
- `spiral_chat_messages` - Chat messages
- `spiral_summaries` - Session summaries

## 🎯 **Best Practices**

### **✅ Do:**
- Use simple functions for new apps (like Spiral)
- Keep personality files separate
- Use consistent database patterns
- Implement both regular and streaming endpoints
- Save messages to database
- Handle errors gracefully

### **❌ Don't:**
- Over-engineer with complex inheritance
- Mix different chat implementations
- Skip database persistence
- Forget error handling
- Create inconsistent API patterns

## 🚀 **Adding New Chat Apps**

1. **Create models** in `app/modules/{app_name}/models.py`
2. **Create schemas** in `app/modules/{app_name}/schemas.py`
3. **Create service** in `app/modules/{app_name}/service_chat_simple.py`
4. **Create router** in `app/modules/{app_name}/chat_router.py`
5. **Add personality** in `app/personality/{app_name}_personality_chat.txt`
6. **Add AI config** in `app/config/ai_models.py`
7. **Include router** in `app/main.py`

## 📝 **Notes**

- **Values Chat** is the reference implementation
- **Spiral Chat** was fixed by copying Values pattern
- **Human Design Chat** uses more complex architecture but works
- All implementations support streaming
- All implementations persist to database
- All support error handling and streaming
