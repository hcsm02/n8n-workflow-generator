"use client";

import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, AlertCircle } from 'lucide-react';
import { api, ConceptStep, ConceptResult, WorkflowPlan } from '@/lib/api';
import { ConceptReview } from './ConceptReview';
import { PlanReview } from './PlanReview';
import { CodeBlock } from './CodeBlock';

/**
 * 三阶段交互状态机：
 * idle → concepting → concept_review → planning → plan_review → generating → done
 */
type InteractionState =
    | 'idle'
    | 'concepting'      // Phase 0: 正在生成逻辑步骤
    | 'concept_review'  // 用户审核/修改逻辑步骤
    | 'planning'        // Phase 1: 正在映射节点
    | 'plan_review'     // 用户审核节点方案
    | 'generating'      // Phase 2: 正在生成 JSON
    | 'done'
    | 'error';

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
    const [n8nVersion, setN8nVersion] = useState('2.11.4');
    const [isCustomVersion, setIsCustomVersion] = useState(false);
    const [customVersion, setCustomVersion] = useState('');

    const [state, setState] = useState<InteractionState>('idle');
    const [threadId, setThreadId] = useState<string | null>(null);

    // Phase 0 数据
    const [concept, setConcept] = useState<ConceptResult | null>(null);
    const [isRefining, setIsRefining] = useState(false);

    // Phase 1 数据
    const [plan, setPlan] = useState<WorkflowPlan | null>(null);

    // Phase 2 数据
    const [resultCode, setResultCode] = useState<any>(null);
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [state, concept, plan, resultCode]);

    // ============================================================
    // Phase 0: 概念建模
    // ============================================================
    const handleConcept = async () => {
        if (!input.trim()) return;

        setState('concepting');
        setErrorMsg(null);
        setConcept(null);
        setPlan(null);
        setResultCode(null);

        try {
            const versionToSend = isCustomVersion ? customVersion : n8nVersion;
            const response = await api.createConcept(input, versionToSend);
            setThreadId(response.thread_id);
            setConcept(response.concept);
            setState('concept_review');
        } catch (err: any) {
            console.error(err);
            setErrorMsg(err.response?.data?.detail || "概念建模失败，请检查后端是否运行。");
            setState('error');
        }
    };

    // ============================================================
    // 对话式修改逻辑步骤
    // ============================================================
    const handleRefine = async (feedback: string, currentSteps: ConceptStep[]) => {
        if (!threadId) return;
        setIsRefining(true);

        try {
            const response = await api.refineConcept(threadId, feedback, currentSteps);
            setThreadId(response.thread_id);
            setConcept(response.concept);
            // 保持在 concept_review 状态
        } catch (err: any) {
            console.error(err);
            setErrorMsg(err.response?.data?.detail || "修改概念失败。");
            setState('error');
        } finally {
            setIsRefining(false);
        }
    };

    // ============================================================
    // Phase 1: 确认逻辑步骤 → 节点映射
    // ============================================================
    const handleConfirmConcept = async (finalSteps: ConceptStep[]) => {
        if (!threadId) return;

        setState('planning');
        try {
            const response = await api.confirmConcept(threadId, finalSteps);
            setThreadId(response.thread_id);
            setPlan(response.plan);
            setState('plan_review');
        } catch (err: any) {
            console.error(err);
            setErrorMsg(err.response?.data?.detail || "节点映射失败。");
            setState('error');
        }
    };

    // ============================================================
    // Phase 2: 确认节点方案 → JSON 生成
    // ============================================================
    const handleConfirmPlan = async () => {
        if (!threadId) return;

        setState('generating');
        try {
            const json = await api.confirmPlan(threadId);
            setResultCode(json);
            setState('done');
        } catch (err: any) {
            console.error(err);
            setErrorMsg(err.response?.data?.detail || "JSON 生成失败。");
            setState('error');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (state === 'idle' || state === 'done' || state === 'error') {
                handleConcept();
            }
        }
    };

    return (
        <div className="max-w-4xl mx-auto w-full space-y-8">

            {/* Messages / Interaction Log */}
            <div className="space-y-6">
                {/* User Request Bubble */}
                {(state !== 'idle' || concept) && (
                    <div className="flex justify-end">
                        <div className="bg-blue-600 text-white px-5 py-3 rounded-2xl rounded-tr-sm shadow-md max-w-[80%]">
                            <p className="whitespace-pre-wrap">{input}</p>
                        </div>
                    </div>
                )}

                {/* Phase 0: 概念建模中 */}
                {state === 'concepting' && (
                    <PlanningIndicator
                        message="正在分析需求，拆解逻辑步骤..."
                        hint="这一步非常快，不会超过 10 秒"
                    />
                )}

                {/* Phase 0: 概念审核 (可拖拽/可修改) */}
                {concept && (state === 'concept_review' || state === 'planning' || state === 'plan_review' || state === 'generating' || state === 'done') && (
                    <div className={`transition-opacity duration-500 ${(state as any) === 'concepting' ? 'opacity-0' : 'opacity-100'}`}>
                        <ConceptReview
                            concept={concept}
                            onConfirm={handleConfirmConcept}
                            onRefine={handleRefine}
                            isRefining={isRefining}
                            isConfirming={state === 'planning'}
                        />
                    </div>
                )}

                {/* Phase 1: 节点映射中 */}
                {state === 'planning' && (
                    <PlanningIndicator
                        message="AI Architect 正在匹配 n8n 节点..."
                        hint="正在参考模板和版本兼容性"
                    />
                )}

                {/* Phase 1: 节点方案审核 */}
                {plan && (state === 'plan_review' || state === 'generating' || state === 'done') && (
                    <div className={`transition-opacity duration-500 ${(state as any) === 'planning' ? 'opacity-0' : 'opacity-100'}`}>
                        <PlanReview
                            plan={plan}
                            onConfirm={handleConfirmPlan}
                            isConfirming={state === 'generating'}
                        />
                    </div>
                )}

                {/* Phase 2: 生成中 */}
                {state === 'generating' && (
                    <PlanningIndicator
                        message="AI Coder 正在生成 n8n 工作流 JSON..."
                        hint="正在组装节点参数和连接"
                    />
                )}

                {/* Phase 2: 最终代码 */}
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

            {/* Input Area — 仅在 idle/done/error 时显示 */}
            {(state === 'idle' || state === 'done' || state === 'error') && (
                <div className="fixed bottom-0 left-0 right-0 p-4 bg-white/80 backdrop-blur-md border-t border-slate-200">
                    <div className="max-w-4xl mx-auto">
                        <div className="flex items-center gap-2 mb-2">
                            <label className="text-xs text-slate-500 whitespace-nowrap">n8n 版本:</label>
                            <select
                                value={isCustomVersion ? 'custom' : n8nVersion}
                                onChange={(e) => {
                                    if (e.target.value === 'custom') {
                                        setIsCustomVersion(true);
                                    } else {
                                        setIsCustomVersion(false);
                                        setN8nVersion(e.target.value);
                                    }
                                }}
                                className="text-xs border border-slate-300 rounded-md px-2 py-1 bg-white text-slate-700 focus:ring-1 focus:ring-blue-400 outline-none"
                            >
                                <option value="2.11.4">v2.11.4 (最新稳定版)</option>
                                <option value="2.0.0">v2.0.0</option>
                                <option value="1.76.1">v1.76.1</option>
                                <option value="1.60.0">v1.60.0</option>
                                <option value="1.30.0">v1.30.0</option>
                                <option value="custom">手动输入...</option>
                            </select>
                            {isCustomVersion && (
                                <input
                                    type="text"
                                    value={customVersion}
                                    onChange={(e) => setCustomVersion(e.target.value)}
                                    placeholder="例如: 2.11.4"
                                    className="text-xs border border-slate-300 rounded-md px-2 py-1 w-24 outline-none focus:ring-1 focus:ring-blue-400"
                                />
                            )}
                        </div>
                        <div className="relative">
                            <textarea
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="描述你的自动化工作流需求（如：'定时检查 RSS，筛选 AI 新闻，用 AI 总结后发到飞书'）..."
                                className="w-full bg-slate-50 border border-slate-300 rounded-xl px-4 py-4 pr-14 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none resize-none shadow-sm transition-all"
                                rows={1}
                                style={{ minHeight: '60px' }}
                            />
                            <button
                                onClick={handleConcept}
                                disabled={!input.trim()}
                                className="absolute right-3 bottom-3 p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                <Send className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                    <p className="text-center text-xs text-slate-400 mt-2">
                        Powered by LangGraph Three-Stage Architecture
                    </p>
                </div>
            )}
        </div>
    );
};
