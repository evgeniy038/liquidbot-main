import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';

import { AuthProvider } from './contexts/AuthContext';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import Portfolio from './pages/Portfolio';
import Portfolios from './pages/Portfolios';
import PortfolioView from './pages/PortfolioView';
import Leaderboard from './pages/Leaderboard';
import Stats from './pages/Stats';
import AuthCallback from './pages/AuthCallback';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Navbar />
        <Routes>
          <Route path="/" element={<Hero />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/portfolios" element={<Portfolios />} />
          <Route path="/portfolios/:userId" element={<PortfolioView />} />
          <Route path="/leaderboard" element={<Leaderboard />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
