import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Badge, Button, Card } from '../components/Common';
import { api } from '../services/api';
import type { DashboardStats } from '../types/api';
import { transformStatus, formatDateShort, getCountryName } from '../utils/transform';
import { ArrowRight, Activity, Map, FileText, ArrowUpRight } from 'lucide-react';

const StatCard: React.FC<{ number: string; title: string; value: number; link: string; icon: React.ReactNode }> = ({ number, title, value, link, icon }) => (
  <Link to={link} className="block group">
    <Card className="p-8 h-full transition-all duration-200 hover:bg-black hover:text-white group-hover:border-black relative overflow-hidden">
      {/* Hover decoration */}
      <div className="absolute top-0 right-0 w-24 h-24 bg-accent translate-x-12 -translate-y-12 rotate-45 opacity-0 group-hover:opacity-100 transition-opacity"></div>
      
      <div className="flex justify-between items-start mb-8 relative z-10">
        <span className="text-xs font-mono text-accent group-hover:text-white">{number}</span>
        <div className="text-black group-hover:text-white transition-colors">
          {icon}
        </div>
      </div>
      
      <div className="relative z-10">
        <p className="text-6xl font-black tracking-tighter mb-2">{value}</p>
        <div className="h-1 w-12 bg-black group-hover:bg-accent mb-4 transition-colors"></div>
        <p className="text-xs font-bold uppercase tracking-widest group-hover:text-white">{title}</p>
      </div>

      <div className="absolute bottom-6 right-6 opacity-0 group-hover:opacity-100 transition-all transform translate-y-2 group-hover:translate-y-0">
        <ArrowRight className="w-6 h-6 text-accent" />
      </div>
    </Card>
  </Link>
);

const Dashboard: React.FC = () => {
  console.log('[DASHBOARD] Dashboard component rendering...');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('[DASHBOARD] useEffect triggered, fetching dashboard data...');
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        console.log('[DASHBOARD] Calling api.getDashboard()...');
        const data = await api.getDashboard();
        console.log('[DASHBOARD] ✅ Dashboard data received:', data);
        setStats(data);
      } catch (err: any) {
        console.error('[DASHBOARD] ❌ Failed to load dashboard:', err);
        setError(err.response?.data?.detail?.message || 'Failed to load dashboard');
      } finally {
        setLoading(false);
        console.log('[DASHBOARD] Dashboard fetch completed, loading set to false');
      }
    };

    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-accent text-white p-6 border-2 border-black">
        <p className="font-bold uppercase">Error: {error}</p>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  const getImpactColor = (hasDiff: boolean) => {
    return hasDiff ? 'bg-accent' : 'bg-muted';
  };

  return (
    <div className="space-y-12">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 pb-8 border-b-4 border-black">
        <div>
          <h1 className="text-6xl font-black uppercase tracking-tighter text-black leading-none mb-2">Dashboard</h1>
          <p className="text-sm font-bold uppercase tracking-widest text-slate-500">System Status & Updates</p>
        </div>
        <div className="text-right hidden md:block">
           <p className="font-mono text-xs">{new Date().toLocaleDateString()}</p>
        </div>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-0 border-2 border-black bg-black">
        {/* Gap-0 + border on parent + gap simulates grid lines if we use bg color, but let's use margin/border approach */}
        <div className="bg-white border-r-0 md:border-r-2 border-b-2 md:border-b-0 border-black p-0">
          <StatCard 
            number="01"
            title="Routes Active" 
            value={stats.totalRoutes} 
            link="/routes" 
            icon={<Map className="w-8 h-8" />}
          />
        </div>
        <div className="bg-white border-r-0 md:border-r-2 border-b-2 md:border-b-0 border-black p-0">
          <StatCard 
            number="02"
            title="Sources Monitored" 
            value={stats.activeSources} 
            link="/sources" 
            icon={<Activity className="w-8 h-8" />}
          />
        </div>
        <div className="bg-white p-0">
          <StatCard 
            number="03"
            title="Changes / Month" 
            value={stats.changesLast30Days} 
            link="/changes" 
            icon={<FileText className="w-8 h-8" />}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        {/* Recent Changes - 7 Cols */}
        <div className="lg:col-span-7 space-y-6">
          <div className="flex items-center justify-between border-b-2 border-black pb-2">
            <h2 className="text-xl font-black uppercase tracking-tight">Recent Changes</h2>
            <Link to="/changes" className="text-xs font-bold uppercase tracking-widest hover:text-accent flex items-center">
              View All <ArrowUpRight className="w-3 h-3 ml-1" />
            </Link>
          </div>
          
          <div className="border-2 border-black">
            <table className="w-full">
              <thead className="bg-black text-white">
                <tr>
                  <th className="px-6 py-4 text-left text-[10px] font-bold uppercase tracking-widest">Detected</th>
                  <th className="px-6 py-4 text-left text-[10px] font-bold uppercase tracking-widest">Route</th>
                  <th className="px-6 py-4 text-right text-[10px] font-bold uppercase tracking-widest">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y-2 divide-black bg-white">
                {stats.recentChanges.slice(0, 5).map((change) => (
                  <tr key={change.id} className="group hover:bg-muted transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-3">
                        <div 
                          className={`w-3 h-3 ${getImpactColor(change.hasDiff)}`} 
                          title={change.hasDiff ? 'Change Detected' : 'No Change'}
                        />
                        <span className="font-mono text-xs">{formatDateShort(change.detectedAt)}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-bold text-sm uppercase">{change.route || change.sourceName}</div>
                      <div className="text-[10px] font-mono text-slate-500 mt-1">{change.sourceName}</div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link to={`/changes/${change.id}`}>
                        <Button size="sm" variant="secondary" className="h-8">Diff</Button>
                      </Link>
                    </td>
                  </tr>
                ))}
                {stats.recentChanges.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-6 py-12 text-center text-slate-500 font-mono text-sm">
                      // NO DATA DETECTED //
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* System Health - 5 Cols */}
        <div className="lg:col-span-5 space-y-6">
          <div className="flex items-center justify-between border-b-2 border-black pb-2">
            <h2 className="text-xl font-black uppercase tracking-tight">System Health</h2>
            <Link to="/sources" className="text-xs font-bold uppercase tracking-widest hover:text-accent flex items-center">
              Manage <ArrowUpRight className="w-3 h-3 ml-1" />
            </Link>
          </div>
          
          <div className="border-2 border-black bg-white p-6 space-y-6 relative">
            <div className="absolute top-0 right-0 w-4 h-4 bg-black"></div>
            <div className="absolute bottom-0 left-0 w-4 h-4 bg-black"></div>

            {stats.sourceHealth.slice(0, 5).map((source) => (
              <div key={source.sourceId} className="flex items-center justify-between pb-4 border-b border-dashed border-black last:border-0 last:pb-0">
                <div>
                  <div className="font-bold text-sm uppercase">{source.sourceName}</div>
                  <div className="text-[10px] font-mono text-slate-500 mt-1">
                    Checked: {formatDateShort(source.lastCheckedAt)}
                  </div>
                </div>
                <Badge status={transformStatus(source.status)} />
              </div>
            ))}
          </div>
          
          <div className="bg-accent p-6 text-white border-2 border-black">
            <h3 className="font-bold uppercase tracking-widest text-xs mb-2">System Status</h3>
            <p className="text-2xl font-black uppercase">Operational</p>
            <p className="text-[10px] font-mono mt-2 opacity-80">Uptime: 99.9%</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;