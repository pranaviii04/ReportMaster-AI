import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getStats } from '../services/api';
import { BookOpen, LogOut, ArrowRight, BarChart3, Clock, Database, User as UserIcon } from 'lucide-react';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({ total_documents: 0, collection_name: 'Unknown' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getStats();
        setStats(data);
      } catch (err) {
        console.error("Failed to load stats", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-300 font-sans selection:bg-blue-500/30">
      {/* Header */}
      <header className="h-16 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-10">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg shadow-lg shadow-blue-500/20">
            <BookOpen className="h-5 w-5 text-white" />
          </div>
          <h1 className="text-xl font-bold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
            ReportMaster AI
          </h1>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/50 rounded-full border border-slate-700">
            <UserIcon className="h-4 w-4 text-blue-400" />
            <span className="text-sm font-medium text-slate-200">{user?.email}</span>
          </div>
          <button 
            onClick={handleLogout}
            className="flex items-center gap-2 px-3 py-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
          >
            <LogOut className="h-4 w-4" />
            <span className="text-sm">Sign Out</span>
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="mb-12">
          <h2 className="text-4xl font-bold text-white mb-4">Welcome back!</h2>
          <p className="text-slate-400 text-lg">
            Your centralized intelligence hub for financial reporting and accounting standards.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {/* Stats Card 1 */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Database className="h-24 w-24 text-blue-500" />
            </div>
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-blue-500/10 rounded-lg border border-blue-500/20">
                  <BookOpen className="h-6 w-6 text-blue-400" />
                </div>
                <h3 className="font-semibold text-white">Knowledge Base</h3>
              </div>
              <div className="text-4xl font-bold text-white mb-2">
                {loading ? '...' : stats.total_documents}
              </div>
              <p className="text-sm text-slate-400">Total document chunks indexed</p>
            </div>
          </div>

          {/* Stats Card 2 */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <BarChart3 className="h-24 w-24 text-emerald-500" />
            </div>
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                  <BarChart3 className="h-6 w-6 text-emerald-400" />
                </div>
                <h3 className="font-semibold text-white">System Status</h3>
              </div>
              <div className="text-2xl font-bold text-emerald-400 mb-2 mt-4">
                Online & Ready
              </div>
              <p className="text-sm text-slate-400">RAG Pipeline is operational</p>
            </div>
          </div>

           {/* Stats Card 3 */}
           <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Clock className="h-24 w-24 text-purple-500" />
            </div>
            <div className="relative z-10">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-purple-500/10 rounded-lg border border-purple-500/20">
                  <Clock className="h-6 w-6 text-purple-400" />
                </div>
                <h3 className="font-semibold text-white">Recent Activity</h3>
              </div>
              <div className="text-lg text-slate-300 mb-2 mt-4">
                Last login: Just now
              </div>
              <p className="text-sm text-slate-400">Session active</p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="bg-gradient-to-br from-blue-900/40 to-slate-900 border border-blue-800/50 rounded-3xl p-10 flex flex-col items-center justify-center text-center shadow-2xl">
          <div className="bg-blue-500/20 p-4 rounded-2xl mb-6 border border-blue-500/30">
            <BookOpen className="h-10 w-10 text-blue-400" />
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">Enter the Workspace</h2>
          <p className="text-slate-300 max-w-2xl mb-8">
            Start querying financial manuals, uploading new documents, and extracting insights using our advanced RAG pipeline.
          </p>
          <Link
            to="/query"
            className="group inline-flex items-center justify-center px-8 py-4 text-base font-semibold text-white bg-blue-600 rounded-xl hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 focus:ring-offset-slate-900 transition-all shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50"
          >
            Launch ReportMaster
            <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
