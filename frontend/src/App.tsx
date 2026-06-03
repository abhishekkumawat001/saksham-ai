import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import BottomNav from './components/BottomNav';
import Home from './pages/Home';
import CropAdvisory from './pages/CropAdvisory';
import Chatbot from './pages/Chatbot';
import ImageDiagnose from './pages/ImageDiagnose';
import FAQ from './pages/FAQ';

function App() {
  return (
    <BrowserRouter>
      {/* 
        Tailwind classes mapping to color palette:
        Surface = #FEFCE8 -> bg-amber-50 (approx)
      */}
      <div className="pb-16 bg-[#FEFCE8] min-h-screen">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/crops" element={<CropAdvisory />} />
          <Route path="/chat" element={<Chatbot />} />
          <Route path="/diagnose" element={<ImageDiagnose />} />
          <Route path="/faq" element={<FAQ />} />
        </Routes>
        <BottomNav />
      </div>
    </BrowserRouter>
  );
}

export default App;
