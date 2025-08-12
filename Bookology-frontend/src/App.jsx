import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
// Removed old BookologyHome landing in favor of new cinematic page
import LandingPage from './components/LandingPage';
import Auth from './Auth';
// Legacy editor kept only for fallback; not used by default
import StoryEditor from './StoryEditor';
import MinimalEditor from './MinimalEditor';
import StoryDashboard from './components/StoryDashboard';
import StoryCreator from './StoryCreator';
import ExplorePage from './components/ExplorePage';
import Page from './components/Page';
import Layout from './components/Layout';
import EditorLayout from './components/EditorLayout';
import { AuthProvider } from './AuthContext';
import ErrorBoundary from './ErrorBoundary';
import './styles/enhancedComponents.css';

function StoriesWrapper() {
  const navigate = useNavigate();
  return <StoryDashboard onStartNewStory={() => navigate('/create')} />;
}

function AppRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait" initial={false}>
      <Routes location={location} key={location.pathname}>
        <Route element={<Layout />}>
          <Route path="/" element={<Page><LandingPage /></Page>} />
          <Route path="/stories" element={<Page><StoriesWrapper /></Page>} />
          <Route path="/create" element={<Page><StoryCreator /></Page>} />
          <Route path="/explore" element={<Page><ExplorePage /></Page>} />
          <Route path="/login" element={<Page><Auth /></Page>} />
        </Route>
        <Route element={<EditorLayout />}>
          {/* MinimalEditor becomes the main editor */}
          <Route path="/editor" element={<Page><MinimalEditor /></Page>} />
          <Route path="/editor-legacy" element={<Page><StoryEditor /></Page>} />
          <Route path="/minimal-editor" element={<Page><MinimalEditor /></Page>} />
          <Route path="/minimal-editor/:storyId" element={<Page><MinimalEditor /></Page>} />
          <Route path="/story/:storyId" element={<Page><MinimalEditor /></Page>} />
        </Route>
      </Routes>
    </AnimatePresence>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Router>
          <AppRoutes />
        </Router>
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;