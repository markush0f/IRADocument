import React, { useEffect } from 'react';
import type {
    PipelineStage,
    AgentThought,
    PlanItem
} from '../types';
import { useAnalysis } from '../context/AnalysisContext';
import { ThoughtConsole } from './ThoughtConsole';
import {
    ArrowsLeftRight,
    Brain,
    List,
    CheckCircle,
    XCircle,
    Warning,
    Lightning
} from '@phosphor-icons/react';

const pipelineStageColors: Record<PipelineStage, string> = {
    idle: 'bg-zinc-800',
    started: 'bg-indigo-600',
    mining: 'bg-sky-600',
    planning: 'bg-violet-600',
    writing: 'bg-fuchsia-600',
    completed: 'bg-emerald-600',
    error: 'bg-red-600',
};

const PlanTree: React.FC<{ items: PlanItem[] }> = ({ items }) => (
    <ul className="pl-4 border-l-2 border-zinc-800 ml-2 space-y-2 text-sm">
        {items.map((item) => (
            <li key={item.id} className="group">
                <div className="flex items-center gap-2 py-1 hover:bg-zinc-800/50 rounded px-2 transition-colors">
                    {item.type === 'category' ? (
                        <List className="w-4 h-4 text-amber-400 group-hover:scale-110 transition-transform" />
                    ) : (
                        <div className="w-2 h-2 rounded bg-indigo-500/50 group-hover:bg-indigo-400" />
                    )}
                    <span className={item.type === 'category' ? 'font-medium text-zinc-200' : 'text-zinc-400'}>
                        {item.label}
                    </span>
                </div>
                {item.children && <PlanTree items={item.children} />}
            </li>
        ))}
    </ul>
);

export const AnalysisView: React.FC = () => {
    const {
        stopAnalysis,
        pipelineStage,
        pipelineMessage,
        pipelineProgress,
        generatedPlan,
        agentThoughts,
        updateStage,
        updateProgress,
        setPlan,
        addThought
    } = useAnalysis();


    return (
        <div className="w-full h-screen bg-zinc-950 flex flex-col overflow-hidden font-sans">
            {/* Top Bar - Status & Progress */}
            <div className="h-20 bg-zinc-900 border-b border-zinc-800 flex items-center px-8 justify-between shadow-xl z-10">
                <div className="flex items-center gap-6">
                    <div className={`w-3 h-3 rounded-full animate-pulse ${pipelineStageColors[pipelineStage]}`} />
                    <div>
                        <h2 className="text-lg font-light text-white tracking-wide">
                            {pipelineMessage}
                        </h2>
                        <div className="flex items-center gap-2 text-xs text-zinc-500 mt-1">
                            <span className="uppercase tracking-widest font-mono">
                                Phase: {pipelineStage}
                            </span>
                            {pipelineProgress.total > 0 && (
                                <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono">
                                    {pipelineProgress.current}/{pipelineProgress.total}
                                </span>
                            )}
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-4 w-1/3">
                    {pipelineProgress.total > 0 && (
                        <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                            <div
                                className="bg-indigo-500 h-full transition-all duration-500 ease-out"
                                style={{ width: `${(pipelineProgress.current / pipelineProgress.total) * 100}%` }}
                            />
                        </div>
                    )}
                    <button
                        onClick={stopAnalysis}
                        className="p-2 hover:bg-zinc-800 rounded-lg text-zinc-500 hover:text-red-400 transition-colors"
                    >
                        <XCircle className="w-6 h-6" />
                    </button>
                </div>
            </div>

            {/* Main Content Areas */}
            <div className="flex-1 flex overflow-hidden">
                {/* Left: Plan Sidebar */}
                <div className="w-80 border-r border-zinc-800/50 bg-zinc-900/20 p-6 overflow-y-auto">
                    <h3 className="text-xs font-mono uppercase tracking-widest text-zinc-500 mb-6 flex items-center gap-2">
                        <List className="w-4 h-4" />
                        Documentation Plan
                    </h3>

                    {generatedPlan ? (
                        <div className="animate-in fade-in slide-in-from-left-4 duration-500">
                            <PlanTree items={generatedPlan} />
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-40 text-zinc-700 space-y-2">
                            <div className="w-8 h-8 border-2 border-zinc-800 border-t-zinc-600 rounded-full animate-spin" />
                            <span className="text-xs">Generating plan...</span>
                        </div>
                    )}
                </div>

                {/* Center: Agent Thoughts (Matrix Console) */}
                <div className="flex-1 bg-black/50 p-6 relative">
                    <div className="absolute inset-0 bg-[radial-gradient(#1e1e2e_1px,transparent_1px)] [background-size:20px_20px] opacity-10 pointer-events-none" />
                    <ThoughtConsole thoughts={agentThoughts} />
                </div>
            </div>
        </div>
    );
};
