import React from 'react';

function App() {
  return (
    <div style={{ fontFamily: 'sans-serif', minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Hero Section */}
      <header style={{ background: 'linear-gradient(90deg, #667eea 0%, #764ba2 100%)', color: 'white', padding: '3rem 1rem', textAlign: 'center' }}>
        <h1 style={{ fontSize: '3rem', margin: 0 }}>Bookology</h1>
        <p style={{ fontSize: '1.5rem', margin: '1rem 0 2rem' }}>Unleash your imagination. Instantly generate books and movie scripts from your ideas!</p>
        <a href="#generator" style={{ background: '#fff', color: '#764ba2', padding: '0.75rem 2rem', borderRadius: '2rem', fontWeight: 'bold', textDecoration: 'none', fontSize: '1.1rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
          Start Generating
        </a>
      </header>

      {/* About Section */}
      <section style={{ flex: 1, padding: '2rem 1rem', maxWidth: 800, margin: '0 auto', textAlign: 'center' }}>
        <h2>What is Bookology?</h2>
        <p style={{ fontSize: '1.1rem', color: '#444', margin: '1rem 0 2rem' }}>
          Bookology is your creative companion. Whether you want to outline a novel, draft a movie script, or just have fun with story ideas, our AI-powered platform brings your imagination to life in seconds.
        </p>
        <ul style={{ listStyle: 'none', padding: 0, color: '#333', fontSize: '1.05rem' }}>
          <li>✨ Instantly generate book outlines or movie scripts</li>
          <li>📝 Easy-to-use interface</li>
          <li>🚀 Powered by advanced AI</li>
        </ul>
      </section>

      {/* Footer */}
      <footer style={{ background: '#222', color: '#fff', textAlign: 'center', padding: '1rem 0', fontSize: '0.95rem' }}>
        &copy; {new Date().getFullYear()} Bookology. All rights reserved.
      </footer>
    </div>
  );
}

export default App;
