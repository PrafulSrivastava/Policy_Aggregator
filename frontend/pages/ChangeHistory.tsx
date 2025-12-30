import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button, Card, Select } from '../components/Common';
import { MOCK_CHANGES, COUNTRIES } from '../data';
import { Filter, X } from 'lucide-react';

const ChangeHistory: React.FC = () => {
  const [filterRoute, setFilterRoute] = useState('');
  
  // Basic filtering for demo
  const filteredChanges = MOCK_CHANGES.filter(change => 
    !filterRoute || change.route.origin.includes(filterRoute) || change.route.destination.includes(filterRoute)
  );

  const getImpactColor = (score?: 'High' | 'Medium' | 'Low') => {
    switch(score) {
      case 'High': return 'bg-red-500';
      case 'Medium': return 'bg-amber-500';
      case 'Low': return 'bg-green-500';
      default: return 'bg-slate-300';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Change History</h1>
          <p className="text-slate-500 mt-1">Audit log of all detected policy modifications.</p>
        </div>
      </div>

      {/* Filter Bar */}
      <Card className="p-4">
        <div className="flex flex-col sm:flex-row gap-4 items-end">
          <Select 
            label="Filter by Route" 
            options={COUNTRIES.map(c => ({ value: c, label: c }))} 
            value={filterRoute}
            onChange={e => setFilterRoute(e.target.value)}
            className="min-w-[200px]"
          />
          
          {filterRoute && (
            <Button variant="secondary" onClick={() => setFilterRoute('')} className="mb-0.5">
              <X className="w-4 h-4 mr-2" /> Clear Filters
            </Button>
          )}
        </div>
      </Card>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Detected</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Route</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Source</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider w-1/3">Preview</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {filteredChanges.map((change) => (
                <tr key={change.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                    <div className="flex items-center gap-2">
                      {change.detectedAt}
                      {change.impactAssessment && (
                        <div 
                          className={`w-2 h-2 rounded-full ${getImpactColor(change.impactAssessment.score)}`} 
                          title={`${change.impactAssessment.score} Impact`}
                        />
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900">
                     {change.route.origin} → {change.route.destination}
                     <div className="text-xs text-slate-500 font-normal">{change.route.visaType}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">{change.sourceName}</td>
                  <td className="px-6 py-4 text-sm font-mono text-slate-500 text-xs">
                    <div className="line-clamp-2 whitespace-pre-line">
                      {change.changePreview}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <Link to={`/changes/${change.id}`}>
                      <Button variant="secondary" size="sm">View Full Diff</Button>
                    </Link>
                  </td>
                </tr>
              ))}
              {filteredChanges.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                    <div className="flex flex-col items-center justify-center">
                      <Filter className="w-12 h-12 text-slate-200 mb-3" />
                      <p>No changes match your filters.</p>
                      {filterRoute && (
                        <Button variant="ghost" size="sm" onClick={() => setFilterRoute('')} className="mt-2 text-primary">
                          Clear Filters
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination Mock */}
        <div className="bg-white px-4 py-3 border-t border-slate-200 flex items-center justify-between sm:px-6">
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-slate-700">
                Showing <span className="font-medium">1</span> to <span className="font-medium">{filteredChanges.length}</span> of <span className="font-medium">{filteredChanges.length}</span> results
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                <button disabled className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-slate-300 bg-white text-sm font-medium text-slate-500 hover:bg-slate-50 disabled:opacity-50">Previous</button>
                <button className="relative inline-flex items-center px-4 py-2 border border-slate-300 bg-white text-sm font-medium text-primary hover:bg-slate-50">1</button>
                <button disabled className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-slate-300 bg-white text-sm font-medium text-slate-500 hover:bg-slate-50 disabled:opacity-50">Next</button>
              </nav>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default ChangeHistory;