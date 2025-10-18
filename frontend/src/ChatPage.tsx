import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from './contexts/UserContext';

interface Message {
  id: string;
  role: string;
  content: string;
  chat_id: string;
  created_at: string;
}

interface ChatRequest {
  user_id: string;
  message: string;
}

interface ChatResponse {
  response: string;
  message_id: string;
}

const ChatPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useUser();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);

  // Load chat history when user changes
  useEffect(() => {
    if (user) {
      loadChatHistory();
    } else {
      setMessages([]);
    }
  }, [user]);

  const loadChatHistory = async () => {
    if (!user) return;
    
    setIsLoading(true);
    try {
      const response = await fetch(`http://localhost:8000/chatbot/messages/${user.id}`);
      if (response.ok) {
        const chatHistory: Message[] = await response.json();
        setMessages(chatHistory);
      } else {
        console.error('Failed to load chat history');
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (messageText: string) => {
    if (!user) return;

    const chatRequest: ChatRequest = {
      user_id: user.id,
      message: messageText
    };

    try {
      const response = await fetch('http://localhost:8000/chatbot/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(chatRequest),
      });

      if (response.ok) {
        await response.json();
        // Reload chat history to get the latest messages
        await loadChatHistory();
      } else {
        const errorData = await response.json();
        console.error('Chat error:', errorData);
        // You could show an error message to the user here
      }
    } catch (error) {
      console.error('Network error:', error);
      // You could show an error message to the user here
    }
  };

  const handleSendMessage = async () => {
    if (inputValue.trim() && user && !isSending) {
      setIsSending(true);
      const messageToSend = inputValue.trim();
      setInputValue(''); // Clear input immediately for better UX
      
      await sendMessage(messageToSend);
      setIsSending(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900 p-4">
      {/* Mobile Phone Container */}
      <div className="relative flex h-[812px] w-full max-w-[375px] flex-col overflow-hidden rounded-[2.5rem] border-8 border-gray-800 dark:border-gray-700 shadow-2xl bg-gradient-to-br from-background-light via-zaman-green/5 to-background-light dark:from-background-dark dark:via-zaman-green/10 dark:to-background-dark">
        {/* Notch */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-6 bg-gray-800 dark:bg-gray-700 rounded-b-2xl z-50"></div>
        
        {/* Content Area */}
        <div className="flex-grow flex flex-col h-full overflow-hidden pt-6">
        <header className="sticky top-0 z-10 flex items-center bg-background-light/80 dark:bg-background-dark/80 backdrop-blur-sm p-4 pb-2 justify-center">
          <div className="text-center">
            <h1 className="text-lg font-bold text-gray-900 dark:text-white">Chat</h1>
            {user && (
              <p className="text-xs text-gray-600 dark:text-gray-400">Welcome, {user.username}</p>
            )}
          </div>
        </header>
        
        <main className="flex-1 overflow-y-auto p-4 space-y-4">
          {!user && (
            <div className="bg-gradient-to-r from-zaman-green/10 to-zaman-solar/10 border border-zaman-green/20 rounded-lg p-4 text-center">
              <p className="text-zaman-green dark:text-zaman-green font-medium">
                👋 Please create a user account in the Goals tab to get started!
              </p>
            </div>
          )}
          
          {isLoading && user && (
            <div className="flex justify-center items-center py-8">
              <div className="flex items-center gap-2 text-zaman-green">
                <svg className="animate-spin" fill="currentColor" height="20" viewBox="0 0 256 256" width="20" xmlns="http://www.w3.org/2000/svg">
                  <path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm0,192a88,88,0,1,1,88-88A88.1,88.1,0,0,1,128,216Z" opacity="0.2"></path>
                  <path d="M232,128a104,104,0,0,1-208,0c0-41,23.81-78.36,60.66-95.27a8,8,0,0,1,6.68,14.54C60.15,61.59,40,93.27,40,128a88,88,0,0,0,176,0c0-34.73-20.15-66.41-51.34-80.73a8,8,0,0,1,6.68-14.54C208.19,49.64,232,87,232,128Z"></path>
                </svg>
                <span>Loading chat history...</span>
              </div>
            </div>
          )}
          
          {!isLoading && messages.length === 0 && user && (
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-zaman-gradient flex items-center justify-center text-gray-800 font-bold text-xl shadow-lg">
                AI
              </div>
              <p className="text-subtle-light dark:text-subtle-dark">
                Welcome! I'm your AI banking assistant. How can I help you today?
              </p>
            </div>
          )}
          
          {messages.map((message) => (
            <div key={message.id} className={`flex items-end gap-3 ${message.role === 'user' ? 'justify-end' : ''}`}>
              {message.role !== 'user' && (
                <div className="w-8 h-8 rounded-full bg-zaman-gradient flex items-center justify-center text-gray-800 font-bold text-sm shadow-lg">
                  AI
                </div>
              )}
              
              <div className={`flex flex-1 flex-col gap-1 ${message.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`${
                  message.role === 'user'
                    ? 'bg-gradient-to-r from-user-bubble-light to-zaman-green/10 dark:from-user-bubble-dark dark:to-zaman-green/20 text-user-text-light dark:text-user-text-dark rounded-xl rounded-br-none border border-zaman-green/20'
                    : 'bg-gradient-to-r from-assistant-bubble-light to-zaman-green/5 dark:from-assistant-bubble-dark dark:to-zaman-green/10 text-assistant-text-light dark:text-assistant-text-dark rounded-xl rounded-bl-none border border-zaman-green/10'
                } px-4 py-3 max-w-[80%] shadow-sm`}>
                  <p className="text-base leading-relaxed">{message.content}</p>
                </div>
              </div>
            </div>
          ))}
        </main>
        
        <footer className="bg-background-light dark:bg-background-dark pt-2 pb-2 px-4">
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <input 
              className="form-input w-full resize-none overflow-hidden rounded-full h-12 pl-5 pr-12 text-base font-normal leading-normal bg-input-bg-light dark:bg-input-bg-dark text-input-text-light dark:text-input-text-dark placeholder:text-input-placeholder-light dark:placeholder:text-input-placeholder-dark border-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50" 
              placeholder={user ? "Type a message..." : "Please create a user account first..."}
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={!user || isSending}
            />
            <button 
              onClick={handleSendMessage}
              disabled={!user || !inputValue.trim() || isSending}
              className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center justify-center h-9 w-9 rounded-full bg-zaman-gradient text-gray-800 hover:opacity-90 transition-opacity shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSending ? (
                <svg className="animate-spin" fill="currentColor" height="16px" viewBox="0 0 256 256" width="16px" xmlns="http://www.w3.org/2000/svg">
                  <path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm0,192a88,88,0,1,1,88-88A88.1,88.1,0,0,1,128,216Z" opacity="0.2"></path>
                  <path d="M232,128a104,104,0,0,1-208,0c0-41,23.81-78.36,60.66-95.27a8,8,0,0,1,6.68,14.54C60.15,61.59,40,93.27,40,128a88,88,0,0,0,176,0c0-34.73-20.15-66.41-51.34-80.73a8,8,0,0,1,6.68-14.54C208.19,49.64,232,87,232,128Z"></path>
                </svg>
              ) : (
                <svg fill="currentColor" height="20px" viewBox="0 0 256 256" width="20px" xmlns="http://www.w3.org/2000/svg">
                  <path d="M231.87,114l-168-95.89A16,16,0,0,0,40.92,37.34L71.55,128,40.92,218.66A16,16,0,0,0,63.87,237.89l168-95.89a16,16,0,0,0,0-27.78ZM56,208.69l26.34-75.53L125,128,82.34,122.84Z"></path>
                </svg>
              )}
            </button>
          </div>
        </div>
        
        {/* Navigation Footer */}
        <div className="bg-surface-light/80 dark:bg-surface-dark/80 backdrop-blur-lg border-t border-zaman-green/10">
          <nav className="flex justify-center p-2 gap-4">
            <button 
              className="flex flex-col items-center justify-center gap-1 p-2 rounded-lg bg-zaman-gradient text-gray-800 w-24 shadow-lg"
            >
              <svg fill="currentColor" height="24" viewBox="0 0 256 256" width="24" xmlns="http://www.w3.org/2000/svg">
                <path d="M216,80H184V48a16,16,0,0,0-16-16H40A16,16,0,0,0,24,48V176a8,8,0,0,0,13,6.22L72,154V184a16,16,0,0,0,16,16h93.59L219,230.22a8,8,0,0,0,5,1.78,8,8,0,0,0,8-8V96A16,16,0,0,0,216,80ZM66.55,137.78,40,159.25V48H168v88H71.58A8,8,0,0,0,66.55,137.78ZM216,207.25l-26.55-21.47a8,8,0,0,0-5-1.78H88V152h80a16,16,0,0,0,16-16V96h32Z"></path>
              </svg>
              <span className="text-xs font-bold">Chat</span>
            </button>
            <button 
              onClick={() => navigate('/goals')}
              className="flex flex-col items-center justify-center gap-1 p-2 rounded-lg text-subtle-light dark:text-subtle-dark w-24"
            >
              <svg fill="currentColor" height="24" viewBox="0 0 256 256" width="24" xmlns="http://www.w3.org/2000/svg">
                <path d="M232,64H208V56a16,16,0,0,0-16-16H64A16,16,0,0,0,48,56v8H24A16,16,0,0,0,8,80V96a40,40,0,0,0,40,40h3.65A80.13,80.13,0,0,0,120,191.61V216H96a8,8,0,0,0,0,16h64a8,8,0,0,0,0-16H136V191.58c31.94-3.23,58.44-25.64,68.08-55.58H208a40,40,0,0,0,40-40V80A16,16,0,0,0,232,64ZM48,120A24,24,0,0,1,24,96V80H48v32q0,4,.39,8ZM232,96a24,24,0,0,1-24,24h-.5a81.81,81.81,0,0,0,.5-8.9V80h24Z"></path>
              </svg>
              <span className="text-xs font-medium">Goals</span>
            </button>
          </nav>
        </div>
      </footer>
      </div>
    </div>
    </div>
  );
};

export default ChatPage;