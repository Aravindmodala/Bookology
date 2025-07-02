import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import Generator from './generator';
import BookologyHome from './bookologyhome';
import Auth from './Auth';
import { AuthProvider } from './AuthContext';
import ErrorBoundary from './ErrorBoundary';

function HomeWrapper() {
  const navigate = useNavigate();
  return <BookologyHome onStart={() => navigate('/generator')} />;
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/" element={<HomeWrapper />} />
            <Route path="/generator" element={<Generator />} />
            <Route path="/login" element={<Auth />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;