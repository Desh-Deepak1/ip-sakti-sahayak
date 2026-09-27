import { useContext } from 'react';
import { AppContext } from './context/AppProvider';

// Import your components (Make sure these paths match your actual folder structure)
import Login from './components/Auth/Login'; 
import ChatInterface from './components/Chat/ChatInterface';

function App() {
  // AppProvider se session status nikal rahe hain
  const { session, loading } = useContext(AppContext) || {};

  // Jab tak Supabase check kar raha hai ki user logged in hai ya nahi
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#fdfcff]">
        <div className="w-10 h-10 border-4 border-gray-200 border-t-gray-900 rounded-full animate-spin"></div>
      </div>
    );
  }

  // Agar user ke paas session (token) nahi hai, toh automatically Login page dikhao
  if (!session) {
    return <Login />;
  }

  // Agar session mil gaya (login success), toh Chat interface dikhao
  return <ChatInterface />;
}

export default App;