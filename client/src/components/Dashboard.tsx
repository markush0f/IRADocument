import React from 'react';
import { ArrowLeft, Sparkle } from '@phosphor-icons/react';
import { useAnalysis } from '../context/AnalysisContext';
import { AnalysisConfig } from './AnalysisConfig';
import { RepoInfo } from './RepoInfo';

export const Dashboard: React.FC = () => {
    const { resetAnalysis, selectedModel, startAnalysis } = useAnalysis();

    return (
        <div className="w-full max-w-7xl mx-auto p-8 animate-in fade-in slide-in-from-bottom-4 duration-150">
            <button
                onClick={resetAnalysis}
                className="mb-6 flex items-center gap-2 text-zinc-400 hover:text-white transition-colors duration-200 group"
            >
                <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
                <span className="text-sm">Back to selection</span>
            </button>

            <div className="relative bg-zinc-900/40 backdrop-blur-sm border border-zinc-800/50 rounded-2xl shadow-2xl overflow-hidden">
                <div className="grid grid-cols-1 lg:grid-cols-2 lg:divide-x divide-y lg:divide-y-0 divide-zinc-800/50">
                    <AnalysisConfig />
                    <RepoInfo />
                </div>

                {/* Start Analysis Button */}
                {selectedModel && (
                    <div className="p-8 border-t border-zinc-800/50 bg-zinc-950/20 animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <button
                            className="w-full flex items-center justify-center gap-3 py-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow-lg shadow-indigo-500/30 transition-all hover:scale-[1.01] active:scale-[0.99] group font-semibold text-lg tracking-wide"
                            onClick={startAnalysis}
                        >
                            <span>Empezar análisis</span>
                            <Sparkle className="w-5 h-5 group-hover:rotate-12 transition-transform shadow-sm" />
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};
