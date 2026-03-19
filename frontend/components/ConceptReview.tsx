"use client";

import React, { useState } from 'react';
import {
    GripVertical, Trash2, Plus, MessageSquare, Check,
    Clock, Database, Filter, Wand2, Zap, Send as SendIcon,
    Lightbulb
} from 'lucide-react';
import { ConceptStep, ConceptResult } from '@/lib/api';

// ============================================================
// 步骤类型与图标/颜色映射
// ============================================================

const STEP_TYPE_CONFIG: Record<string, { icon: React.ElementType; color: string; bg: string; label: string }> = {
    trigger:   { icon: Clock,    color: 'text-green-600',  bg: 'bg-green-50 border-green-200',  label: '触发' },
    fetch:     { icon: Database, color: 'text-blue-600',   bg: 'bg-blue-50 border-blue-200',    label: '获取' },
    filter:    { icon: Filter,   color: 'text-amber-600',  bg: 'bg-amber-50 border-amber-200',  label: '筛选' },
    transform: { icon: Wand2,    color: 'text-purple-600', bg: 'bg-purple-50 border-purple-200', label: '转换' },
    ai:        { icon: Lightbulb,color: 'text-pink-600',   bg: 'bg-pink-50 border-pink-200',     label: 'AI' },
    action:    { icon: Zap,      color: 'text-indigo-600', bg: 'bg-indigo-50 border-indigo-200', label: '动作' },
};

// ============================================================
// 单个步骤卡片
// ============================================================

interface StepCardProps {
    step: ConceptStep;
    index: number;
    total: number;
    onDelete: (id: string) => void;
    onDragStart: (e: React.DragEvent, index: number) => void;
    onDragOver: (e: React.DragEvent) => void;
    onDrop: (e: React.DragEvent, index: number) => void;
    isDragging: boolean;
}

const StepCard: React.FC<StepCardProps> = ({
    step, index, total, onDelete,
    onDragStart, onDragOver, onDrop, isDragging
}) => {
    const config = STEP_TYPE_CONFIG[step.type] || STEP_TYPE_CONFIG['action'];
    const Icon = config.icon;

    return (
        <div
            draggable
            onDragStart={(e) => onDragStart(e, index)}
            onDragOver={onDragOver}
            onDrop={(e) => onDrop(e, index)}
            className={`flex items-center gap-3 p-3 rounded-lg border transition-all cursor-move
                ${config.bg}
                ${isDragging ? 'opacity-50 scale-95' : 'hover:shadow-md'}
            `}
        >
            {/* 拖拽手柄 */}
            <GripVertical className="w-4 h-4 text-slate-400 flex-shrink-0" />

            {/* 序号 */}
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold border ${config.color} bg-white flex-shrink-0`}>
                {index + 1}
            </div>

            {/* 图标 */}
            <Icon className={`w-5 h-5 ${config.color} flex-shrink-0`} />

            {/* 内容 */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-800 text-sm">{step.label}</span>
                    <span className={`text-xs px-1.5 py-0.5 rounded ${config.color} bg-white/80 border`}>
                        {config.label}
                    </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5 truncate">{step.description}</p>
            </div>

            {/* 删除按钮 */}
            {total > 1 && (
                <button
                    onClick={() => onDelete(step.id)}
                    className="p-1 text-slate-400 hover:text-red-500 transition-colors flex-shrink-0"
                    title="删除步骤"
                >
                    <Trash2 className="w-4 h-4" />
                </button>
            )}
        </div>
    );
};

// ============================================================
// 概念审核组件
// ============================================================

interface ConceptReviewProps {
    concept: ConceptResult;
    onConfirm: (steps: ConceptStep[]) => void;
    onRefine: (feedback: string, steps: ConceptStep[]) => void;
    isRefining: boolean;
    isConfirming: boolean;
}

export const ConceptReview: React.FC<ConceptReviewProps> = ({
    concept, onConfirm, onRefine, isRefining, isConfirming,
}) => {
    const [steps, setSteps] = useState<ConceptStep[]>(concept.steps);
    const [dragIndex, setDragIndex] = useState<number | null>(null);
    const [feedback, setFeedback] = useState('');
    const [showChat, setShowChat] = useState(false);

    // 拖拽相关
    const handleDragStart = (e: React.DragEvent, index: number) => {
        setDragIndex(index);
        e.dataTransfer.effectAllowed = 'move';
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    };

    const handleDrop = (e: React.DragEvent, dropIndex: number) => {
        e.preventDefault();
        if (dragIndex === null || dragIndex === dropIndex) return;

        const newSteps = [...steps];
        const [removed] = newSteps.splice(dragIndex, 1);
        newSteps.splice(dropIndex, 0, removed);
        setSteps(newSteps);
        setDragIndex(null);
    };

    const handleDelete = (id: string) => {
        setSteps(steps.filter(s => s.id !== id));
    };

    const handleRefine = () => {
        if (!feedback.trim()) return;
        onRefine(feedback, steps);
        setFeedback('');
    };

    const handleRefineKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleRefine();
        }
    };

    return (
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
            {/* 标题 */}
            <div className="bg-gradient-to-r from-emerald-50 to-blue-50 px-6 py-4 border-b border-slate-200">
                <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-amber-500" />
                    Phase 1: 逻辑步骤预览
                </h3>
                <p className="text-xs text-slate-500 mt-1">
                    拖拽卡片可调整顺序 · 点击垃圾桶删除 · 也可通过对话框修改思路
                </p>
            </div>

            <div className="p-6 space-y-4">
                {/* AI 思考过程 */}
                {concept.thinking && (
                    <div className="text-sm text-slate-600 bg-slate-50 p-3 rounded-md border border-slate-100 italic">
                        💡 {concept.thinking}
                    </div>
                )}

                {/* 步骤列表 (可拖拽) */}
                <div className="space-y-2">
                    {steps.map((step, index) => (
                        <StepCard
                            key={step.id}
                            step={step}
                            index={index}
                            total={steps.length}
                            onDelete={handleDelete}
                            onDragStart={handleDragStart}
                            onDragOver={handleDragOver}
                            onDrop={handleDrop}
                            isDragging={dragIndex === index}
                        />
                    ))}
                </div>

                {/* 对话式修改区 */}
                <div className="border-t border-slate-100 pt-4">
                    <button
                        onClick={() => setShowChat(!showChat)}
                        className="flex items-center gap-2 text-sm text-slate-500 hover:text-blue-600 transition-colors"
                    >
                        <MessageSquare className="w-4 h-4" />
                        {showChat ? '收起对话框' : '通过对话修改思路...'}
                    </button>

                    {showChat && (
                        <div className="mt-3 flex gap-2">
                            <input
                                type="text"
                                value={feedback}
                                onChange={(e) => setFeedback(e.target.value)}
                                onKeyDown={handleRefineKeyDown}
                                placeholder="例如：在筛选和发送之间增加一步 AI 总结..."
                                className="flex-1 text-sm border border-slate-300 rounded-lg px-3 py-2 outline-none focus:ring-2 focus:ring-blue-400"
                                disabled={isRefining}
                            />
                            <button
                                onClick={handleRefine}
                                disabled={!feedback.trim() || isRefining}
                                className="px-3 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                            >
                                {isRefining ? (
                                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                ) : (
                                    <SendIcon className="w-4 h-4" />
                                )}
                            </button>
                        </div>
                    )}
                </div>

                {/* 操作按钮 */}
                <div className="pt-2 flex justify-end">
                    <button
                        onClick={() => onConfirm(steps)}
                        disabled={isConfirming || steps.length === 0}
                        className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2.5 rounded-lg font-medium transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow-md"
                    >
                        {isConfirming ? (
                            <>
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                正在映射节点...
                            </>
                        ) : (
                            <>
                                <Check className="w-4 h-4" />
                                确认思路，开始选节点
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
};
