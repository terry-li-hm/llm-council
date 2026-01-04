import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import Settings from './components/Settings';
import Login from './components/Login';
import { api } from './api';
import { useTheme } from './utils/useTheme';
import './App.css';

// LocalStorage key for persisting settings
const DUPLICATE_MODELS_KEY = 'llm-council-duplicate-models';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  // Settings state
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [availableModels, setAvailableModels] = useState([]);
  const [duplicateModels, setDuplicateModels] = useState(() => {
    // Load from localStorage on init
    try {
      const saved = localStorage.getItem(DUPLICATE_MODELS_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  // Auth state
  const [authStatus, setAuthStatus] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  // Check auth status on mount
  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const status = await api.getAuthStatus();
      setAuthStatus(status);
    } catch {
      // Fall back to requiring auth on error
      setAuthStatus({ authenticated: false, auth_enabled: true });
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      // Logout failed, but clear local state anyway
    }
    setAuthStatus({ authenticated: false, auth_enabled: true });
    setConversations([]);
    setCurrentConversation(null);
    setCurrentConversationId(null);
  };

  // Load conversations and models on mount (only if authenticated)
  useEffect(() => {
    if (authStatus?.authenticated || authStatus?.auth_enabled === false) {
      loadConversations();
      loadModels();
    }
  }, [authStatus]);

  // Save duplicate models to localStorage when changed
  useEffect(() => {
    localStorage.setItem(DUPLICATE_MODELS_KEY, JSON.stringify(duplicateModels));
  }, [duplicateModels]);

  const loadModels = async () => {
    try {
      const models = await api.getModels();
      setAvailableModels(models);
    } catch {
      // Models will remain empty; settings will show no options
    }
  };


  // Load conversation details when selected
  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch {
      // Conversations will remain empty
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
    } catch {
      // Conversation will remain null
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await api.createConversation();
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, message_count: 0 },
        ...conversations,
      ]);
      setCurrentConversationId(newConv.id);
    } catch {
      // Failed to create conversation; user can retry
    }
  };

  const handleSelectConversation = (id) => {
    setCurrentConversationId(id);
    setSidebarOpen(false); // Close sidebar on mobile after selection
  };

  const handleSendMessage = async (content) => {
    if (!currentConversationId) return;

    const isFirstMessage = currentConversation?.messages?.length === 0;

    setIsLoading(true);
    try {
      // Optimistically add user message to UI
      const userMessage = { role: 'user', content };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
      }));

      if (isFirstMessage) {
        // First message: use streaming for full 3-stage deliberation
        const assistantMessage = {
          role: 'assistant',
          stage1: null,
          stage2: null,
          stage3: null,
          metadata: null,
          loading: {
            stage1: false,
            stage2: false,
            stage3: false,
          },
        };

        setCurrentConversation((prev) => ({
          ...prev,
          messages: [...prev.messages, assistantMessage],
        }));

        await api.sendMessageStream(currentConversationId, content, (eventType, event) => {
          switch (eventType) {
            case 'stage1_start':
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.loading.stage1 = true;
                return { ...prev, messages };
              });
              break;

            case 'stage1_complete':
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.stage1 = event.data;
                lastMsg.loading.stage1 = false;
                return { ...prev, messages };
              });
              break;

            case 'stage2_start':
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.loading.stage2 = true;
                return { ...prev, messages };
              });
              break;

            case 'stage2_complete':
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.stage2 = event.data;
                lastMsg.metadata = event.metadata;
                lastMsg.loading.stage2 = false;
                return { ...prev, messages };
              });
              break;

            case 'stage3_start':
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.loading.stage3 = true;
                return { ...prev, messages };
              });
              break;

            case 'stage3_complete':
              setCurrentConversation((prev) => {
                const messages = [...prev.messages];
                const lastMsg = messages[messages.length - 1];
                lastMsg.stage3 = event.data;
                lastMsg.loading.stage3 = false;
                return { ...prev, messages };
              });
              break;

            case 'title_complete':
              loadConversations();
              break;

            case 'complete':
              loadConversations();
              setIsLoading(false);
              break;

            case 'error':
              // Stream error occurred; stop loading
              setIsLoading(false);
              break;

            default:
              // Ignore unknown event types
          }
        }, duplicateModels);
      } else {
        // Follow-up: use non-streaming endpoint (faster, simpler)
        const assistantMessage = {
          role: 'assistant',
          type: 'followup',
          response: null,
          loading: true,
        };

        setCurrentConversation((prev) => ({
          ...prev,
          messages: [...prev.messages, assistantMessage],
        }));

        const result = await api.sendMessage(currentConversationId, content, duplicateModels);

        setCurrentConversation((prev) => {
          const messages = [...prev.messages];
          const lastMsg = messages[messages.length - 1];
          lastMsg.response = result.response;
          lastMsg.loading = false;
          return { ...prev, messages };
        });

        setIsLoading(false);
      }
    } catch {
      // Remove optimistic messages on error
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
    }
  };

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="app loading">
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  // Show login if auth is enabled and user is not authenticated
  if (authStatus?.auth_enabled && !authStatus?.authenticated) {
    return <Login />;
  }

  return (
    <div className="app">
      {/* Mobile header with hamburger menu */}
      <div className="mobile-header">
        <button
          className="hamburger-btn"
          onClick={() => setSidebarOpen(true)}
          aria-label="Open menu"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>
        <h1 className="mobile-title">LLM Council</h1>
      </div>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <Sidebar
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={handleSelectConversation}
        onNewConversation={handleNewConversation}
        onOpenSettings={() => setSettingsOpen(true)}
        theme={theme}
        onToggleTheme={toggleTheme}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        duplicateModelsCount={duplicateModels.length}
        username={authStatus?.username}
        authEnabled={authStatus?.auth_enabled}
        onLogout={handleLogout}
      />
      <ChatInterface
        conversation={currentConversation}
        onSendMessage={handleSendMessage}
        isLoading={isLoading}
      />
      <Settings
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        models={availableModels}
        duplicateModels={duplicateModels}
        onDuplicateModelsChange={setDuplicateModels}
      />
    </div>
  );
}

export default App;
