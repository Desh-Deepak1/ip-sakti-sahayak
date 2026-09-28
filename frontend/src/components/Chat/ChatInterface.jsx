import { useState, useRef, useEffect, useContext } from 'react';
import { AppContext } from '../../context/AppProvider';
import { supabase } from '../../supabaseClient';

export default function ChatInterface() {
  const { user, session } = useContext(AppContext) || {};
  
  // States
  const [messages, setMessages] = useState([]);
  const [fullHistory, setFullHistory] = useState([]); 
  const [input, setInput] = useState('');
  const [jurisdiction, setJurisdiction] = useState('INDIA');
  const [loading, setLoading] = useState(false);
  const [attachment, setAttachment] = useState(null);
  
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [profileData, setProfileData] = useState({ name: '', username: '' });
  const [historyList, setHistoryList] = useState([]);
  
  const messagesEndRef = useRef(null);
  
  // Auto-scroll to bottom
  useEffect(() => { 
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); 
  }, [messages, loading]);

  useEffect(() => {
    if (user) {
      setProfileData({
        name: user.user_metadata?.name || '',
        username: user.user_metadata?.username || user.email?.split('@')[0] || 'User'
      });
    }
  }, [user]);

  // Fetches full history silently in the background
  const loadFullHistory = async () => {
    try {
      const { data: { session: currentSession } } = await supabase.auth.getSession();
      if (!currentSession?.access_token) return;

      const response = await fetch('https://sahayak-ai-xkx9.onrender.com/api/v1/history', {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${currentSession.access_token}` }
      });

      if (response.ok) {
        const data = await response.json();
        const chatHistory = data.history || [];
        
        setFullHistory(chatHistory);
        
        const userQueries = chatHistory.filter(m => m.sender === 'user').map(m => m.text);
        setHistoryList([...new Set(userQueries)].reverse().slice(0, 15)); 
      }
    } catch (error) {
      console.error("History fetch error:", error);
    }
  };

  useEffect(() => {
    loadFullHistory();
  }, []); 

  // Load ONLY the clicked conversation
  const handleHistoryClick = (itemText) => {
    const startIndex = fullHistory.findIndex(m => m.sender === 'user' && m.text === itemText);
    if (startIndex !== -1) {
      const conversation = [fullHistory[startIndex]];
      let i = startIndex + 1;
      while (i < fullHistory.length && fullHistory[i].sender !== 'user') {
        conversation.push(fullHistory[i]);
        i++;
      }
      setMessages(conversation);
      setIsDrawerOpen(false);
    }
  };

  // Helper to delete a specific history conversation
  const handleDeleteHistoryItem = (e, itemText) => {
    e.stopPropagation(); // Prevents opening the chat when clicking delete
    
    // Filter out messages related to this query from fullHistory
    const updatedFullHistory = fullHistory.filter(m => m.text !== itemText);
    setFullHistory(updatedFullHistory);

    // Update the sidebar history list
    const updatedHistoryList = historyList.filter(item => item !== itemText);
    setHistoryList(updatedHistoryList);

    // If the currently active chat matches this item, clear the chat view
    if (messages.length > 0 && messages[0].text === itemText) {
      setMessages([]);
    }
  };

  // Helper to start a completely new chat
  const handleNewChat = () => {
    setMessages([]);
    setAttachment(null);
    setInput('');
    setIsDrawerOpen(false);
  };

  const handleLogout = async () => {
    setIsProfileOpen(false);
    if (supabase) await supabase.auth.signOut();
    window.location.reload();
  };

  const handleProfileUpdate = async (e) => {
    e.preventDefault();
    if (supabase) {
      const { error } = await supabase.auth.updateUser({
        data: { name: profileData.name, username: profileData.username }
      });
      if (!error) setIsProfileOpen(false);
      else alert("Error updating profile: " + error.message);
    }
  };

  const handleSend = async (e, customQuery = null) => {
    if (e) e.preventDefault();
    const queryToSend = customQuery || input;
    if (!queryToSend.trim() && !attachment) return;

    // Check session first
    const { data: { session: currentSession } } = await supabase.auth.getSession();
    if (!currentSession?.access_token) {
      alert("Session expired. Please log in again.");
      return;
    }

    setInput('');
    const currentAttachment = attachment; 
    setAttachment(null);

    setMessages(prev => [...prev, { sender: 'user', text: queryToSend, file: currentAttachment?.name }]);
    setLoading(true);

    try {
      const token = currentSession.access_token;

      const response = await fetch('https://sahayak-ai-xkx9.onrender.com/api/v1/chat', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ query: queryToSend, jurisdiction: jurisdiction })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Server error (${response.status}): ${errorText}`);
      }
      
      const data = await response.json();
      setMessages(prev => [...prev, { sender: 'assistant', text: data.response }]);
      loadFullHistory(); 
    } catch (err) {
      setMessages(prev => [...prev, {
        sender: 'assistant',
        text: `**System Error:** ${err.message}`
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Format AI Response to remove * and # completely
  const formatAIResponse = (text) => {
    if (!text) return { __html: "Processing..." };
    let formattedHtml = text.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-gray-900">$1</strong>');
    formattedHtml = formattedHtml.replace(/[*#]/g, '');
    formattedHtml = formattedHtml.replace(/\n/g, '<br />');
    return { __html: formattedHtml };
  };

  const displayUserName = profileData.username;

  return (
    <div className="flex h-[100dvh] bg-gradient-to-b from-indigo-50 via-white to-fuchsia-50 text-gray-900 font-sans overflow-hidden relative">
      
      {/* Tech Grid Overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none z-0"></div>

      {/* Drawer Overlay */}
      {isDrawerOpen && <div className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50 transition-opacity" onClick={() => setIsDrawerOpen(false)}></div>}

      {/* Side Panel (History) */}
      <div className={`fixed top-0 left-0 h-full w-[280px] sm:w-[300px] bg-white/95 backdrop-blur-xl border-r border-purple-100 z-50 transform transition-transform duration-300 ease-in-out shadow-2xl flex flex-col ${isDrawerOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="p-4 sm:p-6 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
             <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-full border border-purple-300 p-0.5 bg-white shadow-sm"><img src="/logo.png" alt="logo" className="w-full h-full rounded-full object-cover"/></div>
             <span className="font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-indigo-900 to-purple-800 tracking-tight text-base sm:text-lg">IP-SAKTI</span>
          </div>
          <button onClick={() => setIsDrawerOpen(false)} className="text-gray-500 hover:text-red-500 transition-colors">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/></svg>
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-3 sm:p-4">
          <div className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-3 ml-2">Recent History</div>
          <div className="space-y-2">
            {historyList.length === 0 ? (
              <div className="px-3 py-2 text-sm text-gray-400 italic">No recent chats found.</div>
            ) : (
              historyList.map((item, index) => (
                <div 
                  key={index} 
                  onClick={() => handleHistoryClick(item)} 
                  className="px-3 sm:px-4 py-3 text-xs sm:text-sm font-medium text-gray-700 bg-white hover:bg-purple-50 rounded-xl cursor-pointer transition-all truncate border border-gray-100 shadow-sm flex items-center justify-between group"
                >
                  <div className="flex items-center gap-2 sm:gap-3 truncate">
                    <svg className="w-4 h-4 text-purple-400 group-hover:text-purple-600 transition-colors flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/></svg>
                    <span className="truncate">{item}</span>
                  </div>
                  
                  {/* Delete Button Icon */}
                  <button 
                    onClick={(e) => handleDeleteHistoryItem(e, item)} 
                    className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-600 p-1 transition-opacity"
                    title="Delete chat"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
        <div className="p-3 sm:p-4 border-t border-gray-100 bg-gray-50/50">
          <button onClick={handleNewChat} className="w-full bg-gradient-to-r from-gray-900 to-black text-white py-3 rounded-xl text-xs sm:text-sm font-bold hover:shadow-lg hover:scale-[1.02] transition-all duration-300 shadow-md">
            + Start New Chat
          </button>
        </div>
      </div>

      {/* Profile Modal Overlay */}
      {isProfileOpen && <div className="fixed inset-0 z-50" onClick={() => setIsProfileOpen(false)}></div>}

      {/* Profile Modal */}
      {isProfileOpen && (
        <div className="absolute top-16 right-4 sm:right-8 w-[300px] sm:w-[340px] bg-white/95 backdrop-blur-xl border border-gray-200 rounded-2xl shadow-2xl z-50 p-5 sm:p-6 transform transition-all">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base sm:text-lg font-bold text-gray-900 tracking-tight">Account Settings</h3>
            <button onClick={() => setIsProfileOpen(false)} className="text-gray-400 hover:text-red-500"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"/></svg></button>
          </div>
          <form onSubmit={handleProfileUpdate} className="space-y-3 sm:space-y-4">
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1 ml-1">Email</label>
              <input type="text" value={user?.email || ''} disabled className="w-full px-3 py-2 bg-gray-100 border border-gray-200 rounded-xl text-gray-600 text-xs sm:text-sm cursor-not-allowed" />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1 ml-1">Username</label>
              <input type="text" value={profileData.username} onChange={(e) => setProfileData({...profileData, username: e.target.value})} className="w-full px-3 py-2 bg-white border border-gray-300 rounded-xl text-gray-900 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
            </div>
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-wider mb-1 ml-1">Full Name</label>
              <input type="text" value={profileData.name} onChange={(e) => setProfileData({...profileData, name: e.target.value})} placeholder="e.g. Rahul Kumar" className="w-full px-3 py-2 bg-white border border-gray-300 rounded-xl text-gray-900 text-xs sm:text-sm focus:outline-none focus:ring-2 focus:ring-purple-500" />
            </div>
            <div className="flex gap-2 sm:gap-3 pt-3">
              <button type="submit" className="flex-1 bg-gray-900 hover:bg-black text-white py-2.5 rounded-xl text-xs sm:text-sm font-semibold transition-all shadow-md">Save</button>
              <button type="button" onClick={handleLogout} className="flex-1 bg-red-50 text-red-600 py-2.5 rounded-xl text-xs sm:text-sm font-semibold hover:bg-red-100 transition-colors border border-red-200">Log Out</button>
            </div>
          </form>
        </div>
      )}

      {/* Main Content Area - Fully Flex Container */}
      <div className="flex-1 flex flex-col h-full relative w-full z-10 overflow-hidden">
        
        {/* Header - Flex-shrink so it never overlaps */}
        <header className="flex-shrink-0 flex items-center justify-between px-3 sm:px-6 md:px-8 py-3 bg-white/95 backdrop-blur-xl border-b border-gray-200/50 shadow-sm z-30">
          <div className="flex items-center gap-2 sm:gap-4">
            <button onClick={() => setIsDrawerOpen(true)} className="text-gray-700 hover:text-purple-700 transition-colors p-1 rounded-lg hover:bg-gray-100">
              <svg className="w-6 h-6 sm:w-7 sm:h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M4 6h16M4 12h16M4 18h16"/></svg>
            </button>
            
            <div className="flex items-center gap-1.5 sm:gap-2 bg-gray-50 px-2.5 sm:px-4 py-1.5 rounded-full border border-gray-200 shadow-sm">
              <div className="w-5 h-5 sm:w-6 sm:h-6 rounded-full overflow-hidden border border-gray-200 flex-shrink-0">
                <img src="/logo.png" alt="logo" className="w-full h-full object-cover" />
              </div>
              <span className="font-bold text-xs sm:text-sm text-gray-900 tracking-wide truncate max-w-[90px] sm:max-w-none">IP-SAKTI</span>
              <span className="w-2 h-2 sm:w-2.5 sm:h-2.5 rounded-full bg-green-500 ml-0.5 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse flex-shrink-0"></span>
            </div>

            {/* New Chat Icon Button */}
            <button onClick={handleNewChat} className="p-1.5 bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors shadow-sm" title="Start New Chat">
              <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 4v16m8-8H4"/></svg>
            </button>
          </div>
          
          <div className="flex items-center gap-2 sm:gap-4">
            <div className="flex bg-gray-100 p-0.5 sm:p-1 rounded-full border border-gray-200 shadow-sm">
              <button onClick={() => setJurisdiction('INDIA')} className={`px-3 sm:px-5 py-1 text-[10px] sm:text-xs font-bold rounded-full transition-all duration-300 ${jurisdiction === 'INDIA' ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md' : 'text-gray-600 hover:text-gray-900'}`}>India</button>
              <button onClick={() => setJurisdiction('INTERNATIONAL')} className={`px-3 sm:px-5 py-1 text-[10px] sm:text-xs font-bold rounded-full transition-all duration-300 ${jurisdiction === 'INTERNATIONAL' ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-md' : 'text-gray-600 hover:text-gray-900'}`}>Intl</button>
            </div>
            
            <button onClick={() => setIsProfileOpen(!isProfileOpen)} className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-gray-800 to-black text-white flex items-center justify-center font-bold text-xs sm:text-sm shadow-lg hover:shadow-xl hover:scale-105 transition-all border-2 border-white ring-2 ring-purple-100 flex-shrink-0">
              {displayUserName.charAt(0).toUpperCase()}
            </button>
          </div>
        </header>

        {/* Chat Area & Welcome Screen */}
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center px-4 md:px-6 z-10 overflow-y-auto">
            <div className="w-20 h-20 sm:w-28 sm:h-28 mb-6 sm:mb-8 rounded-full border-4 border-white shadow-2xl overflow-hidden bg-white hover:scale-105 transition-transform duration-500 flex-shrink-0">
               <img src="/logo.png" className="w-full h-full object-cover" alt="IP SAKTI" />
            </div>
            
            <h1 className="text-2xl sm:text-4xl md:text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-gray-900 to-gray-600 tracking-tight mb-3 text-center drop-shadow-sm px-2">Hello, {displayUserName}</h1>
            <p className="text-sm sm:text-lg md:text-xl text-gray-600 font-medium mb-8 sm:mb-12 text-center max-w-xl leading-relaxed px-4">Experience the next generation of <span className="font-bold text-purple-700">{jurisdiction === 'INDIA' ? 'Indian' : 'International'}</span> Intellectual Property analysis powered by Ayurveda intelligence.</p>
            
            <div className="w-full max-w-2xl px-2">
              <div className="bg-white/90 backdrop-blur-xl border border-white rounded-[1.5rem] sm:rounded-[2rem] shadow-2xl p-2 mb-4 focus-within:ring-4 focus-within:ring-purple-200 transition-all duration-300">
                <form onSubmit={handleSend} className="flex flex-col">
                  <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask anything about IP & Ayurveda..." className="w-full px-4 sm:px-6 py-3 sm:py-4 text-sm sm:text-lg text-gray-900 focus:outline-none bg-transparent placeholder-gray-400 font-medium" />
                  
                  <div className="flex items-center justify-between px-2 sm:px-4 pb-1 pt-2 border-t border-gray-100/50 mt-1">
                    <div className="flex items-center gap-2">
                      <label className="cursor-pointer text-gray-500 hover:text-purple-600 transition-colors p-2 rounded-full hover:bg-purple-50 flex items-center gap-2">
                        <input type="file" className="hidden" onChange={(e) => setAttachment(e.target.files[0])} />
                        <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/></svg>
                        {attachment && <span className="text-xs sm:text-sm font-bold text-gray-800 truncate max-w-[100px]">{attachment.name}</span>}
                      </label>
                    </div>
                    <button type="submit" disabled={loading} className="bg-gradient-to-r from-gray-900 to-black hover:scale-105 text-white p-2.5 sm:p-3.5 rounded-full transition-all duration-300 disabled:opacity-50 shadow-lg">
                      <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 12h14M12 5l7 7-7 7"/></svg>
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto w-full scroll-smooth px-3 sm:px-6 py-4 space-y-4 sm:space-y-6 z-10">
            <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6 pb-20">
              {messages.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {msg.sender === 'assistant' && (
                    <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full border-2 border-white shadow-md p-0.5 flex-shrink-0 mr-2 sm:mr-4 mt-1 bg-white">
                      <img src="/logo.png" className="w-full h-full object-cover rounded-full" alt="bot" />
                    </div>
                  )}
                  <div className={`max-w-[88%] sm:max-w-[80%] rounded-[1.2rem] sm:rounded-[1.5rem] px-4 sm:px-6 py-3 sm:py-5 text-xs sm:text-[15px] leading-relaxed shadow-lg ${msg.sender === 'user' ? 'bg-gray-100 text-gray-900 border border-gray-200 rounded-tr-sm' : 'bg-white/95 backdrop-blur-sm border border-purple-100/50 text-gray-800 rounded-tl-sm'}`}>
                    {msg.file && (
                      <div className={`mb-2 sm:mb-3 inline-flex items-center gap-2 px-2.5 py-1 rounded-lg text-[10px] sm:text-xs font-bold ${msg.sender === 'user' ? 'bg-white text-gray-800 shadow-sm' : 'bg-purple-50 text-purple-800'}`}>
                        <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/></svg>
                        {msg.file}
                      </div>
                    )}
                    {msg.sender === 'user' ? (
                      <div className="whitespace-pre-wrap font-medium">{msg.text}</div>
                    ) : (
                      <div className="whitespace-pre-wrap font-medium" dangerouslySetInnerHTML={formatAIResponse(msg.text)} />
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start items-center gap-3 sm:gap-4">
                  <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-white shadow-md animate-pulse flex-shrink-0 border-2 border-purple-100"></div>
                  <div className="bg-white/90 backdrop-blur-sm border border-purple-100/50 rounded-[1.2rem] sm:rounded-[1.5rem] rounded-tl-sm px-4 sm:px-6 py-3 shadow-lg flex gap-2 items-center h-12 sm:h-14">
                    <span className="w-2 h-2 sm:w-2.5 sm:h-2.5 bg-purple-500 rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 sm:w-2.5 sm:h-2.5 bg-fuchsia-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></span>
                    <span className="w-2 h-2 sm:w-2.5 sm:h-2.5 bg-indigo-500 rounded-full animate-bounce" style={{animationDelay: '0.4s'}}></span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>
        )}

        {/* Floating Input Box for active chat - Flex-shrink so it stays at bottom nicely */}
        {messages.length > 0 && (
          <div className="flex-shrink-0 w-full px-3 sm:px-6 py-3 bg-white/60 backdrop-blur-md border-t border-gray-200/50 flex justify-center z-30">
            <div className="w-full max-w-3xl bg-white/95 backdrop-blur-xl border border-gray-200 rounded-full shadow-2xl p-1.5 sm:p-2 flex items-center focus-within:border-purple-300 transition-all duration-300">
              <label className="cursor-pointer p-2 text-gray-500 hover:text-purple-600 transition-colors ml-1 rounded-full hover:bg-purple-50">
                <input type="file" className="hidden" onChange={(e) => setAttachment(e.target.files[0])} />
                <svg className="w-5 h-5 sm:w-6 sm:h-6 transform rotate-45" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"/></svg>
              </label>
              {attachment && <span className="ml-1 text-xs font-bold text-purple-800 bg-purple-100 px-2.5 py-1 rounded-lg truncate max-w-[90px] shadow-sm">{attachment.name}</span>}
              
              <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask a follow-up question..." className="flex-1 px-3 text-sm sm:text-[16px] text-gray-900 font-medium focus:outline-none bg-transparent placeholder-gray-400" />
              <button onClick={handleSend} disabled={loading} className="bg-gradient-to-r from-gray-900 to-black hover:scale-105 text-white p-2.5 sm:p-3.5 rounded-full text-sm font-semibold transition-all duration-300 disabled:opacity-50 mr-1 shadow-lg">
                <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 12h14M12 5l7 7-7 7"/></svg>
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}