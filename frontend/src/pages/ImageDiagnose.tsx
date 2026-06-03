import React from 'react';

export default function ImageDiagnose() {
  return (
    <div className="p-4 flex flex-col items-center justify-center min-h-[80vh]">
      <h1 className="text-2xl font-bold text-[#1C1917] mb-2">Photo Diagnose</h1>
      <p className="text-[#78716C] mb-8 text-center">Fasal ki bimari ki photo kheinchiye aur turant upaay paiye.</p>
      
      <div className="w-full max-w-sm aspect-square border-4 border-dashed border-gray-300 rounded-3xl flex flex-col items-center justify-center bg-white hover:bg-gray-50 transition cursor-pointer">
         <span className="text-6xl mb-4 text-[#1B6B3A]">📸</span>
         <span className="font-semibold text-[#1C1917]">Tap to Upload</span>
         <span className="text-sm text-gray-400 mt-2">ya Gallery se chunein</span>
      </div>
    </div>
  );
}
