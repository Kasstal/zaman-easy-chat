import React, { createContext, useContext, useState, useEffect } from 'react';

interface UserResponse {
  username: string;
  id: string;
  created_at: string;
}

interface UserContextType {
  user: UserResponse | null;
  setUser: (user: UserResponse | null) => void;
  isLoading: boolean;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const useUser = () => {
  const context = useContext(UserContext);
  if (context === undefined) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUserState] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load user from localStorage on component mount
  useEffect(() => {
    const savedUser = localStorage.getItem('zamanUser');
    if (savedUser) {
      try {
        const parsedUser = JSON.parse(savedUser);
        setUserState(parsedUser);
      } catch (error) {
        console.error('Error parsing saved user:', error);
        localStorage.removeItem('zamanUser');
      }
    }
    setIsLoading(false);
  }, []);

  // Save user to localStorage whenever user changes
  const setUser = (newUser: UserResponse | null) => {
    setUserState(newUser);
    if (newUser) {
      localStorage.setItem('zamanUser', JSON.stringify(newUser));
    } else {
      localStorage.removeItem('zamanUser');
    }
  };

  const value = {
    user,
    setUser,
    isLoading,
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
};