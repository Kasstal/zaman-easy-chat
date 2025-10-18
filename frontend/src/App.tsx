import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { UserProvider } from './contexts/UserContext';
import ChatPage from './ChatPage';
import GoalsPage from './GoalsPage';

const App: React.FC = () => {
  return (
    <UserProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<Navigate to="/chat" replace />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/goals" element={<GoalsPage />} />
          </Routes>
        </div>
      </Router>
    </UserProvider>
  );
};

export default App;
