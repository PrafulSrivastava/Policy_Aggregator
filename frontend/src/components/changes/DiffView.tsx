/**
 * DiffView Component
 * Displays unified diff with color coding for additions and deletions
 */

import React, { useMemo } from 'react';

interface DiffViewProps {
  diff: string;
  className?: string;
}

/**
 * Parse unified diff and categorize lines
 */
const parseDiff = (diff: string): Array<{ type: 'added' | 'removed' | 'context' | 'header'; line: string }> => {
  const lines = diff.split('\n');
  const parsed: Array<{ type: 'added' | 'removed' | 'context' | 'header'; line: string }> = [];

  for (const line of lines) {
    if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('@@')) {
      parsed.push({ type: 'header', line });
    } else if (line.startsWith('+') && !line.startsWith('+++')) {
      parsed.push({ type: 'added', line: line.substring(1) });
    } else if (line.startsWith('-') && !line.startsWith('---')) {
      parsed.push({ type: 'removed', line: line.substring(1) });
    } else if (line.startsWith(' ')) {
      parsed.push({ type: 'context', line: line.substring(1) });
    } else {
      // Handle lines that don't match standard diff format
      parsed.push({ type: 'context', line });
    }
  }

  return parsed;
};

const DiffView: React.FC<DiffViewProps> = ({ diff, className = '' }) => {
  const parsedLines = useMemo(() => parseDiff(diff), [diff]);

  return (
    <div className={`border-2 border-foreground bg-background overflow-auto ${className}`}>
      <pre className="font-mono text-sm p-4 m-0">
        {parsedLines.map((item, index) => {
          let lineClass = 'block py-0.5 px-2';
          let prefix = '';

          switch (item.type) {
            case 'added':
              lineClass += ' bg-green-100 text-green-900';
              prefix = '+ ';
              break;
            case 'removed':
              lineClass += ' bg-red-100 text-red-900 line-through';
              prefix = '- ';
              break;
            case 'header':
              lineClass += ' bg-muted text-mutedForeground font-semibold';
              break;
            case 'context':
            default:
              lineClass += ' text-foreground';
              prefix = '  ';
              break;
          }

          return (
            <div key={index} className={lineClass}>
              <span className="select-none text-mutedForeground mr-2">{prefix}</span>
              <span>{item.line || ' '}</span>
            </div>
          );
        })}
      </pre>
    </div>
  );
};

export default DiffView;


