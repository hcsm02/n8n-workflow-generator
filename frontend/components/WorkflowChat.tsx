"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, AlertCircle } from 'lucide-react';
import { api, WorkflowPlan } from '@/lib/api';
import { PlanReview } from './PlanReview';
import { CodeBlock } from './CodeBlock';

type InteractionState = 'idle' | 'planning' | 'review' | 'generating' | 'done' | 'error';

export const WorkflowChat = () => {
    const [input, setInput] = useState('');
    const [state, setState] = useState<InteractionState>('idle');
    const [threadId, setThreadId] = useState<string | null>(null);
    const [plan, setPlan] = useState<WorkflowPlan | null>(null);
    const [resultCode, setResultCode] = useState<any>(null);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [state, plan, resultCode]);

    const handlePlan = async () => {
        if (!input.trim()) return;

        setState('planning');
        setErrorMsg(null);
        setPlan(null); // Reset previous plan if any
        setResultCode(null);

        try {
            const response = await api.createPlan(input);
            setThreadId(response.thread_id);
            setPlan(response.plan);
            setState('review');
        } catch (err: any) {
            console.error(err);
            setErrorMsg(err.response?.data?.detail || "Failed to create plan. Is the backend running?");
            setState('error');
        }
    };

    const handleConfirm = async () => {
        if (!threadId) return;

        setState('generating');
        try {
            const json = await api.confirmPlan(threadId);
            setResultCode(json);
            setState('done');
        } catch (err: any) {
            console.error(err);
            setErrorMsg(err.response?.data?.detail || "Failed to generate code.");
            setState('error');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (state === 'idle' || state === 'done' || state === 'error') {
                handlePlan();
            }
        }
    };

    return (
        <div className="max-w-4xl mx-auto w-full space-y-8">

            {/* Messages / Interaction Log */}
            <div className="space-y-6">
                {/* User Request Bubble */}
                {(state !== 'idle' || plan) && (
                    <div className="flex justify-end">
                        <div className="bg-blue-600 text-white px-5 py-3 rounded-2xl rounded-tr-sm shadow-md max-w-[80%]">
                            <p className="whitespace-pre-wrap">{input}</p>
                        </div>
                    </div>
                )}

                {/* System: Planning State */}
                {state === 'planning' && (
                    <div className="flex justify-start animate-pulse">
                        <div className="bg-white border border-slate-200 px-5 py-3 rounded-2xl rounded-tl-sm shadow-sm flex items-center gap-3">
                            <Sparkles className="w-4 h-4 text-amber-500 animate-spin-slow" />
                            <span className="text-slate-600">Architect is designing your workflow...</span>
                        </div>
                    </div>
                )}

                {/* System: Plan Review */}
                {plan && (
                    <div className={`transition-opacity duration-500 ${state === 'planning' ? 'opacity-0' : 'opacity-100'}`}>
                        <PlanReview
                            plan={plan}
                            onConfirm={handleConfirm}
                            isConfirming={state === 'generating'}
                        />
                    </div>
                )}

                {/* System: Generating Code State */}
                {state === 'generating' && (
                    <div className="flex justify-start animate-pulse">
                        <div className="bg-white border border-slate-200 px-5 py-3 rounded-2xl rounded-tl-sm shadow-sm flex items-center gap-3">
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" />
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce delay-75" />
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce delay-150" />
                            <span className="text-slate-600 ml-2">Coder is writing n8n implementation...</span>
                        </div>
                    </div>
                )}

                {/* System: Final Code */}
                {resultCode && (
                    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
                        <CodeBlock code={resultCode} />
                    </div>
                )}

                {/* Error Message */}
                {state === 'error' && (
                    <div className="flex justify-center">
                        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg flex items-center gap-2">
                            <AlertCircle className="w-5 h-5" />
                            <span>{errorMsg}</span>
                        </div>
                    </div>
                )}
            </div>

            <div ref={bottomRef} />

            {/* Input Area */}
            {/* Only show input if in idle state or done state to start over */}
            {(state === 'idle' || state === 'done' || state === 'error') && (
                <div className="fixed bottom-0 left-0 right-0 p-4 bg-white/80 backdrop-blur-md border-t border-slate-200">
                    <div className="max-w-4xl mx-auto relative">
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Describe your workflow logic (e.g., 'Every hour check RSS and post to Slack if related to AI')..."
                            className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-4 pr-14 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none shadow-sm transition-all"
                            rows={1}
                            style={{ minHeight: '60px' }}
                        />
                        <button
                            onClick={handlePlan}
                            disabled={!input.trim()}
                            className="absolute right-3 bottom-3 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <Send className="w-5 h-5" />
                        </button>
                    </div>
                    <p className="text-center text-xs text-slate-400 mt-2">
                        Powered by LangGraph Multi-Agent Architecture
                    </p>
                </div>
            )}
        </div>
    );
};
