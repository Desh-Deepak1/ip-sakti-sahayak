import { useState } from 'react';
import { supabase } from '../../supabaseClient';

export default function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  const handleAuth = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage({ type: '', text: '' });

    try {
      if (isLogin) {
        // Direct Login flow
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (error) throw error;
        // Successful login will automatically trigger AppProvider state change and redirect
      } else {
        // Signup Flow with Username
        if (username.length < 3) throw new Error("Username must be at least 3 characters long.");
        
        const { error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              username: username.toLowerCase().trim(),
            }
          }
        });
        
        if (error) throw error;
        setMessage({ type: 'success', text: 'Account created successfully! You can now log in.' });
        setIsLogin(true); // Switch back to login tab
        setPassword('');
      }
    } catch (error) {
      setMessage({ type: 'error', text: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-[#fdfcff] overflow-hidden font-sans">
      
      {/* Premium Global Grid Background */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#e5e7eb_1px,transparent_1px),linear-gradient(to_bottom,#e5e7eb_1px,transparent_1px)] bg-[size:32px_32px] [mask-image:radial-gradient(ellipse_70%_70%_at_50%_50%,#000_70%,transparent_100%)]"></div>
      
      {/* Dynamic Ambient AI Glows */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-purple-300/20 rounded-full blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-blue-200/20 rounded-full blur-[100px] pointer-events-none"></div>

      {/* Login/Signup Card (Premium Glassmorphism) */}
      <div className="relative z-10 w-full max-w-md p-10 bg-white/80 backdrop-blur-3xl rounded-[2rem] shadow-[0_8px_40px_-12px_rgba(0,0,0,0.1)] border border-white mx-4">
        
        {/* AI Bot Logo */}
        <div className="flex justify-center mb-6">
          <div className="relative w-20 h-20 rounded-full flex items-center justify-center bg-white shadow-[0_0_40px_-10px_rgba(168,85,247,0.4)] border border-purple-100 p-1 group">
            <img src="/logo.png" alt="IP-SAKTI Logo" className="w-full h-full object-cover rounded-full" />
          </div>
        </div>

        {/* Title */}
        <div className="text-center mb-6">
          <h2 className="text-2xl font-extrabold text-gray-900 tracking-tight mb-2">Welcome to IP-SAKTI</h2>
          <p className="text-sm text-gray-500 font-medium">Your AI Legal Assistant</p>
        </div>

        {/* Toggle Login / Signup */}
        <div className="flex p-1 bg-gray-100/80 rounded-xl mb-8">
          <button 
            type="button"
            onClick={() => { setIsLogin(true); setMessage({type:'', text:''}); }}
            className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${isLogin ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
          >
            Log In
          </button>
          <button 
            type="button"
            onClick={() => { setIsLogin(false); setMessage({type:'', text:''}); }}
            className={`flex-1 py-2 text-sm font-semibold rounded-lg transition-all ${!isLogin ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
          >
            Create Account
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleAuth} className="space-y-5">
          
          {!isLogin && (
            <div>
              <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-1">Username</label>
              <input 
                type="text" 
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. rahul_lawyer"
                required={!isLogin}
                className="w-full px-5 py-3.5 bg-gray-50/50 border border-gray-200 rounded-2xl text-gray-900 text-sm focus:outline-none focus:ring-4 focus:ring-purple-500/10 focus:border-purple-400 transition-all shadow-sm placeholder-gray-400"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-1">Email Address</label>
            <input 
              type="email" 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
              required
              className="w-full px-5 py-3.5 bg-gray-50/50 border border-gray-200 rounded-2xl text-gray-900 text-sm focus:outline-none focus:ring-4 focus:ring-purple-500/10 focus:border-purple-400 transition-all shadow-sm placeholder-gray-400"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1.5 ml-1">Password</label>
            <input 
              type="password" 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={6}
              className="w-full px-5 py-3.5 bg-gray-50/50 border border-gray-200 rounded-2xl text-gray-900 text-sm focus:outline-none focus:ring-4 focus:ring-purple-500/10 focus:border-purple-400 transition-all shadow-sm placeholder-gray-400"
            />
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-gray-900 hover:bg-black text-white font-semibold py-4 rounded-2xl transition-all shadow-xl shadow-gray-900/20 mt-2 flex items-center justify-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
          >
            {loading ? 'Processing...' : (isLogin ? 'Log In Securely' : 'Create My Account')}
          </button>
        </form>

        {/* Status Messages */}
        {message.text && (
          <div className={`mt-5 p-4 rounded-xl text-sm font-semibold flex items-start gap-3 ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200/60' : 'bg-red-50 text-red-600 border border-red-200/60'}`}>
            {message.text}
          </div>
        )}
      </div>
    </div>
  );
}