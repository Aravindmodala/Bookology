import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import BookologyHome from './bookologyhome';
import Auth from './Auth';
import StoryEditor from './StoryEditor';
import StoryDashboard from './components/StoryDashboard';
import StoryCreator from './StoryCreator';
import { AuthProvider } from './AuthContext';
import ErrorBoundary from './ErrorBoundary';

function HomeWrapper() {
  const navigate = useNavigate();
  return <BookologyHome onStart={() => navigate('/stories')} />;
}

function StoriesWrapper() {
  const navigate = useNavigate();
  return <StoryDashboard onStartNewStory={() => navigate('/create')} />;
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/" element={<HomeWrapper />} />
            <Route path="/stories" element={<StoriesWrapper />} />
            <Route path="/create" element={<StoryCreator />} />
            <Route path="/editor" element={<StoryEditor />} />
            <Route path="/login" element={<Auth />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;