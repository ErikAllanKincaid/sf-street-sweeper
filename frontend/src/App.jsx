import { Routes, Route, Link, useLocation } from 'react-router-dom'
import Home from './pages/Home'
import Saved from './pages/Saved'
import Settings from './pages/Settings'

function App() {
  const location = useLocation()
  
  return (
    <div className="container">
      <header className="header">
        <h1>SF Street Sweeper</h1>
      </header>
      <nav className="nav">
        <Link 
          to="/" 
          className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
        >
          Map
        </Link>
        <Link 
          to="/saved" 
          className={`nav-link ${location.pathname === '/saved' ? 'active' : ''}`}
        >
          Saved
        </Link>
        <Link 
          to="/settings" 
          className={`nav-link ${location.pathname === '/settings' ? 'active' : ''}`}
        >
          Settings
        </Link>
      </nav>
      
      <main className="main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/saved" element={<Saved />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
