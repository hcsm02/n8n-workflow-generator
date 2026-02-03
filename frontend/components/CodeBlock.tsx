import React, { useState } from 'react';
import { Copy, Check, FileJson } from 'lucide-react';

interface CodeBlockProps {
    code: object;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ code }) => {
    const [copied, setCopied] = useState(false);
    const codeString = JSON.stringify(code, null, 2);

    const handleCopy = () => {
        navigator.clipboard.writeText(codeString);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="w-full bg-slate-900 rounded-lg overflow-hidden border border-slate-700 shadow-xl">
            <div className="px-4 py-3 bg-slate-800/50 border-b border-slate-700 flex justify-between items-center">
                <div className="flex items-center gap-2 text-slate-300">
                    <FileJson className="w-4 h-4" />
                    <span className="text-sm font-medium">n8n Workflow JSON</span>
                </div>
                <button
                    onClick={handleCopy}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-medium transition-colors"
                >
                    {copied ? (
                        <>
                            <Check className="w-3.5 h-3.5" />
                            Copied!
                        </>
                    ) : (
                        <>
                            <Copy className="w-3.5 h-3.5" />
                            Copy Code
                        </>
                    )}
                </button>
            </div>
            <pre className="p-4 overflow-x-auto text-sm font-mono leading-relaxed text-blue-100 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
                <code>{codeString}</code>
            </pre>
            <div className="px-4 py-2 bg-slate-800/30 border-t border-slate-700 text-xs text-slate-400 text-center">
                Copy this JSON and press standard <kbd className="bg-slate-700 px-1 rounded text-slate-300">Ctrl/Cmd + V</kbd> in your n8n editor to import.
            </div>
        </div>
    );
};
