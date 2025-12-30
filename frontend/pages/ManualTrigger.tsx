import React, { useState } from 'react';
import { Badge, Button, Card, Select } from '../components/Common';
import { MOCK_SOURCES } from '../data';
import { FetchResult } from '../types';
import { Play, RotateCcw, Copy, CheckCircle, AlertTriangle } from 'lucide-react';

const ManualTrigger: React.FC = () => {
  const [selectedSource, setSelectedSource] = useState('');
  const [isFetching, setIsFetching] = useState(false);
  const [result, setResult] = useState<FetchResult | null>(null);

  const handleTrigger = () => {
    if (!selectedSource) return;
    setIsFetching(true);
    setResult(null);

    // Mock Fetch Logic
    setTimeout(() => {
      setIsFetching(false);
      // Simulate random outcome
      const isChange = Math.random() > 0.5;
      
      setResult({
        success: true,
        fetchedAt: new Date().toLocaleString(),
        duration: 1.25,
        contentHash: "sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
        contentLength: 14205,
        contentPreview: `<!DOCTYPE html>\n<html lang="en">\n<head>\n<title>Official Visa Policy</title>\n...</head>\n<body>\n  <h1>Current Requirements</h1>\n  <p>Effective immediately, all applicants must...</p>\n</body>\n</html>`,
        changeDetected: isChange,
        previousHash: "sha256:oldhash...",
        diffPreview: isChange ? "- Fee: €60\n+ Fee: €80" : undefined
      });
    }, 2000);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Manual Trigger</h1>
        <p className="text-slate-500 mt-1">Force fetch updates for debugging or immediate verification.</p>
      </div>

      <Card className="p-6">
        <div className="flex flex-col md:flex-row gap-4 items-end">
          <div className="w-full md:w-1/2">
             <Select 
               label="Select Source"
               value={selectedSource}
               onChange={e => setSelectedSource(e.target.value)}
               options={MOCK_SOURCES.map(s => ({ value: String(s.id), label: s.name }))}
             />
          </div>
          <Button 
            size="lg" 
            onClick={handleTrigger} 
            disabled={!selectedSource} 
            isLoading={isFetching}
            className="w-full md:w-auto"
          >
            {!isFetching && <Play className="w-4 h-4 mr-2" />}
            {isFetching ? "Fetching Source..." : "Trigger Fetch"}
          </Button>
        </div>
      </Card>

      {result && (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-slate-900">Fetch Result</h2>
            <Badge status={result.success ? 'Success' : 'Error'} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="p-6 lg:col-span-1 space-y-4 h-fit">
              <div>
                <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold">Metadata</p>
                <div className="mt-2 space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Timestamp:</span>
                    <span className="font-medium">{result.fetchedAt}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Duration:</span>
                    <span className="font-medium">{result.duration}s</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Size:</span>
                    <span className="font-medium">{result.contentLength} chars</span>
                  </div>
                </div>
              </div>
              <div className="pt-4 border-t border-slate-100">
                <p className="text-xs text-slate-500 uppercase tracking-wide font-semibold mb-2">Hash</p>
                <div className="bg-slate-100 p-2 rounded text-xs font-mono break-all text-slate-600 flex justify-between items-start gap-2">
                  {result.contentHash}
                  <button className="text-slate-400 hover:text-slate-600"><Copy className="w-3 h-3" /></button>
                </div>
              </div>
            </Card>

            <div className="lg:col-span-2 space-y-6">
              <Card className={`p-4 border-l-4 ${result.changeDetected ? 'border-l-amber-500 bg-amber-50' : 'border-l-green-500 bg-green-50'}`}>
                 <div className="flex items-start">
                    {result.changeDetected ? <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 mr-3" /> : <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 mr-3" />}
                    <div>
                       <h3 className={`text-sm font-bold ${result.changeDetected ? 'text-amber-800' : 'text-green-800'}`}>
                         {result.changeDetected ? 'Change Detected' : 'No Changes Detected'}
                       </h3>
                       <p className={`text-sm mt-1 ${result.changeDetected ? 'text-amber-700' : 'text-green-700'}`}>
                         {result.changeDetected 
                           ? "Content hash differs from previous version. See diff below." 
                           : "Content hash matches the last successful fetch."}
                       </p>
                    </div>
                 </div>
              </Card>

              {result.changeDetected && result.diffPreview && (
                <Card className="overflow-hidden">
                  <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 text-xs font-medium text-slate-500 uppercase">
                    Diff Preview
                  </div>
                  <pre className="p-4 bg-white text-sm font-mono whitespace-pre-wrap">
                    {result.diffPreview.split('\n').map((line, i) => (
                      <div key={i} className={line.startsWith('+') ? 'text-green-600 bg-green-50' : line.startsWith('-') ? 'text-red-600 bg-red-50' : 'text-slate-600'}>
                        {line}
                      </div>
                    ))}
                  </pre>
                </Card>
              )}
              
              <Card className="overflow-hidden">
                <div className="bg-slate-50 px-4 py-2 border-b border-slate-200 text-xs font-medium text-slate-500 uppercase">
                  Raw Content Preview
                </div>
                <div className="p-4 bg-white font-mono text-xs text-slate-600 h-64 overflow-y-auto whitespace-pre-wrap">
                  {result.contentPreview}
                </div>
              </Card>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ManualTrigger;