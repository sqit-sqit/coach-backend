# 📚 Documentation Index

## 🎯 **Quick Navigation**

### **🏗️ Architecture & Design**
- **[ARCHITECTURE_AI_CHAT.md](./ARCHITECTURE_AI_CHAT.md)** - Complete AI chat architecture documentation
- **[CHAT_IMPLEMENTATION_GUIDE.md](./CHAT_IMPLEMENTATION_GUIDE.md)** - Practical implementation patterns
- **[FRONTEND_CHAT_IMPLEMENTATION.md](./FRONTEND_CHAT_IMPLEMENTATION.md)** - Frontend chat patterns and best practices
- **[VALUES_LAYOUT_TEMPLATE.md](./VALUES_LAYOUT_TEMPLATE.md)** - Reusable layout template for all applications

### **📋 By Topic**

#### **AI Chat Systems**
- [BaseChatService Architecture](./ARCHITECTURE_AI_CHAT.md#basechatservice-architecture)
- [Streaming Implementation](./ARCHITECTURE_AI_CHAT.md#streaming-implementation)
- [Personality Management](./ARCHITECTURE_AI_CHAT.md#personality-management)
- [Database Patterns](./CHAT_IMPLEMENTATION_GUIDE.md#database-schema)

#### **Application Implementations**
- [Values Chat](./CHAT_IMPLEMENTATION_GUIDE.md#1-values-chat-working)
- [Human Design Chat](./CHAT_IMPLEMENTATION_GUIDE.md#2-human-design-chat-working)
- [Spiral Chat](./CHAT_IMPLEMENTATION_GUIDE.md#3-spiral-chat-fixed)

#### **Development Patterns**
- [Simple Functions Pattern](./CHAT_IMPLEMENTATION_GUIDE.md#pattern-1-simple-functions-values-spiral)
- [Service Classes Pattern](./CHAT_IMPLEMENTATION_GUIDE.md#pattern-2-service-classes-human-design)
- [Frontend Chat Patterns](./FRONTEND_CHAT_IMPLEMENTATION.md#architecture-patterns)
- [Layout Template Pattern](./VALUES_LAYOUT_TEMPLATE.md#layout-architecture)
- [Common Pitfalls](./FRONTEND_CHAT_IMPLEMENTATION.md#common-pitfalls-and-solutions)
- [Best Practices](./CHAT_IMPLEMENTATION_GUIDE.md#best-practices)

#### **Adding New Features**
- [New Chat Apps](./CHAT_IMPLEMENTATION_GUIDE.md#adding-new-chat-apps)
- [New Layout Implementation](./VALUES_LAYOUT_TEMPLATE.md#implementation-guide)
- [Database Migrations](./ARCHITECTURE_AI_CHAT.md#database-migrations)
- [API Endpoints](./CHAT_IMPLEMENTATION_GUIDE.md#endpoints)

### **🔧 Implementation Status**

| Application | Status | Architecture | Documentation |
|-------------|--------|--------------|---------------|
| Values | ✅ Working | Simple Functions | [Guide](./CHAT_IMPLEMENTATION_GUIDE.md#1-values-chat-working) |
| Human Design | ✅ Working | Service Classes | [Guide](./CHAT_IMPLEMENTATION_GUIDE.md#2-human-design-chat-working) |
| Spiral | ✅ Fixed | Simple Functions | [Guide](./CHAT_IMPLEMENTATION_GUIDE.md#3-spiral-chat-fixed) |

### **📁 File Locations**

#### **Backend Code**
- `app/modules/values/` - Values implementation
- `app/modules/hd/` - Human Design implementation  
- `app/modules/spiral/` - Spiral implementation
- `app/core/chat_service.py` - BaseChatService
- `app/config/ai_models.py` - AI model configuration

#### **Personality Files**
- `app/personality/value_personality_chat.txt`
- `app/personality/hd_personality_chat.txt`
- `app/personality/spiral_personality_chat.txt`

#### **Database Models**
- `app/modules/*/models.py` - SQLAlchemy models
- `app/modules/*/schemas.py` - Pydantic schemas
- `migrations/` - Alembic migrations

### **🚀 Getting Started**

1. **New to the project?** Start with [README.md](./README.md)
2. **Implementing chat?** Read [CHAT_IMPLEMENTATION_GUIDE.md](./CHAT_IMPLEMENTATION_GUIDE.md)
3. **Understanding architecture?** Study [ARCHITECTURE_AI_CHAT.md](./ARCHITECTURE_AI_CHAT.md)
4. **Adding new app?** Follow [Adding New Chat Apps](./CHAT_IMPLEMENTATION_GUIDE.md#adding-new-chat-apps)

### **🔍 Troubleshooting**

**Header hiding after first message?**
→ [Solution: Auto-scroll pitfall](./FRONTEND_CHAT_IMPLEMENTATION.md#1-️-header-hiding-after-first-message)

**Chat layout issues?**
→ [Solution: WorkshopLayout vs Chat Layout](./FRONTEND_CHAT_IMPLEMENTATION.md#2-chat-layout-vs-workshoplayout)

**Streaming not working?**
→ [Solution: Stream debugging](./FRONTEND_CHAT_IMPLEMENTATION.md#3-stream-not-working)

**Messages disappearing?**
→ [Solution: State management](./FRONTEND_CHAT_IMPLEMENTATION.md#4-messages-disappearing)

**Full checklist:**
→ [New Chat Implementation Checklist](./FRONTEND_CHAT_IMPLEMENTATION.md#checklist-for-new-chat-implementation)

### **📞 Need Help?**

- Check code examples in `app/modules/`
- Review implementation patterns in the guides
- Look at working applications (Values, HD, Spiral)
- Follow the established patterns for consistency
- Check [Common Pitfalls](./FRONTEND_CHAT_IMPLEMENTATION.md#common-pitfalls-and-solutions) section
