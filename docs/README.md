# 📚 Coach Backend Documentation

## 📋 **Overview**

This directory contains comprehensive documentation for the Coach backend application, including architecture guides, implementation patterns, and best practices.

## 📁 **Documentation Structure**

### 🏗️ **Architecture Documentation**
- **[ARCHITECTURE_AI_CHAT.md](./ARCHITECTURE_AI_CHAT.md)** - Theoretical AI chat architecture with `BaseChatService` and specialized services
- **[CHAT_IMPLEMENTATION_GUIDE.md](./CHAT_IMPLEMENTATION_GUIDE.md)** - Practical implementation guide for chat functionality across all applications

### 🎯 **Key Topics Covered**

#### **AI Chat Architecture**
- Unified chat service design
- Streaming implementation
- Database persistence patterns
- Error handling strategies
- Personality management

#### **Application-Specific Implementations**
- **Values Chat** - Simple function-based approach
- **Human Design Chat** - Service class inheritance
- **Spiral Chat** - Fixed implementation using Values pattern

#### **Database Schema**
- Session management
- Message persistence
- Summary generation
- User authentication

## 🚀 **Quick Start**

1. **Read Architecture Overview**: Start with `ARCHITECTURE_AI_CHAT.md` for theoretical understanding
2. **Follow Implementation Guide**: Use `CHAT_IMPLEMENTATION_GUIDE.md` for practical implementation
3. **Reference Code Examples**: Check actual implementations in `app/modules/` directories

## 📝 **Documentation Standards**

- **Markdown format** for readability
- **Code examples** with syntax highlighting
- **Step-by-step guides** for complex processes
- **Best practices** and anti-patterns clearly marked
- **Cross-references** between related documents

## 🔄 **Maintenance**

This documentation is maintained alongside code changes. When implementing new features:

1. Update relevant documentation files
2. Add new patterns to implementation guide
3. Update architecture docs for significant changes
4. Keep examples current and working

## 📞 **Support**

For questions about implementation or architecture decisions, refer to:
- Code comments in relevant files
- This documentation directory
- Implementation examples in `app/modules/`

