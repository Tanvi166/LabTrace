import React, { useState, useEffect } from 'react';
import { FlaskConical, CheckCircle2, AlertTriangle, FileText, ArrowRight, Search, Trash2, Eye, RefreshCw, PlayCircle, ShieldCheck, Activity, BrainCircuit } from 'lucide-react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { experimentApi, PaginatedExperiments } from '../services/api';

// @ts-ignore
import beakerImg from '../assets/beaker.jpg';

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<PaginatedExperiments | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const fetchExperiments = async (searchQuery: string = '') => {
    setLoading(true);
    setError(null);
    try {
      const res = await experimentApi.getExperiments({ search: searchQuery });
      setData(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch experiments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchExperiments(search);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this experiment?')) return;
    try {
      await experimentApi.deleteExperiment(id);
      fetchExperiments(search);
    } catch (err: any) {
      alert('Failed to delete experiment');
    }
  };

  const experiments = data?.items || [];
  const totalCount = data?.total || 0;

  return (
    <div className="space-y-16 pb-12">
      {/* Hero Section */}
      <section className="relative w-full max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-12 items-center pt-8">
        
        {/* Left Column: Text & CTA */}
        <motion.div 
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
          className="space-y-6 z-10"
        >
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-sm font-medium shadow-neon">
            <ShieldCheck className="w-4 h-4" />
            <span>AI-POWERED REPRODUCIBILITY</span>
          </div>
          
          <h1 className="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white to-slate-400 leading-tight">
            Build, analyze &<br/>reproduce research<br/>
            <span className="text-glow text-neon-cyan">with confidence</span>
          </h1>
          
          <p className="text-slate-400 text-lg leading-relaxed max-w-md">
            LabTrace uses a multi-agent AI system to analyze your experiments, detect reproducibility gaps, and generate actionable insights — so your research is transparent, reliable, and reusable.
          </p>

          <div className="flex items-center space-x-4 pt-4">
            <Link to="/upload" className="px-6 py-3 bg-gradient-to-r from-neon-cyan to-brand-500 text-white font-semibold rounded-full shadow-neon hover:shadow-neon-strong transition-all duration-300 flex items-center space-x-2">
              <span>Let's Get Started</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <button className="px-6 py-3 bg-white/5 border border-white/10 hover:bg-white/10 text-white font-semibold rounded-full transition-all duration-300 flex items-center space-x-2 glass-panel">
              <PlayCircle className="w-4 h-4" />
              <span>Watch Demo</span>
            </button>
          </div>
        </motion.div>

        {/* Center Column: 3D Beaker */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.8, y: 30 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.2 }}
          className="relative flex justify-center items-center z-0"
        >
          {/* Decorative glowing backdrops */}
          <div className="absolute inset-0 bg-neon-cyan/20 blur-[100px] rounded-full w-full h-full transform scale-75"></div>
          
          {/* Floating Beaker Image */}
          <motion.img 
            animate={{ y: [0, -15, 0] }}
            transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
            src={beakerImg} 
            alt="AI Beaker" 
            className="w-full max-w-md object-contain relative z-10 drop-shadow-[0_0_25px_rgba(34,211,238,0.4)] rounded-full mix-blend-screen"
          />
        </motion.div>

        {/* Right Column: Workflow Steps */}
        <motion.div 
          initial={{ opacity: 0, x: 30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="glass-panel p-6 z-10 relative overflow-hidden"
        >
          <h3 className="text-xl font-bold text-white mb-2">The LabTrace Workflow</h3>
          <p className="text-sm text-slate-400 mb-6">Multi-agent AI analysis pipeline</p>
          
          <div className="space-y-4 relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-neon-cyan before:to-neon-purple before:opacity-30">
            {[
              { num: '1', title: 'Ingestion Agent', desc: 'Parses your code, data and configs', icon: <FileText /> },
              { num: '2', title: 'Preprocessing Auditor', desc: 'Detects reproducibility gaps', icon: <Search /> },
              { num: '3', title: 'Reproducibility Scorer', desc: 'Combines findings with past knowledge', icon: <Activity /> },
              { num: '4', title: 'Report Generator', desc: 'Creates structured report & recommendations', icon: <BrainCircuit /> },
            ].map((step, idx) => (
              <div key={idx} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
                <div className="flex items-center justify-center w-10 h-10 rounded-full border border-white/20 bg-slate-900 text-neon-cyan shadow-[0_0_10px_rgba(34,211,238,0.2)] shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 z-10 font-bold">
                  {step.num}
                </div>
                <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-3 rounded-xl border border-white/5 bg-white/5 backdrop-blur-md group-hover:bg-white/10 transition-colors">
                  <div className="flex items-center space-x-3">
                    <div className="text-neon-purple opacity-70 w-5 h-5">{step.icon}</div>
                    <div>
                      <h4 className="font-semibold text-slate-200 text-sm">{step.title}</h4>
                      <p className="text-xs text-slate-400">{step.desc}</p>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </section>


      {/* Data Management Section */}
      <section className="pt-12 border-t border-white/10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h2 className="text-2xl font-bold text-white">Your Experiments</h2>
            <p className="text-slate-400 text-sm mt-1">Manage and track your reproducibility analyses.</p>
          </div>
        </div>

        {/* Overview Stat Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          {[
            { label: 'Total Experiments', value: totalCount, icon: <FlaskConical className="w-6 h-6" />, color: 'text-neon-cyan' },
            { label: 'Analyzed', value: experiments.filter(e => e.status === 'COMPLETED').length, icon: <CheckCircle2 className="w-6 h-6" />, color: 'text-emerald-400' },
            { label: 'Average Score', value: '78', icon: <Activity className="w-6 h-6" />, color: 'text-amber-400' },
            { label: 'Issues Found', value: '31', icon: <AlertTriangle className="w-6 h-6" />, color: 'text-rose-400' }
          ].map((stat, i) => (
            <motion.div 
              key={i}
              whileHover={{ y: -5 }}
              className="glass-panel p-6 flex items-center space-x-4"
            >
              <div className={`p-3 bg-white/5 rounded-xl border border-white/10 ${stat.color} shadow-glass`}>
                {stat.icon}
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium uppercase tracking-wider">{stat.label}</p>
                <p className="text-3xl font-bold text-white mt-1">{stat.value}</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Search & Actions Bar */}
        <div className="glass-panel p-4 flex flex-col sm:flex-row items-center justify-between gap-4 mb-8">
          <div className="relative w-full sm:w-96">
            <Search className="w-4 h-4 absolute left-3 top-3.5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search experiments by name or description..."
              className="w-full pl-9 pr-4 py-2.5 text-sm bg-black/20 border border-white/10 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:border-neon-cyan focus:ring-1 focus:ring-neon-cyan transition-colors"
            />
          </div>
          <button
            onClick={() => fetchExperiments(search)}
            className="flex items-center space-x-2 px-4 py-2.5 text-sm font-medium text-slate-300 hover:text-white bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg transition-colors shadow-glass"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>

        {/* Experiments List */}
        {loading ? (
          <div className="glass-panel p-12 text-center text-slate-400">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4 text-neon-cyan" />
            Loading experiments...
          </div>
        ) : error ? (
          <div className="bg-rose-500/10 text-rose-400 p-4 rounded-xl border border-rose-500/20 text-sm">
            {error}
          </div>
        ) : experiments.length === 0 ? (
          <div className="glass-panel p-12 text-center">
            <FlaskConical className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-white">No Experiments Found</h3>
            <p className="text-sm text-slate-400 max-w-md mx-auto mt-2 mb-8">
              Upload your code, data, or config files to start your first AI-powered reproducibility analysis.
            </p>
            <Link
              to="/upload"
              className="inline-flex items-center px-6 py-3 bg-brand-600 hover:bg-brand-500 text-white rounded-full text-sm font-medium shadow-neon transition-colors space-x-2"
            >
              <span>Upload First Experiment</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
            {experiments.map((exp, idx) => (
              <motion.div 
                key={exp.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: idx * 0.1 }}
                className="glass-panel glass-panel-hover p-6 flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <h3 className="font-semibold text-white text-lg leading-tight truncate group-hover:text-neon-cyan transition-colors">{exp.title}</h3>
                    <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider border ${
                      exp.status === 'READY' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 
                      exp.status === 'COMPLETED' ? 'bg-brand-500/10 text-brand-400 border-brand-500/20' :
                      'bg-slate-500/10 text-slate-400 border-slate-500/20'
                    }`}>
                      {exp.status}
                    </span>
                  </div>
                  {exp.description && (
                    <p className="text-sm text-slate-400 line-clamp-2 mb-5">{exp.description}</p>
                  )}
                  {exp.tags && exp.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-5">
                      {exp.tags.map((tag, i) => (
                        <span key={i} className="bg-black/30 border border-white/5 text-slate-300 text-xs px-2.5 py-1 rounded-md">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                <div className="pt-4 border-t border-white/10 flex items-center justify-between text-xs text-slate-500">
                  <div className="flex items-center space-x-2">
                    <span className="flex items-center space-x-1 bg-white/5 px-2 py-1 rounded text-slate-300">
                      <FileText className="w-3 h-3" />
                      <span>{exp.files_count || (exp.files?.length || 0)}</span>
                    </span>
                    <span>&bull;</span>
                    <span>{new Date(exp.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Link
                      to={`/experiments/${exp.id}`}
                      className="p-2 text-slate-400 hover:text-neon-cyan hover:bg-neon-cyan/10 rounded-lg transition-colors"
                      title="View Details"
                    >
                      <Eye className="w-4 h-4" />
                    </Link>
                    <button
                      onClick={(e) => handleDelete(exp.id, e)}
                      className="p-2 text-slate-400 hover:text-rose-400 hover:bg-rose-400/10 rounded-lg transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
