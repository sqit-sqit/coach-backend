# 🎨 Values Layout Template

## 📋 **Overview**

This document describes the complete layout structure used in the Values application, serving as a ready-to-use template for other applications (Human Design, Spiral, etc.).

## 🏗️ **Layout Architecture**

### **1. Main Layout Structure**
```
app/{app_name}/layout.js
├── WorkshopLayout (base component)
├── BackButton (conditional)
├── Width management
└── Background management
```

### **2. Component Hierarchy**
```
WorkshopLayout
├── Background (white/gray/gradient)
├── Container (width management)
├── BackButton (conditional)
└── Children (page content)
```

## 📁 **File Structure**

### **Required Files:**
```
src/app/{app_name}/
├── layout.js                    # Main layout wrapper
├── init/page.js                 # Initialization page
├── chat/page.js                # Chat interface
└── [other pages]/page.js        # Additional pages

src/components/layouts/
└── WorkshopLayout.jsx           # Reusable layout component
```

## 🎯 **Implementation Guide**

### **Step 1: Create Layout File**
**File:** `src/app/{app_name}/layout.js`

```javascript
"use client";

import { Suspense } from "react";
import WorkshopLayout from "../../components/layouts/WorkshopLayout";
import { usePathname, useSearchParams } from "next/navigation";

function {AppName}LayoutContent({ children }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const step = searchParams?.get('step');
  
  // Customize width for specific pages
  const isSpecialPage = pathname?.includes('/special-page');
  const width = isSpecialPage ? "wide" : "default";
  
  // Show back button logic
  const isInitPage = pathname?.includes('/init');
  const isInitStep1 = isInitPage && (!step || step === '1');
  const showBackButton = !isInitStep1;
  
  // Custom back button logic
  const handleBack = () => {
    if (isInitPage && step) {
      const currentStep = parseInt(step, 10);
      if (currentStep > 1) {
        window.location.href = `/{app_name}/init?step=${currentStep - 1}`;
      } else {
        window.location.href = '/';
      }
    } else {
      window.history.back();
    }
  };
  
  return (
    <WorkshopLayout 
      background="gray"           // "white", "gray", "gradient"
      width={width}              // "narrow", "default", "wide", "game"
      showBackButton={showBackButton}
      backButtonProps={{ onClick: handleBack }}
    >
      {children}
    </WorkshopLayout>
  );
}

export default function {AppName}Layout({ children }) {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <{AppName}LayoutContent>{children}</{AppName}LayoutContent>
    </Suspense>
  );
}
```

### **Step 2: WorkshopLayout Component**
**File:** `src/components/layouts/WorkshopLayout.jsx`

```jsx
import BackButton from "../ui/BackButton";

export default function WorkshopLayout({ 
  children, 
  className = "",
  width = "default",     // "narrow", "default", "wide", "game"
  background = "white",  // "white", "gray", "gradient"
  showBackButton = false,
  backButtonProps = {}
}) {
  const widthClasses = {
    narrow: "max-w-3xl",    // For text content
    default: "max-w-4xl",   // Standard width
    wide: "max-w-5xl",      // For forms/feedback
    game: "max-w-6xl"       // For games/interactive content
  };
  
  const backgroundClasses = {
    white: "bg-white",
    gray: "bg-gray-50", 
    gradient: "bg-gradient-to-br from-purple-50 to-blue-50"
  };
  
  return (
    <div className={`${backgroundClasses[background]} min-h-screen`}>
      <div className={`${widthClasses[width]} mx-auto w-full px-6 py-8 ${className} relative`}>
        {showBackButton && (
          <div className="absolute top-4 left-4 z-20">
            <BackButton {...backButtonProps} />
          </div>
        )}
        {children}
      </div>
    </div>
  );
}
```

### **Step 3: Page Structure Template**
**File:** `src/app/{app_name}/init/page.js`

```javascript
"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Button from "components/ui/Button";
import Heading from "components/ui/Heading";
import ExpandableInfo from "components/ui/ExpandableInfo";
import AuthChoiceModal from "components/AuthChoiceModal";
import { useAuth } from "hooks/useAuth";
import { getCurrentUserId } from "lib/guestUser";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export const dynamic = "force-dynamic";

// Main content component
function InitContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { userId: authUserId, isAuthenticated, isLoading } = useAuth();

  const [userId, setUserId] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  
  useEffect(() => {
    if (!isLoading) {
      const hasGuestId = typeof window !== 'undefined' && localStorage.getItem('guest_user_id');
      
      if (!authUserId && !hasGuestId) {
        setShowAuthModal(true);
      } else {
        const id = getCurrentUserId(authUserId);
        setUserId(id);
      }
    }
  }, [authUserId, isLoading]);
  
  const handleContinueAsGuest = () => {
    const id = getCurrentUserId(null);
    setUserId(id);
    setShowAuthModal(false);
  };
  
  const handleSignIn = () => {
    setShowAuthModal(false);
    // Auth will be handled by useAuth hook
  };

  // Your page content here
  return (
    <>
      <Heading level={1} className="text-center mb-8">
        {App Name} Workshop
      </Heading>
      
      <div className="bg-white rounded-xl shadow-lg p-8">
        {/* Your content */}
      </div>
      
      {showAuthModal && (
        <AuthChoiceModal
          onContinueAsGuest={handleContinueAsGuest}
          onSignIn={handleSignIn}
        />
      )}
    </>
  );
}

// Wrapper with Suspense
export default function InitPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <InitContent />
    </Suspense>
  );
}
```

### **Step 4: Chat Page Template**
**File:** `src/app/{app_name}/chat/page.js`

```javascript
"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import ChatBubble from "components/ui/ChatBubble";
import ChatInput from "components/ui/ChatInput";
import QuickChip from "components/ui/QuickChip";
import { useAuth } from "hooks/useAuth";
import { useApi } from "hooks/useApi";
import { getCurrentUserId } from "lib/guestUser";

export default function {AppName}ChatPage() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading } = useAuth();
  const { userId: authUserId, apiPostStream, apiPost, apiGet } = useApi();
  
  const [messages, setMessages] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [userId, setUserId] = useState(null);
  
  useEffect(() => {
    if (!isLoading) {
      const id = getCurrentUserId(authUserId);
      setUserId(id);
    }
  }, [authUserId, isLoading]);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (messages.length > 1) {
      scrollToBottom();
    }
  }, [messages]);

  // Your chat logic here

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 bg-white rounded-lg shadow-md mb-4 custom-scrollbar">
        {messages.map((msg, index) => (
          <ChatBubble key={index} role={msg.role} content={msg.content} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <ChatInput
        onSend={handleSendMessage}
        disabled={isStreaming}
      />
    </div>
  );
}
```

## 🎨 **Layout Configuration Options**

### **Width Options:**
- `narrow` (max-w-3xl) - For text content, articles
- `default` (max-w-4xl) - Standard width for most pages
- `wide` (max-w-5xl) - For forms, feedback, data display
- `game` (max-w-6xl) - For interactive content, games

### **Background Options:**
- `white` - Clean white background
- `gray` - Light gray background (bg-gray-50)
- `gradient` - Purple to blue gradient

### **Back Button Logic:**
- **Always show** except on initial step 1
- **Custom logic** for step navigation
- **Browser back** for other pages
- **Conditional display** based on pathname

### **Back Button Positioning:**
- **Position**: `absolute top-4 left-4 z-20`
- **Container**: Inside the main content wrapper with `relative` positioning
- **Styling**: Gray text with blue hover, arrow icon + "Back" text
- **Z-index**: `z-20` to ensure it appears above content
- **Responsive**: Fixed position regardless of content scroll

### **Back Button Implementation Details:**
```jsx
// WorkshopLayout.jsx - Back Button Container
{showBackButton && (
  <div className="absolute top-4 left-4 z-20">
    <BackButton {...backButtonProps} />
  </div>
)}

// BackButton.js - Component Styling
<button
  onClick={onClick}
  className="flex items-center space-x-2 text-gray-700 hover:text-blue-600 focus:outline-none focus:ring-0"
>
  <span className="text-2xl">←</span>
  <span className="text-base font-medium">Back</span>
</button>
```

### **Back Button Behavior by Page Type:**
- **Init Step 1**: Hidden (no back button)
- **Init Step 2+**: Navigate to previous step
- **Chat Pages**: Browser back navigation
- **Other Pages**: Browser back navigation

## 🔧 **Customization Points**

### **1. App-Specific Styling**
```javascript
// In layout.js
const background = "gray";  // Change per app
const width = "default";    // Adjust per page type
```

### **2. Navigation Logic**
```javascript
// Customize back button behavior
const handleBack = () => {
  // App-specific navigation logic
};
```

### **3. Page-Specific Widths**
```javascript
// Different widths for different pages
const isGamePage = pathname?.includes('/game');
const width = isGamePage ? "game" : "default";
```

### **4. Back Button Customization**
```javascript
// Custom back button positioning
const backButtonClasses = "absolute top-6 left-6 z-20"; // Custom position
const backButtonStyle = { top: '24px', left: '24px' }; // Custom styling

// Custom back button behavior
const handleBack = () => {
  // App-specific navigation logic
  if (isSpecialPage) {
    router.push('/special-route');
  } else {
    window.history.back();
  }
};
```

## 📋 **Required Components**

### **UI Components:**
- `Button` - Primary action buttons
- `Heading` - Page headings
- `ChatBubble` - Chat message display
- `ChatInput` - Message input
- `QuickChip` - Quick action buttons
- `BackButton` - Navigation button
- `ExpandableInfo` - Collapsible information

### **Layout Components:**
- `WorkshopLayout` - Main layout wrapper
- `AuthChoiceModal` - Authentication choice

### **Hooks:**
- `useAuth` - Authentication state
- `useApi` - API communication
- `getCurrentUserId` - User ID management

## 🚀 **Usage Examples**

### **Values Application:**
```javascript
// layout.js
<WorkshopLayout 
  background="gray" 
  width={isGamePage ? "game" : "default"}
  showBackButton={showBackButton}
  backButtonProps={{ onClick: handleBack }}
>
```

### **Human Design Application:**
```javascript
// layout.js
<WorkshopLayout 
  background="gradient" 
  width="default"
  showBackButton={true}
  backButtonProps={{ href: "/hd/init" }}
>
```

### **Spiral Application:**
```javascript
// layout.js
<WorkshopLayout 
  background="gray" 
  width="default"
  showBackButton={true}
  backButtonProps={{ href: "/spiral/init" }}
>
```

## 📝 **Best Practices**

1. **Consistent Naming** - Use `{AppName}Layout` pattern
2. **Suspense Wrapper** - Always wrap with Suspense for searchParams
3. **Width Management** - Choose appropriate width for content type
4. **Back Button Logic** - Implement consistent navigation
5. **Authentication** - Handle both authenticated and guest users
6. **Error Handling** - Include loading states and error boundaries

## 🔄 **Migration Guide**

To migrate an existing app to use this layout:

1. **Create layout.js** using the template
2. **Update page components** to remove layout code
3. **Adjust width/background** for app-specific needs
4. **Test navigation** and back button behavior
5. **Verify responsive design** on different screen sizes

This template provides a solid foundation for consistent, responsive layouts across all applications in the Coach system.
