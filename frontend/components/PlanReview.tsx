import React, { useState } from 'react';
import { Network, ArrowRight, CheckCircle2, Lightbulb, BookOpen, ChevronDown, ChevronUp } from 'lucide-react';
import { WorkflowPlan } from '@/lib/api';

interface PlanReviewProps {
    plan: WorkflowPlan;
    onConfirm: () => void;
    isConfirming: boolean;
}

export const PlanReview: React.FC<PlanReviewProps> = ({ plan, onConfirm, isConfirming }) => {
    const [showThinking, setShowThinking] = useState(true);

    return (
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
            <div className="bg-slate-50 px-6 py-4 border-b border-slate-200 flex justify-between items-center">
                <div className="flex items-center gap-2">
                    <Network className="w-5 h-5 text-blue-600" />
                    <h3 className="font-semibold text-slate-800">Workflow Blueprint</h3>
                </div>
                {plan.referenced_templates && plan.referenced_templates.length > 0 && (
                    <div className="flex items-center gap-2 text-xs text-slate-500 bg-white px-3 py-1 rounded-full border border-slate-200">
                        <BookOpen className="w-3 h-3" />
                        <span>Referenced: {plan.referenced_templates.join(', ')}</span>
                    </div>
                )}
            </div>

            <div className="p-6 space-y-6">
                {/* Thinking Process Section */}
                {plan.thinking_process && (
                    <div className="bg-amber-50/30 border border-amber-100 rounded-lg overflow-hidden">
                        <button 
                            onClick={() => setShowThinking(!showThinking)}
                            className="w-full px-4 py-3 flex items-center justify-between text-amber-900 bg-amber-50/50 hover:bg-amber-50 transition-colors"
                        >
                            <div className="flex items-center gap-2 font-medium text-sm">
                                <Lightbulb className="w-4 h-4 text-amber-500" />
                                <span>AI Thinking Process</span>
                            </div>
                            {showThinking ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                        </button>
                        {showThinking && (
                            <div className="p-4 text-sm text-slate-600 leading-relaxed border-t border-amber-100 animate-in fade-in slide-in-from-top-1 duration-200">
                                <p className="whitespace-pre-wrap">{plan.thinking_process}</p>
                            </div>
                        )}
                    </div>
                )}

                {/* Summary Section */}
                <div>
                    <h4 className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-2">Summary</h4>
                    <p className="text-slate-700 leading-relaxed bg-slate-50 p-3 rounded-md border border-slate-100">
                        {plan.summary}
                    </p>
                </div>

                {/* Pre-flight Checks / Questions */}
                {plan.questions_to_user && plan.questions_to_user.length > 0 && (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                        <h4 className="text-sm font-bold text-amber-800 uppercase tracking-wider mb-2 flex items-center gap-2">
                            <span className="w-2 h-2 bg-amber-500 rounded-full animate-pulse" />
                            Pre-flight Checks
                        </h4>
                        <ul className="list-disc list-inside text-sm text-amber-800 space-y-1">
                            {plan.questions_to_user.map((q: string, i: number) => (
                                <li key={i}>{q}</li>
                            ))}
                        </ul>
                        <p className="text-xs text-amber-600 mt-2 italic">
                            * Please ensure these conditions are met, otherwise the workflow might fail.
                        </p>
                    </div>
                )}

                {/* Node Flow Visualization (List) */}
                <div>
                    <h4 className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-3">Execution Flow</h4>
                    <div className="space-y-3">
                        {plan.nodes.map((node, index) => (
                            <div key={index} className="flex items-center gap-3 group">
                                {/* Connector Line */}
                                {index > 0 && (
                                    <div className="flex justify-center w-8">
                                        <div className="h-full w-0.5 bg-slate-200 group-first:h-0"></div>
                                    </div>
                                )}

                                <div className="flex-1 flex gap-4 p-3 bg-white border border-slate-200 rounded-lg hover:border-blue-300 transition-colors shadow-sm">
                                    <div className="flex flex-col items-center gap-1 min-w-[32px]">
                                        <div className="w-8 h-8 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center text-sm font-bold border border-blue-100">
                                            {index + 1}
                                        </div>
                                    </div>

                                    <div>
                                        <h5 className="font-semibold text-slate-800 flex items-center gap-2">
                                            {node.name}
                                            <span className="text-xs font-normal text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
                                                {node.type}
                                            </span>
                                        </h5>
                                        <p className="text-sm text-slate-600 mt-1">{node.purpose}</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Logic Description */}
                <div>
                    <h4 className="text-sm font-medium text-slate-500 uppercase tracking-wider mb-2">Logic & Data Flow</h4>
                    <div className="text-sm text-slate-600 bg-blue-50/50 p-4 rounded-lg border border-blue-100">
                        {plan.connections_logic}
                    </div>
                </div>

                {/* Action Button */}
                <div className="pt-4 flex justify-end">
                    <button
                        onClick={onConfirm}
                        disabled={isConfirming}
                        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2.5 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
                    >
                        {isConfirming ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                Generating Code...
                            </>
                        ) : (
                            <>
                                <CheckCircle2 className="w-4 h-4" />
                                Confirm & Generate JSON
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};
