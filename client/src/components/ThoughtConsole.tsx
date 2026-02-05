import React from 'react';
import {
    Clock,
    Brain,
    Code,
    Database,
    Browser,
    Function,
    ArrowsLeftRight,
    Terminal,
    Cpu
} from '@phosphor-icons/react';
import type { AgentThought } from '../types';
import { cn } from '../utils/cn';

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

    const renderThoughtContent = (thought: AgentThought) => {
        if (thought.subtype === 'llm_request') {
            return (
                <div className="space-y-2 font-mono text-xs">
                    <div className="flex items-center gap-2 text-indigo-400">
                        <Brain className="w-4 h-4" />
                        <span className="font-bold">LLM REQUEST</span>
                    </div>
                    <div className="pl-6 border-l-2 border-indigo-500/30 text-zinc-300">
                        {JSON.stringify(thought.data, null, 2)}
                    </div>
                </div>
            );
        }

        if (thought.subtype === 'tool_calls') {
            return (
                <div className="space-y-2 font-mono text-xs">
                    <div className="flex items-center gap-2 text-emerald-400">
                        <Function className="w-4 h-4" />
                        <span className="font-bold">TOOL EXECUTION</span>
                    </div>
                    {thought.data.calls.map((call, idx) => (
                        <div key={idx} className="pl-6 border-l-2 border-emerald-500/30">
                            <span className="text-emerald-300">{call.function.name}</span>
                            <pre className="mt-1 text-zinc-400 overflow-x-auto">
                                {JSON.stringify(JSON.parse(call.function.arguments), null, 2)}
                            </pre>
                        </div>
                    ))}
                </div>
            );
        }

        return (
            <div className="flex items-center gap-2 text-zinc-300 font-mono text-xs">
                <Terminal className="w-4 h-4 text-zinc-500" />
                <span>{JSON.stringify(thought.data)}</span>
            </div>
        );
    };

    return (
        <div className="bg-black/90 rounded-xl border border-zinc-800/50 flex flex-col h-full overflow-hidden shadow-2xl">
            <div className="flex items-center justify-between px-4 py-3 bg-zinc-900/50 border-b border-zinc-800/50">
                <div className="flex items-center gap-2 text-zinc-400">
                    <Cpu className="w-4 h-4" />
                    <span className="text-xs font-mono uppercase tracking-wider">Agent Matrix Console</span>
                </div>
                <div className="flex gap-1.5">
                    <div className="w-2.5 h-2.5 rounded-full bg-red-500/20 border border-red-500/50" />
                    <div className="w-2.5 h-2.5 rounded-full bg-amber-500/20 border border-amber-500/50" />
                    <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/20 border border-emerald-500/50" />
                </div>
            </div>

            <div
                ref={scrollRef}
                className="flex-1 p-4 overflow-y-auto custom-scrollbar space-y-4 font-mono"
            >
                {thoughts.length === 0 && (
                    <div className="h-full flex flex-col items-center justify-center text-zinc-600 space-y-2">
                        <Terminal className="w-8 h-8 opacity-20" />
                        <p className="text-xs uppercase tracking-widest opacity-50">System Standby</p>
                    </div>
                )}

                {thoughts.map((thought, idx) => (
                    <div
                        key={idx}
                        className="animate-in fade-in slide-in-from-left-2 duration-300"
                    >
                        <div className="flex items-center gap-2 mb-1 opacity-50">
                            <Clock className="w-3 h-3 text-zinc-500" />
                            <span className="text-[10px] text-zinc-500">
                                {new Date(thought.timestamp).toLocaleTimeString()}
                            </span>
                        </div>
                        {renderThoughtContent(thought)}
                    </div>
                ))}
            </div>
        </div>
    );
};
