import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, useNavigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
// Removed old BookologyHome landing in favor of new cinematic page
const LandingPage = lazy(() => import('./components/LandingPage'));
const Auth = lazy(() => import('./Auth'));
// Legacy editor kept only for fallback; not used by default
const MinimalEditor = lazy(() => import('./MinimalEditor'));
const StoryDashboard = lazy(() => import('./components/StoryDashboard'));
const StoryCreator = lazy(() => import('./StoryCreator'));
const ExplorePage = lazy(() => import('./components/explore/ExplorePage'));
const StoryView = lazy(() => import('./components/StoryView'));
import Page from './components/Page';
import Layout from './components/Layout';
import EditorLayout from './components/EditorLayout';
import { AuthProvider } from './AuthContext';
import ErrorBoundary from './ErrorBoundary';
import './styles/enhancedComponents.css';

function StoriesWrapper() {
  const navigate = useNavigate();
  return <StoryDashboard onStartNewStory={() => navigate('/create', { state: { flow: 'ai' } })} />;
}

function AppRoutes() {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait" initial={false}>
      <Suspense fallback={<div style={{padding:'2rem'}}>Loading…</div>}>
      <Routes location={location} key={location.pathname}>
        <Route element={<Layout />}>
          <Route path="/" element={<Page><LandingPage /></Page>} />
          <Route path="/stories" element={<Page><StoriesWrapper /></Page>} />
          <Route path="/create" element={<Page><StoryCreator /></Page>} />
          <Route path="/explore" element={<Page><ExplorePage /></Page>} />
          <Route path="/story/:storyId" element={<Page><StoryView /></Page>} />
          <Route path="/login" element={<Page><Auth /></Page>} />
        </Route>
        <Route element={<EditorLayout />}>
          {/* MinimalEditor becomes the main editor */}
          <Route path="/editor" element={<Page><MinimalEditor /></Page>} />
          <Route path="/minimal-editor" element={<Page><MinimalEditor /></Page>} />
          <Route path="/minimal-editor/:storyId" element={<Page><MinimalEditor /></Page>} />
        </Route>
      </Routes>
      </Suspense>
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