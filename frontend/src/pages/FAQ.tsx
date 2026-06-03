import React from 'react';

export default function FAQ() {
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-6 text-[#1C1917]">Aam Sawaal (FAQ)</h1>
      <div className="space-y-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
          <h3 className="font-bold text-[#1B6B3A] mb-2">Q: Tamatar ke patton pe safed dhabbe kyun aate hain?</h3>
          <p className="text-gray-700">A: Yeh powdery mildew ho sakta hai. Isme sulfur-based fungicide ka upyog karein.</p>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100">
          <h3 className="font-bold text-[#1B6B3A] mb-2">Q: Urea kab dalna chahiye?</h3>
          <p className="text-gray-700">A: Fasal lagane ke 20-25 din baad pehli top dressing karni chahiye.</p>
        </div>
      </div>
    </div>
  );
}
