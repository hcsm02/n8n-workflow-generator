"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, AlertCircle } from 'lucide-react';
import { api, WorkflowPlan } from '@/lib/api';
import { PlanReview } from './PlanReview';
import { CodeBlock } from './CodeBlock';

type InteractionState = 'idle' | 'planning' | 'review' | 'generating' | 'done' | 'error';

// 带计时器的等待提示组件
const PlanningIndicator = ({ message, hint }: { message: string; hint: string }) => {
    const [elapsed, setElapsed] = React.useState(0);
    React.useEffect(() => {
        const timer = setInterval(() => setElapsed(s => s + 1), 1000);
        return () => clearInterval(timer);
    }, []);
    const mins = Math.floor(elapsed / 60);
    const secs = elapsed % 60;
    const timeStr = mins > 0 ? `${mins}分${secs}秒` : `${secs}秒`;
    return (
        <div className="flex justify-start">
            <div className="bg-white border border-slate-200 px-5 py-3 rounded-2xl rounded-tl-sm shadow-sm space-y-1">
                <div className="flex items-center gap-3">
                    <Sparkles className="w-4 h-4 text-amber-500 animate-spin" />
                    <span className="text-slate-700 font-medium">{message}</span>
                    <span className="text-sm text-blue-500 font-mono">{timeStr}</span>
                </div>
                <p className="text-xs text-slate-400">{hint}</p>
            </div>
        </div>
    );
};

export const WorkflowChat = () => {
    const [input, setInput] = useState('');
    const [n8nVersion, setN8nVersion] = useState('1.76.1');
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
            const response = await api.createPlan(input, n8nVersion);
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
                    <PlanningIndicator message="AI Architect 正在设计您的工作流..." hint="首次调用需要 1-3 分钟（LLM + MCP 工具搜索模板中）" />
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
                    <PlanningIndicator message="AI Coder 正在生成 n8n 工作流 JSON..." hint="Coder 正在查询节点参数并生成代码" />
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
                    <div className="max-w-4xl mx-auto">
                        <div className="flex items-center gap-2 mb-2">
                            <label className="text-xs text-slate-500 whitespace-nowrap">n8n 版本:</label>
                            <select
                                value={n8nVersion}
                                onChange={(e) => setN8nVersion(e.target.value)}
                                className="text-xs border border-slate-300 rounded-md px-2 py-1 bg-white text-slate-700 focus:ring-1 focus:ring-blue-400 outline-none"
                            >
                                <option value="1.76.1">v1.76.1 (最新)</option>
                                <option value="1.70.0">v1.70.0</option>
                                <option value="1.60.0">v1.60.0</option>
                                <option value="1.50.0">v1.50.0</option>
                                <option value="1.40.0">v1.40.0</option>
                                <option value="1.30.0">v1.30.0</option>
                            </select>
                        </div>
                        <div className="relative">
                            <textarea
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="描述你的自动化工作流需求（如：'每小时检查 RSS，如果有 AI 相关新闻就发送到 Slack'）..."
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
                    </div>
                    <p className="text-center text-xs text-slate-400 mt-2">
                        Powered by LangGraph Multi-Agent Architecture
                    </p>
                </div>
            )}
        </div>
    );
};
