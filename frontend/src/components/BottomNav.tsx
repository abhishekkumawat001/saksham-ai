import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function BottomNav() {
  const location = useLocation();
  
  const navItems = [
    { name: 'Home', path: '/', icon: '🏠' },
    { name: 'Ask AI', path: '/ask', icon: '🌾' },
    { name: 'Crops', path: '/crops', icon: '🌱' },
    // { name: 'Diagnose', path: '/diagnose', icon: '📷' },  // coming in v2
    { name: 'FAQ', path: '/faq', icon: '❓' },
  ];

  return (
    <div className="fixed bottom-0 w-full bg-white border-t border-gray-200 flex justify-around p-3">
      {navItems.map((item) => {
        const isActive = location.pathname === item.path;
        return (
          <Link 
            key={item.name} 
            to={item.path} 
            className={`flex flex-col items-center p-2 rounded-lg transition-colors ${isActive ? 'text-[#1B6B3A] font-bold' : 'text-[#78716C]'}`}
          >
            <span className="text-xl mb-1">{item.icon}</span>
            <span className="text-xs">{item.name}</span>
          </Link>
        )
      })}
    </div>
  );
}
