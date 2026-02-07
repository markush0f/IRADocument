import React from 'react';
import type {
    PipelineStage,
    PlanItem,
    AgentThought
} from '../types';
import { useAnalysis } from '../context/AnalysisContext';
import { 
    Brain, 
    Wrench, 
    ArrowRight, 
    BookOpen, 
    Search, 
    FolderTree, 
    PenTool, 
    CircleCheck, 
    CircleX, 
    Hammer, 
    FileText 
} from 'lucide-react';

interface PhaseInfo {
    id: PipelineStage;
    icon: React.ReactNode;
    title: string;
    description: string;
    color: string;
    activeColor: string;
}

const PHASES: PhaseInfo[] = [
    {
        id: 'mining',
        title: 'Miner',
        icon: <Search className="w-5 h-5" />,
        color: 'border-cyan-500/30 text-cyan-500',
        activeColor: 'border-cyan-500 bg-cyan-500/10 text-cyan-400',
        description: 'Extrayendo información del código'
    },
    {
        id: 'planning',
        title: 'Architect',
        icon: <FolderTree className="w-5 h-5" />,
        color: 'border-violet-500/30 text-violet-500',
        activeColor: 'border-violet-500 bg-violet-500/10 text-violet-400',
        description: 'Diseñando la estructura'
    },
    {
        id: 'writing',
        title: 'Scribe',
        icon: <PenTool className="w-5 h-5" />,
        color: 'border-fuchsia-500/30 text-fuchsia-500',
        activeColor: 'border-fuchsia-500 bg-fuchsia-500/10 text-fuchsia-400',
        description: 'Escribiendo documentación'
    }
];

const PlanTree: React.FC<{ items: PlanItem[], depth?: number }> = ({ items, depth = 0 }) => (
    <ul className={depth > 0 ? "ml-4 mt-2 space-y-1" : "space-y-1"}>
        {items.map((item) => (
            <li key={item.id} className="group">
                <div className="flex items-center gap-2 py-2 px-3 hover:bg-zinc-800/50 rounded-lg transition-all duration-200">
                    {item.type === 'category' ? (
                        <Hammer className="w-4 h-4 text-amber-400 flex-shrink-0" />
                    ) : (
                        <FileText className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                    )}
                    <span className={`text-sm ${item.type === 'category' ? 'font-semibold text-zinc-100' : 'text-zinc-300'}`}>
                        {item.label}
                    </span>
                </div>
                {item.children && item.children.length > 0 && (
                    <PlanTree items={item.children} depth={depth + 1} />
                )}
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
        agentThoughts
    } = useAnalysis();

    const getCurrentPhaseIndex = () => {
        const index = PHASES.findIndex(p => p.id === pipelineStage);
        return index !== -1 ? index : -1;
    };

    const isPhaseActive = (phase: PhaseInfo) => phase.id === pipelineStage;
    const isPhaseCompleted = (phase: PhaseInfo) => {
        const currentIndex = getCurrentPhaseIndex();
        const phaseIndex = PHASES.findIndex(p => p.id === phase.id);
        return currentIndex > phaseIndex || pipelineStage === 'completed';
    };

    const getPhaseStatus = (phase: PhaseInfo) => {
        if (isPhaseActive(phase)) return 'active';
        if (isPhaseCompleted(phase)) return 'completed';
        return 'pending';
    };

    const getThoughtInfo = (thought: AgentThought) => {
        if (thought.subtype === 'llm_request') {
            const messages = thought.data.messages;
            const content = Array.isArray(messages) 
                ? messages[0]?.content 
                : messages?.content;
            
            return {
                icon: <Brain className="w-3 h-3" />,
                message: content || 'Analizando...'
            };
        }

        if (thought.subtype === 'tool_calls') {
            const toolName = thought.data.calls[0]?.function?.name || 'Unknown';
            return {
                icon: <Wrench className="w-3 h-3" />,
                message: toolName
            };
        }

        if (thought.subtype === 'llm_response') {
            return {
                icon: <ArrowRight className="w-3 h-3" />,
                message: thought.data.content || 'OK'
            };
        }

        return {
            icon: <ArrowRight className="w-3 h-3" />,
            message: 'Procesando...'
        };
    };

    return (
        <div className="fixed inset-0 z-50 w-full h-screen bg-zinc-950 flex flex-col overflow-hidden">
            {/* Compact Header */}
            <div className="flex-shrink-0 border-b border-zinc-800 bg-zinc-900/80 px-6 py-3">
                <div className="flex items-center justify-between">
                    {/* Logo - Hidden during analysis */}
                    {['idle', 'completed', 'error'].includes(pipelineStage) ? (
                        <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-violet-500/10 rounded-lg flex items-center justify-center border border-violet-500/20">
                                <BookOpen className="w-4 h-4 text-violet-400" />
                            </div>
                            <div>
                                <h1 className="text-sm font-medium text-white">Generando Docs</h1>
                                <p className="text-[10px] text-zinc-500">Pipeline IA</p>
                            </div>
                        </div>
                    ) : <div />}
                    
                    {/* Compact Phase Indicators */}
                    <div className="flex items-center gap-2">
                        {PHASES.map((phase, index) => {
                            const status = getPhaseStatus(phase);
                            const isActive = status === 'active';
                            const isCompleted = status === 'completed';
                            
                            return (
                                <React.Fragment key={phase.id}>
                                    <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border ${
                                        isActive ? 'border-violet-500 bg-violet-500/10 text-violet-400' 
                                        : isCompleted ? 'border-emerald-500/30 text-emerald-400' 
                                        : 'border-zinc-700 text-zinc-500'
                                    }`}>
                                        {isCompleted ? <CircleCheck className="w-4 h-4" /> : phase.icon}
                                        <span className="text-xs font-medium">{phase.title}</span>
                                        {isActive && <div className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />}
                                    </div>
                                    {index < PHASES.length - 1 && (
                                        <div className={`w-4 h-px ${isCompleted ? 'bg-emerald-500' : 'bg-zinc-700'}`} />
                                    )}
                                </React.Fragment>
                            );
                        })}
                    </div>

                    <button
                        onClick={stopAnalysis}
                        className="px-3 py-1.5 text-sm bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 flex items-center gap-1.5"
                    >
                        <CircleX className="w-4 h-4" />
                        Detener
                    </button>
                </div>
                
                {pipelineProgress.total > 0 && (
                    <div className="mt-4 flex items-center gap-4">
                        <div className="flex flex-col min-w-[100px]">
                            <span className="text-[10px] uppercase tracking-wider text-zinc-500 font-semibold">Progreso</span>
                            <span className="text-sm font-mono text-zinc-300">
                                {pipelineProgress.current} <span className="text-zinc-600">/</span> {pipelineProgress.total} <span className="text-xs text-zinc-500 ml-1">páginas</span>
                            </span>
                        </div>
                        
                        <div className="flex-1 space-y-1.5">
                            <div className="flex justify-between text-xs">
                                <span className="text-zinc-400">{pipelineMessage}</span>
                                <span className="text-violet-400 font-medium">{Math.round((pipelineProgress.current / pipelineProgress.total) * 100)}%</span>
                            </div>
                            <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-violet-600 to-indigo-500 rounded-full transition-all duration-500 ease-out"
                                    style={{ width: `${(pipelineProgress.current / pipelineProgress.total) * 100}%` }}
                                />
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Main Layout: Sidebar + Content */}
            <div className="flex-1 flex overflow-hidden">
                
                {/* LEFT SIDEBAR: Documentation Structure */}
                <div className="w-80 flex-shrink-0 border-r border-zinc-800 bg-zinc-900/50 flex flex-col overflow-hidden">
                    <div className="h-16 flex items-center px-4 border-b border-zinc-800">
                        <div className="flex items-center gap-2">
                            <FolderTree className="w-5 h-5 text-violet-400" />
                            <h2 className="text-sm font-semibold text-white">Estructura</h2>
                        </div>
                    </div>
                    
                    <div className="flex-1 overflow-y-auto p-4">
                        {generatedPlan ? (
                            <div className="space-y-1">
                                {generatedPlan.map((item) => (
                                    <TreeItem key={item.id} item={item} depth={0} />
                                ))}
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center h-full text-center">
                                <div className="w-12 h-12 border-2 border-zinc-700 border-t-violet-500 rounded-full animate-spin mb-4" />
                                <p className="text-sm text-zinc-500">Esperando estructura...</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* MAIN CONTENT: Agent Activity (BIG) */}
                <div className="flex-1 flex flex-col overflow-hidden bg-zinc-950">
                    <div className="h-16 flex items-center justify-between px-6 border-b border-zinc-800 bg-zinc-900/30">
                        <div className="flex items-center gap-3">
                            <div className="w-3 h-3 rounded-full bg-sky-400 animate-pulse" />
                            <h2 className="text-lg font-semibold text-white">Actividad de IA</h2>
                        </div>
                        <span className="text-sm text-zinc-400 font-mono">{agentThoughts.length} eventos</span>
                    </div>
                    
                    <div className="flex-1 overflow-y-auto p-6 space-y-3">
                        {agentThoughts.length === 0 ? (
                            <div className="h-full flex flex-col items-center justify-center text-center">
                                <Brain className="w-16 h-16 text-zinc-700 mb-4" />
                                <p className="text-xl text-zinc-500 font-medium">Esperando actividad...</p>
                                <p className="text-sm text-zinc-600 mt-2">Los pensamientos del agente aparecerán aquí</p>
                            </div>
                        ) : (
                            agentThoughts.map((thought) => {
                                const info = getThoughtInfo(thought);
                                return (
                                    <div
                                        key={thought.id}
                                        className="flex items-start gap-4 p-4 bg-zinc-900/50 border border-zinc-800 rounded-xl hover:bg-zinc-900/80 transition-colors"
                                    >
                                        <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
                                            {info.icon}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-base text-zinc-200 leading-relaxed">
                                                {info.message}
                                            </p>
                                            <p className="text-xs text-zinc-600 mt-1">
                                                {new Date(thought.timestamp).toLocaleTimeString()}
                                            </p>
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>
            </div>

            {/* Completion State */}
            {pipelineStage === 'completed' && (
                <div className="absolute inset-0 bg-zinc-950/90 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="text-center p-12 bg-zinc-900 border border-emerald-500/30 rounded-2xl">
                        <CircleCheck className="w-16 h-16 text-emerald-400 mx-auto mb-4" />
                        <h3 className="text-2xl font-bold text-white mb-2">¡Completado!</h3>
                        <button onClick={stopAnalysis} className="mt-4 px-6 py-3 bg-emerald-500 text-white rounded-lg">
                            Volver
                        </button>
                    </div>
                </div>
            )}

            {/* Error State */}
            {pipelineStage === 'error' && (
                <div className="absolute inset-0 bg-zinc-950/90 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="text-center p-12 bg-zinc-900 border border-red-500/30 rounded-2xl">
                        <CircleX className="w-16 h-16 text-red-400 mx-auto mb-4" />
                        <h3 className="text-2xl font-bold text-white mb-2">Error</h3>
                        <p className="text-zinc-400">{pipelineMessage}</p>
                        <button onClick={stopAnalysis} className="mt-4 px-6 py-3 bg-red-500 text-white rounded-lg">
                            Cerrar
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

// Tree item component for sidebar
const TreeItem: React.FC<{ item: PlanItem; depth: number }> = ({ item, depth }) => {
    const isCategory = item.type === 'category';
    
    return (
        <div style={{ marginLeft: depth * 16 }}>
            <div className={`flex items-center gap-2 py-2 px-3 rounded-lg text-sm ${
                isCategory ? 'text-zinc-200 font-medium' : 'text-zinc-400 hover:bg-zinc-800/50'
            }`}>
                {isCategory ? (
                    <Hammer className="w-4 h-4 text-amber-400 flex-shrink-0" />
                ) : (
                    <FileText className="w-4 h-4 text-indigo-400 flex-shrink-0" />
                )}
                <span className="truncate">{item.label}</span>
            </div>
            {item.children && item.children.length > 0 && (
                <div className="space-y-0.5">
                    {item.children.map((child) => (
                        <TreeItem key={child.id} item={child} depth={depth + 1} />
                    ))}
                </div>
            )}
        </div>
    );
};
