import React, { useState } from 'react';
import { Button, Card } from '../components/Common';
import { Sparkles, Save, ShieldCheck, Check } from 'lucide-react';

const Settings: React.FC = () => {
  const [aiEnabled, setAiEnabled] = useState(true);
  const [emailSummaries, setEmailSummaries] = useState(true);
  const [impactEnabled, setImpactEnabled] = useState(true);
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const handleSave = () => {
    setIsSaving(true);
    setTimeout(() => {
      setIsSaving(false);
      alert('Settings saved successfully');
    }, 800);
  };

  const SquareToggle = ({ checked, onChange, id }: { checked: boolean, onChange: () => void, id: string }) => (
    <div className="relative inline-block w-12 h-6 align-middle select-none">
      <input 
        type="checkbox" 
        name={id} 
        id={id} 
        className="sr-only"
        checked={checked}
        onChange={onChange}
      />
      <div 
        className={`w-12 h-6 border-2 border-black transition-colors duration-200 cursor-pointer ${checked ? 'bg-accent' : 'bg-white'}`}
        onClick={onChange}
      >
        <div className={`absolute top-0.5 left-0.5 bg-black w-4 h-4 transition-transform duration-200 ${checked ? 'translate-x-6 bg-white' : 'translate-x-0'}`}></div>
      </div>
    </div>
  );

  return (
    <div className="space-y-12 max-w-4xl mx-auto">
      <div className="border-b-4 border-black pb-8">
        <h1 className="text-6xl font-black uppercase tracking-tighter text-black leading-none mb-2">Settings</h1>
        <p className="text-sm font-bold uppercase tracking-widest text-slate-500">System Configuration</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-12">
        <div className="md:col-span-4">
           <h2 className="text-2xl font-black uppercase tracking-tight mb-4">Intelligence</h2>
           <p className="text-sm text-slate-600 leading-relaxed">
             Configure automated analysis engines and notification density.
           </p>
        </div>

        <div className="md:col-span-8">
          <Card className="p-12 space-y-10 relative overflow-hidden">
             {/* Decorative background element */}
             <div className="absolute top-0 right-0 p-4 opacity-10">
                <Sparkles className="w-32 h-32" />
             </div>

             <div className="space-y-8 relative z-10">
              <div className="flex items-start justify-between group">
                <div>
                  <label htmlFor="ai-toggle" className="text-lg font-bold uppercase tracking-wide block group-hover:text-accent transition-colors">AI Summaries</label>
                  <p className="text-sm text-slate-500 mt-1 max-w-sm">Use LLMs to generate natural language summaries of policy diffs.</p>
                </div>
                <SquareToggle id="ai-toggle" checked={aiEnabled} onChange={() => setAiEnabled(!aiEnabled)} />
              </div>

              <div className={`flex items-start justify-between group transition-opacity ${!aiEnabled ? 'opacity-50 pointer-events-none' : ''}`}>
                <div>
                  <label htmlFor="email-toggle" className="text-lg font-bold uppercase tracking-wide block group-hover:text-accent transition-colors">Email Enrichment</label>
                  <p className="text-sm text-slate-500 mt-1 max-w-sm">Include generated summaries in the body of alert emails.</p>
                </div>
                <SquareToggle id="email-toggle" checked={emailSummaries} onChange={() => setEmailSummaries(!emailSummaries)} />
              </div>

              <div className="flex items-start justify-between group">
                <div>
                  <label htmlFor="impact-toggle" className="text-lg font-bold uppercase tracking-wide block group-hover:text-accent transition-colors">Impact Assessment</label>
                  <p className="text-sm text-slate-500 mt-1 max-w-sm">Automated scoring (High/Medium/Low) based on diff semantic analysis.</p>
                </div>
                <SquareToggle id="impact-toggle" checked={impactEnabled} onChange={() => setImpactEnabled(!impactEnabled)} />
              </div>
            </div>

            <div className="mt-12 pt-8 border-t-2 border-black border-dashed">
              <div className="flex items-start gap-4">
                 <div className="relative flex items-start">
                   <div className="flex items-center h-5">
                     <input 
                        type="checkbox" 
                        id="disclaimer" 
                        className="h-5 w-5 text-black border-2 border-black rounded-none focus:ring-0 cursor-pointer"
                        checked={disclaimerAccepted}
                        onChange={() => setDisclaimerAccepted(!disclaimerAccepted)}
                     />
                   </div>
                   <div className="ml-3 text-sm">
                     <label htmlFor="disclaimer" className="font-bold uppercase text-black">Legal Disclaimer</label>
                     <p className="text-slate-500 mt-1 text-xs">
                       I acknowledge that automated insights are not legal advice and must be verified.
                     </p>
                   </div>
                 </div>
              </div>
              
              <div className="mt-8 flex justify-end">
                <Button onClick={handleSave} isLoading={isSaving} disabled={!disclaimerAccepted} size="lg">
                  <Save className="w-4 h-4 mr-2" /> Save Configuration
                </Button>
              </div>
            </div>
          </Card>
          
          <div className="mt-6 flex items-center justify-center gap-2 text-[10px] font-mono uppercase text-slate-400">
            <ShieldCheck className="w-3 h-3" /> 
            <span>Secure Processing Environment • No Training on Client Data</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;