import React from 'react';

export default function CropAdvisory() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4 text-[#1B6B3A]">Crop Advisory</h1>
      <p className="text-[#78716C] mb-6">Select a crop to view recommendations.</p>
      
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Mock crops */}
        {['Tomato', 'Wheat', 'Sugarcane', 'Cotton'].map(crop => (
          <div key={crop} className="bg-white p-4 rounded-xl shadow border border-gray-100 flex flex-col items-center">
             <div className="h-16 w-16 bg-gray-100 rounded-full mb-3 flex items-center justify-center text-2xl">🌿</div>
             <span className="font-semibold">{crop}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
