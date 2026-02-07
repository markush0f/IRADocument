import React from 'react';
import { Brain, Wrench, ArrowRight } from 'lucide-react';
import type { AgentThought } from '../types';

interface ThoughtConsoleProps {
    thoughts: AgentThought[];
}

export const ThoughtConsole: React.FC<ThoughtConsoleProps> = ({ thoughts }) => {
    const scrollRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [thoughts]);

    const getThoughtInfo = (thought: AgentThought) => {
        if (thought.subtype === 'llm_request') {
            const messages = thought.data.messages;
            const content = Array.isArray(messages) 
                ? messages[0]?.content 
                : messages?.content;
            
            return {
                icon: <Brain className="w-4 h-4" />,
                type: 'Pensando',
                message: content || 'Analizando...',
                color: 'text-blue-400 bg-blue-500/10 border-blue-500/20'
            };
        }

        if (thought.subtype === 'tool_calls') {
            const toolName = thought.data.calls[0]?.function?.name || 'Unknown';
            return {
                icon: <Wrench className="w-4 h-4" />,
                type: 'Ejecutando',
                message: `Herramienta: ${toolName}`,
                color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20'
            };
        }

        if (thought.subtype === 'llm_response') {
            const content = thought.data.content || 'Respuesta recibida';
            return {
                icon: <ArrowRight className="w-4 h-4" />,
                type: 'Respuesta',
                message: content,
                color: 'text-violet-400 bg-violet-500/10 border-violet-500/20'
            };
        }

        return {
            icon: <ArrowRight className="w-4 h-4" />,
            type: 'Info',
            message: JSON.stringify(thought.data),
            color: 'text-zinc-400 bg-zinc-500/10 border-zinc-500/20'
        };
    };

    // Only show last 8 thoughts to keep it compact
    const recentThoughts = thoughts.slice(-8);

    return (
        <div className="h-full flex flex-col bg-zinc-900/30 rounded-lg border border-zinc-800/50 overflow-hidden">
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto p-3 space-y-2"
            >
                {recentThoughts.length === 0 && (
                    <div className="h-full flex items-center justify-center text-zinc-600">
                        <p className="text-xs">Esperando actividad...</p>
                    </div>
                )}

                {recentThoughts.map((thought, idx) => {
                    const info = getThoughtInfo(thought);
                    return (
                        <div
                            key={thought.id}
                            className={`flex items-start gap-2 p-2 rounded-lg border transition-all duration-200 ${info.color}`}
                        >
                            <div className="flex-shrink-0 mt-0.5">
                                {info.icon}
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="text-xs font-semibold mb-0.5">
                                    {info.type}
                                </div>
                                <div className="text-xs text-zinc-300 line-clamp-2">
                                    {info.message}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};
