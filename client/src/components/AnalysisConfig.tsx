import React, { useState } from 'react';
import { Sparkle, ShareNetwork, TreeView, MagnifyingGlass, Check } from '@phosphor-icons/react';
import { useAnalysis } from '../context/AnalysisContext';
import { AI_PROVIDERS } from '../constants/ai-providers';
import { cn } from '../utils/cn';
import type { AIProviderId } from '../types';

export const AnalysisConfig: React.FC = () => {
    const {
        analysisOptions, setAnalysisOptions,
        selectedProvider, setSelectedProvider,
        selectedModel, setSelectedModel
    } = useAnalysis();

    const [modelFilter, setModelFilter] = useState('');

    const toggleOption = (option: 'endpoints' | 'tree') => {
        setAnalysisOptions(prev => ({ ...prev, [option]: !prev[option] }));
    };

    const filteredModels = selectedProvider
        ? AI_PROVIDERS[selectedProvider].models.filter(model =>
            model.name.toLowerCase().includes(modelFilter.toLowerCase())
        )
        : [];

    return (
        <div className="p-10">
            <h3 className="text-2xl font-extralight tracking-wide text-white mb-8 flex items-center gap-3">
                <Sparkle className="w-6 h-6 text-indigo-400" />
                Configuración de Análisis
            </h3>

            {/* Analysis Options */}
            <div className="space-y-4 mb-8">
                <p className="text-xs text-zinc-500 uppercase tracking-widest mb-3">Opciones de Análisis</p>

                <label className={cn(
                    "flex items-center gap-4 p-4 rounded-xl border-2 cursor-pointer transition-all duration-200",
                    analysisOptions.endpoints
                        ? "bg-indigo-950/30 border-indigo-500/50"
                        : "bg-zinc-950/30 border-zinc-800/50 hover:border-zinc-700"
                )}>
                    <input
                        type="checkbox"
                        checked={analysisOptions.endpoints}
                        onChange={() => toggleOption('endpoints')}
                        className="sr-only"
                    />
                    <div className={cn(
                        "w-5 h-5 rounded border-2 flex items-center justify-center transition-colors",
                        analysisOptions.endpoints ? "bg-indigo-600 border-indigo-600" : "border-zinc-600"
                    )}>
                        {analysisOptions.endpoints && <Check className="w-3 h-3 text-white" />}
                    </div>
                    <ShareNetwork className="w-5 h-5 text-zinc-400" />
                    <span className="text-zinc-200">Endpoints</span>
                </label>

                <label className={cn(
                    "flex items-center gap-4 p-4 rounded-xl border-2 cursor-pointer transition-all duration-200",
                    analysisOptions.tree
                        ? "bg-indigo-950/30 border-indigo-500/50"
                        : "bg-zinc-950/30 border-zinc-800/50 hover:border-zinc-700"
                )}>
                    <input
                        type="checkbox"
                        checked={analysisOptions.tree}
                        onChange={() => toggleOption('tree')}
                        className="sr-only"
                    />
                    <div className={cn(
                        "w-5 h-5 rounded border-2 flex items-center justify-center transition-colors",
                        analysisOptions.tree ? "bg-indigo-600 border-indigo-600" : "border-zinc-600"
                    )}>
                        {analysisOptions.tree && <Check className="w-3 h-3 text-white" />}
                    </div>
                    <TreeView className="w-5 h-5 text-zinc-400" />
                    <span className="text-zinc-200">Tree</span>
                </label>
            </div>

            {/* AI Provider Selection */}
            <div className="space-y-4 mb-8">
                <p className="text-xs text-zinc-500 uppercase tracking-widest mb-3">Seleccionar Cliente</p>

                <div className="grid grid-cols-2 gap-3">
                    {(Object.keys(AI_PROVIDERS) as AIProviderId[]).map(providerId => (
                        <button
                            key={providerId}
                            onClick={() => {
                                setSelectedProvider(providerId);
                                setSelectedModel(null);
                            }}
                            className={cn(
                                "p-4 rounded-xl border-2 transition-all duration-200 text-left",
                                selectedProvider === providerId
                                    ? "bg-indigo-950/30 border-indigo-500/50"
                                    : "bg-zinc-950/30 border-zinc-800/50 hover:border-zinc-700"
                            )}
                        >
                            <p className="font-medium text-white">{AI_PROVIDERS[providerId].name}</p>
                        </button>
                    ))}
                </div>
            </div>

            {/* Model Selection */}
            {selectedProvider && (
                <div className="space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">
                    <p className="text-xs text-zinc-500 uppercase tracking-widest mb-3">Seleccionar Modelo</p>

                    <div className="relative">
                        <MagnifyingGlass className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                        <input
                            type="text"
                            value={modelFilter}
                            onChange={(e) => setModelFilter(e.target.value)}
                            placeholder="Filtrar modelos..."
                            className="w-full bg-zinc-950/50 border border-zinc-800 text-zinc-100 placeholder:text-zinc-600 rounded-lg py-2 pl-10 pr-4 text-sm outline-none focus:border-indigo-500/50"
                        />
                    </div>

                    <div className="space-y-2 max-h-48 overflow-y-auto custom-scrollbar">
                        {filteredModels.map((model) => (
                            <button
                                key={model.id}
                                onClick={() => setSelectedModel(model.id)}
                                className={cn(
                                    "w-full flex items-center justify-between p-3 rounded-lg border transition-all duration-200",
                                    selectedModel === model.id
                                        ? "bg-indigo-600 border-indigo-500 text-white"
                                        : "bg-zinc-950/30 border-zinc-800/50 text-zinc-300 hover:border-zinc-700"
                                )}
                            >
                                <span className="text-sm">{model.name}</span>
                                {model.recommended && (
                                    <span className="text-xs px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded-full border border-emerald-500/30">
                                        Recomendado
                                    </span>
                                )}
                            </button>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
