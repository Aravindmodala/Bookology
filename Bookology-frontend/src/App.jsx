import React from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import Generator from './generator';
import BookologyHome from './bookologyhome';

function HomeWrapper() {
  const navigate = useNavigate();
  return <BookologyHome onStart={() => navigate('/generator')} />;
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomeWrapper />} />
        <Route path="/generator" element={<Generator />} />
      </Routes>
    </Router>
  );
}

export default App;