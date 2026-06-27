import { BrowserRouter, Routes, Route } from 'react-router-dom';
import BottomNav from './components/BottomNav';
import Home from './pages/Home';
import CropAdvisory from './pages/CropAdvisory';
import FAQ from './pages/FAQ';
import Assistant from './pages/Assistant';

function App() {
  return (
    <BrowserRouter>
      <div className="pb-16 bg-[#FEFCE8] min-h-screen">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/crops" element={<CropAdvisory />} />
          <Route path="/ask" element={<Assistant />} />
          <Route path="/faq" element={<FAQ />} />
        </Routes>
        <BottomNav />
      </div>
    </BrowserRouter>
  );
}

export default App;