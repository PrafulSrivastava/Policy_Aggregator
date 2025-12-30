import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Badge, Button, Card } from '../components/Common';
import { MOCK_CHANGES } from '../data';
import { PolicyChange } from '../types';
import { ArrowLeft, ExternalLink, Download, Sparkles, AlertTriangle } from 'lucide-react';

const ChangeDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [change, setChange] = useState<PolicyChange | null>(null);

  useEffect(() => {
    // Mock fetch
    const found = MOCK_CHANGES.find(c => c.id === Number(id));
    setChange(found || null);
  }, [id]);

  if (!change) {
    return <div className="text-center py-12">Loading change details...</div>;
  }

  // Parse Diff lines
  const diffLines = change.diff.split('\n');

  return (
    <div className="space-y-6">
      <div>
        <Link to="/changes" className="text-sm text-slate-500 hover:text-slate-900 inline-flex items-center mb-4">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back to Change History
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-1">
               <h1 className="text-2xl font-bold text-slate-900">Change Details</h1>
               <span className="bg-slate-100 text-slate-700 text-xs px-2 py-1 rounded font-mono">#{change.id}</span>
               {change.impactAssessment && (
                 <Badge 
                   status={change.impactAssessment.score} 
                   text={`${change.impactAssessment.score} Impact`} 
                 />
               )}
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-600">
               <span className="font-medium text-slate-900">{change.route.origin} → {change.route.destination}</span>
               <span>•</span>
               <span>{change.route.visaType}</span>
            </div>
          </div>
          <div className="flex gap-2">
            <a href={change.sourceUrl} target="_blank" rel="noreferrer">
              <Button variant="secondary" size="sm">
                <ExternalLink className="w-4 h-4 mr-2" /> View Source
              </Button>
            </a>
            <Button variant="secondary" size="sm">
              <Download className="w-4 h-4 mr-2" /> Export
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Source Info Side Card */}
        <div className="md:col-span-1 space-y-4">
          <Card className="p-4">
            <h3 className="font-semibold text-slate-900 mb-3 border-b pb-2 border-slate-100">Source Information</h3>
            <div className="space-y-3 text-sm">
              <div>
                <p className="text-slate-500 text-xs">Source Name</p>
                <p className="font-medium">{change.sourceName}</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs">Detected At</p>
                <p>{change.detectedAt}</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs">Last Checked</p>
                <p>{change.lastChecked}</p>
              </div>
              <div>
                <p className="text-slate-500 text-xs">Status</p>
                <Badge status="Warning" text="Change Detected" />
              </div>
            </div>
          </Card>
          
          {change.impactAssessment && (
            <Card className="p-4 bg-slate-50 border-slate-200">
              <h3 className="font-semibold text-slate-900 mb-2 flex items-center">
                 <AlertTriangle className="w-4 h-4 mr-2 text-amber-600" />
                 Impact Assessment
              </h3>
              <p className="text-sm text-slate-600 mb-2">
                {change.impactAssessment.explanation}
              </p>
              <div className="text-xs text-slate-400 mt-3 pt-2 border-t border-slate-200">
                * Automated assessment. Not legal advice.
              </div>
            </Card>
          )}
        </div>

        {/* Diff View */}
        <div className="md:col-span-2 space-y-6">
          
          {/* AI Summary Section */}
          {change.aiSummary && (
            <Card className="p-5 border-blue-100 bg-blue-50/50">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-semibold text-slate-900 flex items-center">
                  <Sparkles className="w-4 h-4 mr-2 text-primary" />
                  AI Summary
                </h3>
                <span className="bg-white/80 text-primary text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded border border-blue-100 shadow-sm">
                  AI-Generated
                </span>
              </div>
              <p className="text-slate-700 text-sm leading-relaxed">
                {change.aiSummary}
              </p>
              <div className="mt-3 text-[10px] text-slate-400">
                Disclaimer: This summary is AI-generated and may contain errors. Please verify with the full diff below.
              </div>
            </Card>
          )}

          <Card className="overflow-hidden border-slate-300 shadow-md">
            <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 flex justify-between items-center">
              <span className="text-sm font-medium text-slate-700">Unified Diff</span>
              <span className="text-xs text-slate-500 font-mono">UTF-8</span>
            </div>
            <div className="overflow-x-auto bg-white">
              <pre className="text-sm font-mono leading-6 min-w-full">
                {diffLines.map((line, idx) => {
                  const isAdd = line.startsWith('+');
                  const isDel = line.startsWith('-');
                  const lineNum = idx + 1;
                  
                  return (
                    <div 
                      key={idx} 
                      className={`flex ${isAdd ? 'bg-green-50' : isDel ? 'bg-red-50' : ''}`}
                    >
                      <span className="w-12 text-slate-400 text-right select-none pr-4 border-r border-slate-100 bg-slate-50">{lineNum}</span>
                      <span className={`px-4 flex-1 whitespace-pre-wrap ${isAdd ? 'text-green-800' : isDel ? 'text-red-800' : 'text-slate-600'}`}>
                        {line}
                      </span>
                    </div>
                  );
                })}
              </pre>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ChangeDetail;