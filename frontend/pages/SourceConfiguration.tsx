import React, { useState } from 'react';
import { Badge, Button, Card, Input, Modal, Select } from '../components/Common';
import { COUNTRIES, MOCK_SOURCES, VISA_TYPES } from '../data';
import { SourceConfig } from '../types';
import { Edit2, ExternalLink, PlayCircle, Plus, RefreshCw } from 'lucide-react';

const SourceConfiguration: React.FC = () => {
  const [sources, setSources] = useState<SourceConfig[]>(MOCK_SOURCES);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isTestLoading, setIsTestLoading] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  // Form State
  const [formState, setFormState] = useState({
    country: '',
    visaType: '',
    url: '',
    fetchType: 'HTML',
    checkFrequency: 'Daily'
  });

  const handleTestFetch = () => {
    setIsTestLoading(true);
    setTestResult(null);
    setTimeout(() => {
      setIsTestLoading(false);
      setTestResult({
        success: true,
        preview: "<html><head><title>Visa Requirements</title>...</head><body>...</body></html>",
        hash: "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        duration: "0.45s"
      });
    }, 1500);
  };

  const handleSave = () => {
    const newSource: SourceConfig = {
      id: Date.now(),
      name: `${formState.country} - ${formState.visaType} Source`,
      country: formState.country,
      visaType: formState.visaType,
      url: formState.url,
      fetchType: formState.fetchType as any,
      checkFrequency: formState.checkFrequency as any,
      lastChecked: "Just now",
      lastChangeDetected: "Never",
      status: "Healthy"
    };
    setSources([newSource, ...sources]);
    setIsModalOpen(false);
    setTestResult(null);
    setFormState({ country: '', visaType: '', url: '', fetchType: 'HTML', checkFrequency: 'Daily' });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Source Configuration</h1>
          <p className="text-slate-500 mt-1">Manage external data sources and fetch settings.</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus className="w-4 h-4 mr-2" /> Add Source
        </Button>
      </div>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Source Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Details</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Config</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Last Checked</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-slate-200">
              {sources.map((source) => (
                <tr key={source.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-slate-900">{source.name}</div>
                    <a href={source.url} target="_blank" rel="noreferrer" className="text-xs text-primary hover:underline flex items-center mt-1">
                      {source.url.substring(0, 30)}... <ExternalLink className="w-3 h-3 ml-1" />
                    </a>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                    <div>{source.country}</div>
                    <div className="text-xs text-slate-500">{source.visaType}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    <div className="flex gap-2">
                       <span className="px-2 py-0.5 bg-slate-100 border border-slate-200 rounded text-xs text-slate-600">{source.fetchType}</span>
                       <span className="px-2 py-0.5 bg-slate-100 border border-slate-200 rounded text-xs text-slate-600">{source.checkFrequency}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                    {source.lastChecked}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge status={source.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end gap-3">
                      <button title="Test Fetch" className="text-slate-400 hover:text-green-600 transition-colors">
                        <PlayCircle className="w-4 h-4" />
                      </button>
                      <button title="Edit" className="text-slate-400 hover:text-primary transition-colors">
                        <Edit2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Configure Source"
        size="lg"
        footer={
          <>
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={!formState.url}>Save Source</Button>
          </>
        }
      >
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Select 
            label="Country *"
            value={formState.country}
            onChange={e => setFormState({...formState, country: e.target.value})}
            options={COUNTRIES.map(c => ({ value: c, label: c }))}
          />
          <Select 
            label="Visa Type *"
            value={formState.visaType}
            onChange={e => setFormState({...formState, visaType: e.target.value})}
            options={VISA_TYPES.map(vt => ({ value: vt, label: vt }))}
          />
          <div className="md:col-span-2">
            <Input
              label="Source URL *"
              value={formState.url}
              onChange={e => setFormState({...formState, url: e.target.value})}
              placeholder="https://..."
            />
          </div>
          <Select 
            label="Fetch Type"
            value={formState.fetchType}
            onChange={e => setFormState({...formState, fetchType: e.target.value})}
            options={[{value: 'HTML', label: 'HTML Scraping'}, {value: 'PDF', label: 'PDF Parse'}]}
          />
          <Select 
            label="Frequency"
            value={formState.checkFrequency}
            onChange={e => setFormState({...formState, checkFrequency: e.target.value})}
            options={[{value: 'Daily', label: 'Daily'}, {value: 'Weekly', label: 'Weekly'}]}
          />
        </div>

        <div className="mt-6 border-t border-slate-100 pt-4">
           <div className="flex justify-between items-center mb-2">
             <h4 className="text-sm font-medium text-slate-700">Test Configuration</h4>
             <Button size="sm" variant="secondary" onClick={handleTestFetch} isLoading={isTestLoading}>
                <RefreshCw className="w-3 h-3 mr-2" /> Test Fetch
             </Button>
           </div>
           
           {testResult && (
             <div className="bg-slate-50 rounded-md p-3 text-sm border border-slate-200">
                <div className="flex items-center text-green-600 mb-1 font-medium">
                  <Badge status="Success" text="Fetch Successful" />
                  <span className="ml-2 text-slate-500 text-xs">Duration: {testResult.duration}</span>
                </div>
                <div className="text-xs font-mono text-slate-500 truncate mb-2">Hash: {testResult.hash}</div>
                <div className="text-xs text-slate-700 bg-white p-2 rounded border border-slate-200 font-mono h-20 overflow-y-auto">
                  {testResult.preview}
                </div>
             </div>
           )}
        </div>
      </Modal>
    </div>
  );
};

export default SourceConfiguration;