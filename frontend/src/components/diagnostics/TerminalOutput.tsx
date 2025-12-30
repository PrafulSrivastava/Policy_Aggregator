/**
 * Terminal Output Component
 * Displays scrolling log output with monospace font in terminal-style
 */

import React, { useEffect, useRef } from 'react';

interface TerminalOutputProps {
  logs: string[];
}

const TerminalOutput: React.FC<TerminalOutputProps> = ({ logs }) => {
  const terminalRef = useRef<HTMLDivElement>(null);

  /**
   * Auto-scroll to bottom when new logs are added
   */
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="card">
      <h2 className="text-xl font-display font-semibold uppercase tracking-widest mb-4">
        Terminal Output
      </h2>
      
      <div
        ref={terminalRef}
        className="bg-black text-green-400 font-mono text-sm p-4 h-64 overflow-y-auto border border-black"
        style={{
          fontFamily: '"JetBrains Mono", monospace',
        }}
      >
        {logs.length === 0 ? (
          <div className="text-gray-500 italic">
            Waiting for operation...
          </div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="mb-1">
              <span className="text-gray-500">$ </span>
              <span>{log}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default TerminalOutput;

