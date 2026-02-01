import React from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import PortfolioPage from './components/PortfolioPage';

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/portfolios/:discordId" element={<PortfolioPage />} />
        {/* Redirect root to a demo portfolio for immediate visualization */}
        <Route path="/" element={<Navigate to="/portfolios/123456789012345678" replace />} />
      </Routes>
    </HashRouter>
  );
}

export default App;