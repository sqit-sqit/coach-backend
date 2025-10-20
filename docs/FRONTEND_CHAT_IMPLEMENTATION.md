# Frontend Chat Implementation Guide

## Overview

This document describes how to implement chat functionality in the frontend, based on the working implementations in Values and Human Design applications.

## Architecture Patterns

### 1. Values Chat (Recommended Pattern)
- **File**: `src/app/values/chat/page.js`
- **Pattern**: Direct implementation with `useApi` hook
- **Features**: Full control, custom streaming, complex state management
- **Best for**: Complex applications with custom logic

### 2. Human Design Chat (Shared Hooks Pattern)
- **File**: `src/app/hd/chat/page.js`
- **Pattern**: Uses shared hooks (`useStreamingChat`, `useChatMessages`)
- **Features**: Simpler implementation, reusable components
- **Best for**: Simple applications with standard chat flow

## Common Layout Structure

Both implementations use the same basic layout structure:

```jsx
<div className="min-h-screen flex flex-col bg-[#F9F9FB]">
  {/* Chat messages area */}
  <div className="flex-1 overflow-y-auto">
    <div className="space-y-6 px-4 sm:px-6 lg:px-8 pt-16">
      {/* Messages */}
      <div className="space-y-6">
        {messages.map((message, index) => (
          <ChatBubble key={index} role={message.role}>
            {message.content}
          </ChatBubble>
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
  </div>

  {/* Input area – sticky na dole */}
  <div className="bg-transparent sticky bottom-0">
    <div className="space-y-4 px-4 sm:px-6 lg:px-8">
      <div className="flex gap-2 justify-end">
        {quickTips.map((tip, index) => (
          <QuickChip key={index} label={tip.label} onClick={tip.onClick} />
        ))}
      </div>
      <ChatInput onSend={handleSendMessage} disabled={isStreaming} />
    </div>
  </div>
</div>
```

## Key Components

### 1. ChatBubble
- **File**: `src/components/ui/ChatBubble.jsx`
- **Props**: `role`, `title`, `isSummary`, `hasActionChips`, `onActionChipClick`
- **Usage**: Renders individual chat messages

### 2. ChatInput
- **File**: `src/components/ui/ChatInput.jsx`
- **Props**: `onSend`, `disabled`
- **Usage**: Input field for sending messages

### 3. QuickChip
- **File**: `src/components/ui/QuickChip.jsx`
- **Props**: `label`, `onClick`
- **Usage**: Quick action buttons

### 4. TypingIndicator
- **File**: `src/components/ui/TypingIndicator.jsx`
- **Usage**: Shows when AI is generating response

## State Management

### Values Pattern (Recommended)

```javascript
// Core state
const [messages, setMessages] = useState([]);
const [isStreaming, setIsStreaming] = useState(false);
const [userId, setUserId] = useState(null);

// Application-specific state
const [chosenValue, setChosenValue] = useState(null);
const [chatMode, setChatMode] = useState("chat");
const [sessionSummary, setSessionSummary] = useState(null);

// Refs
const messagesEndRef = useRef(null);
const abortControllerRef = useRef(null);

// Auto-scroll implementation
const scrollToBottom = () => {
  messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
};

// ⚠️ IMPORTANT: Skip first message to keep header visible!
useEffect(() => {
  if (messages.length > 1) {
    scrollToBottom();
  }
}, [messages]);
```

### Human Design Pattern (Shared Hooks)

```javascript
// Use shared hooks
const { sendMessage, isStreaming } = useStreamingChat();
const { 
  messages, 
  setMessages, 
  isLoading, 
  setIsLoading, 
  addUserMessage, 
  updateAssistantMessage 
} = useChatMessages();

// Application-specific state
const [userId, setUserId] = useState(null);
const [sessionId, setSessionId] = useState(null);
const [appData, setAppData] = useState(null);
const messagesEndRef = useRef(null);

// Auto-scroll
useEffect(() => {
  messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
}, [messages]);
```

## Message Handling

### Values Pattern (Direct State Management)

```javascript
// Add user message directly
const addUserMessage = (content) => {
  const userMessage = { role: "user", content };
  setMessages(prev => [...prev, userMessage]);
  return prev.length; // Return index for assistant message
};

// Update assistant message during streaming
const updateAssistantMessage = (content, index, append = false) => {
  setMessages(prev => {
    const updated = [...prev];
    if (append) {
      updated[index].content += content;
    } else {
      updated[index].content = content;
    }
    return updated;
  });
};

// Add assistant message with placeholder
const addAssistantMessage = () => {
  const assistantMessage = { 
    role: "assistant", 
    content: "", 
    isGenerating: true 
  };
  setMessages(prev => [...prev, assistantMessage]);
  return prev.length;
};
```

### Human Design Pattern (Shared Hooks)

```javascript
// Use shared hook methods
const assistantIndex = addUserMessage(message);
const onMessageUpdate = (content, append = false) => {
  updateAssistantMessage(content, assistantIndex, append);
};
```

## Streaming Implementation

### Values Pattern (Direct with useApi)

```javascript
const handleSendMessage = async (message) => {
  if (!message.trim() || isStreaming) return;

  // Add user message
  const assistantIndex = addUserMessage(message);
  setIsStreaming(true);

  // Create callback for streaming
  const onMessageUpdate = (content, append = false) => {
    updateAssistantMessage(content, assistantIndex, append);
  };

  // Use useApi hook for streaming
  await apiPostStream(
    `/values/chat/${userId}/stream`,
    { message, history: messages },
    onMessageUpdate
  );

  setIsStreaming(false);
};
```

### Human Design Pattern (Shared Hooks)

```javascript
const { sendMessage, isStreaming } = useStreamingChat();
const { messages, setMessages, addUserMessage, updateAssistantMessage } = useChatMessages();

const handleSendMessage = async (message) => {
  if (!message.trim() || isStreaming) return;

  const assistantIndex = addUserMessage(message);
  
  const onMessageUpdate = (content, append = false) => {
    updateAssistantMessage(content, assistantIndex, append);
  };

  await sendMessage(
    `/hd/chat/${sessionId}/stream`,
    message,
    messages.map(m => ({ role: m.role, content: m.content })),
    onMessageUpdate
  );
};
```

## Initialization Patterns

### Values Pattern (Auto-generate First Message)

```javascript
// Auto-generate first AI message when data is ready
useEffect(() => {
  if (!chosenValue || messages.length > 0) return;
  
  generateFirstAIMessage();
}, [chosenValue]);

const generateFirstAIMessage = async () => {
  try {
    setIsStreaming(true);
    
    // Add placeholder message
    const assistantIndex = addAssistantMessage();
    
    const onMessageUpdate = (content, append = false) => {
      updateAssistantMessage(content, assistantIndex, append);
    };

    await apiPostStream(
      `/values/chat/${userId}/stream`,
      { message: "", history: [] },
      onMessageUpdate
    );
    
    setIsStreaming(false);
  } catch (error) {
    console.error("Error generating first message:", error);
    setIsStreaming(false);
  }
};
```

### Human Design Pattern (Backend Initialization)

```javascript
// Initialize chat through backend endpoint
const startChatSession = async () => {
  try {
    const response = await fetch(`${API_URL}/hd/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId })
    });

    if (response.ok) {
      const data = await response.json();
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: data.message,
        timestamp: new Date().toISOString()
      }]);
    }
  } catch (error) {
    console.error("Error starting chat session:", error);
  }
};
```

## Loading States

### Authentication Loading

```javascript
if (isLoading || !userId) {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading...</p>
      </div>
    </div>
  );
}
```

### Data Loading

```javascript
if (!data) {
  return (
    <div className="max-w-4xl mx-auto text-center py-12">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
      <p className="text-gray-600">Loading data...</p>
    </div>
  );
}
```

## Quick Tips Implementation

```javascript
const quickTips = [
  {
    label: "Tip 1",
    onClick: () => handleSendMessage("Predefined message 1")
  },
  {
    label: "Tip 2", 
    onClick: () => handleSendMessage("Predefined message 2")
  }
];
```

## Responsive Design

### Container Classes
- **Main container**: `min-h-screen flex flex-col bg-[#F9F9FB]`
- **Messages area**: `flex-1 overflow-y-auto`
- **Messages container**: `space-y-6 px-4 sm:px-6 lg:px-8 pt-16`
- **Input area**: `bg-transparent sticky bottom-0`
- **Input container**: `space-y-4 px-4 sm:px-6 lg:px-8`

### Breakpoints
- `sm:` - 640px and up
- `lg:` - 1024px and up

## Best Practices

### 1. Choose the Right Pattern

**Use Values Pattern when:**
- You need complex state management
- You have custom business logic
- You need full control over streaming
- You want to avoid shared hooks complexity

**Use Human Design Pattern when:**
- You want simple, standard chat flow
- You prefer reusable components
- You don't need complex state management
- You want faster development

### 2. Message Structure
```javascript
const message = {
  role: "user" | "assistant",
  content: "Message content",
  timestamp: new Date().toISOString(),
  isGenerating: false, // For streaming
  error: false // For error states
};
```

### 3. Error Handling
```javascript
try {
  // API call
} catch (error) {
  console.error('Error:', error);
  setMessages(prev => [...prev, {
    role: "assistant",
    content: "Sorry, I couldn't process your message. Please try again.",
    error: true
  }]);
}
```

### 4. Cleanup
```javascript
useEffect(() => {
  return () => {
    // Cleanup any ongoing requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };
}, []);
```

### 5. Performance
- Use `useCallback` for event handlers
- Debounce user input if needed
- Implement proper cleanup in `useEffect`
- Avoid unnecessary re-renders

### 6. User Experience
- Show loading states during API calls
- Provide visual feedback for user actions
- Implement proper auto-scroll behavior
- Handle edge cases (empty messages, network issues)

## Implementation Checklist

### Values Pattern (Recommended for Complex Apps)
- [ ] Set up basic layout structure
- [ ] Implement direct state management
- [ ] Add auto-scroll functionality
- [ ] Implement streaming with `useApi`
- [ ] Add loading states
- [ ] Implement error handling
- [ ] Add quick tips functionality
- [ ] Test responsive design
- [ ] Add proper cleanup
- [ ] Add application-specific logic

### Human Design Pattern (Good for Simple Apps)
- [ ] Set up basic layout structure
- [ ] Import shared hooks
- [ ] Add auto-scroll functionality
- [ ] Implement streaming with shared hooks
- [ ] Add loading states
- [ ] Implement error handling
- [ ] Add quick tips functionality
- [ ] Test responsive design
- [ ] Add proper cleanup
- [ ] Configure backend initialization

## Recommended Approach

For new applications, **start with the Values pattern** for better control:

1. Use direct state management with `useApi`
2. Implement custom streaming logic
3. Add application-specific data loading
4. Customize quick tips for your domain
5. Only use shared hooks if you need simple, standard chat flow

This approach provides:
- ✅ Full control over chat behavior
- ✅ Better performance
- ✅ Easier debugging
- ✅ More flexible customization

---

## Common Pitfalls and Solutions

### 1. ⚠️ Header Hiding After First Message

**Problem**: After the first AI message appears, the page auto-scrolls and hides the header behind the top edge of the screen.

**Cause**: Auto-scroll (`scrollIntoView`) triggers on **every** message, including the first one. When the first message appears, the page scrolls to `messagesEndRef` (at the bottom), pushing the header out of view.

**Solution**: Only trigger auto-scroll when `messages.length > 1`:

```javascript
// ❌ WRONG - scrolls even for first message
useEffect(() => {
  messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
}, [messages]);

// ✅ CORRECT - skips first message
useEffect(() => {
  if (messages.length > 1) {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }
}, [messages]);
```

**Why this works**:
- First message (length === 1): No scroll, header stays visible
- Subsequent messages (length > 1): Auto-scroll to latest message
- User can see header and "Back" button immediately

**Tested in**: Values chat, Human Design chat, Spiral chat

---

### 2. Chat Layout with WorkshopLayout

**Problem**: Chat pages need sticky input at the bottom, but should use `WorkshopLayout` for consistent width and back button positioning.

**Solution**: Use `WorkshopLayout` for all pages (including chat) and implement sticky input within the content:

```javascript
// In layout.js - ALL pages use WorkshopLayout
function AppLayoutContent({ children }) {
  const pathname = usePathname();
  const width = "default";
  const showBackButton = true;
  
  const handleBack = () => {
    const isInitPage = pathname?.includes('/init');
    
    if (isInitPage) {
      window.location.href = '/';
    } else {
      window.history.back();
    }
  };
  
  return (
    <WorkshopLayout 
      background="gray"
      width={width}
      showBackButton={showBackButton}
      backButtonProps={{ onClick: handleBack }}
    >
      {children}
    </WorkshopLayout>
  );
}
```

**In chat page**:
```javascript
return (
  <div className="flex flex-col min-h-[calc(100vh-16rem)]">
    {/* Chat messages area */}
    <div className="flex-1 overflow-y-auto">
      <div className="space-y-6 pt-8 pb-20">
        {/* Messages */}
        {messages.map((message, index) => (
          <ChatBubble key={index} role={message.role}>
            {message.content}
          </ChatBubble>
        ))}
        <div ref={messagesEndRef} />
      </div>
    </div>
    
    {/* Input area – sticky at bottom */}
    <div className="bg-gray-50 sticky bottom-0 pb-4">
      <div className="space-y-4">
        <div className="flex gap-2 justify-end">
          {quickTips.map((tip, index) => (
            <QuickChip key={index} label={tip.label} onClick={tip.onClick} />
          ))}
        </div>
        <ChatInput onSend={handleSendMessage} disabled={isStreaming} />
      </div>
    </div>
  </div>
);
```

**Key elements**:
- `WorkshopLayout` provides consistent width, background, and back button
- `flex flex-col min-h-[calc(100vh-16rem)]`: Container with flexible height
- `pt-8`: Top padding (2rem) for spacing below back button
- `pb-20`: Bottom padding (5rem) to ensure space for sticky input
- `bg-gray-50 sticky bottom-0 pb-4`: Sticky input with matching background
- No custom back button needed - provided by `WorkshopLayout`

**Why this approach**:
- ✅ Consistent width across all pages (init, chat)
- ✅ Consistent back button positioning
- ✅ Sticky input at the bottom
- ✅ No duplicate layout code
- ✅ Easier to maintain

---

### 3. Stream Not Working

If streaming appears to not work (receiving full response at once), check:

1. **Backend**: Ensure using `StreamingResponse` with `text/event-stream`
2. **Frontend**: Use `ReadableStream` reader pattern
3. **CORS**: Ensure backend allows streaming from frontend origin

---

### 4. Messages Disappearing

If messages appear then disappear, check:

1. **`isGenerating` flag**: Must be set to `false` after content is received
2. **Placeholder messages**: Must have `content: ""` initially
3. **Message updates**: Use correct index when updating assistant message

---

## Checklist for New Chat Implementation

When implementing a new chat application, ensure:

- [ ] Layout: ALL pages (including chat) use `WorkshopLayout` from parent layout
- [ ] Layout: Chat page container uses `flex flex-col min-h-[calc(100vh-16rem)]`
- [ ] Back button: Provided by `WorkshopLayout` (no custom button needed)
- [ ] Messages container: Has `pt-8` for top padding (spacing below back button)
- [ ] Messages container: Has `pb-20` for bottom padding (space for sticky input)
- [ ] Auto-scroll: Only triggers when `messages.length > 1` ⚠️ IMPORTANT
- [ ] Input area: Uses `bg-gray-50 sticky bottom-0 pb-4` for sticky positioning
- [ ] Input area: Background color matches `WorkshopLayout` background
- [ ] Streaming: Implements proper `ReadableStream` handling
- [ ] State: Uses `isStreaming` to prevent concurrent requests
- [ ] Refs: Includes `messagesEndRef` for scroll target
- [ ] Backend: Chat personality file exists in `app/personality/`
- [ ] Backend: Endpoints follow pattern: `POST /app/chat/` for init, `POST /app/chat/{sessionId}/stream` for messages
