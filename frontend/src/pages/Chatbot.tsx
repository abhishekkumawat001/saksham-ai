import React, { useState } from 'react';

export default function Chatbot() {
  const [messages, setMessages] = useState([{ sender: 'bot', text: 'Namaste! Main KisanSaathi hoon. Aapki kya madad kar sakta hoon?' }]);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (!input.trim()) return;
    setMessages([...messages, { sender: 'user', text: input }]);
    setInput('');
  };

  return (
    <div className="flex flex-col h-[calc(100vh-80px)]">
      <div className="p-4 bg-[#1B6B3A] text-white">
        <h1 className="text-lg font-bold">KisanSaathi Chat</h1>
      </div>
      
      <div className="flex-1 p-4 overflow-y-auto space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`p-3 rounded-lg max-w-[80%] ${m.sender === 'bot' ? 'bg-white mr-auto text-gray-800' : 'bg-green-100 ml-auto text-green-900'}`}>
            {m.text}
          </div>
        ))}
      </div>

      <div className="p-3 bg-white border-t flex items-center gap-2">
        <input 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Bol kar ya type karke poochhein..." 
          className="flex-1 p-3 border rounded-full focus:outline-none focus:border-[#1B6B3A]" 
        />
        <button onClick={handleSend} className="bg-[#1B6B3A] text-white p-3 rounded-full text-xl leading-none">
          ✈️
        </button>
      </div>
    </div>
  );
}
