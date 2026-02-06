import React, { useState, useEffect } from 'react';
import { GithubLogo, GitBranch, ArrowRight, SpinnerGap } from '@phosphor-icons/react';
import { useAnalysis } from '../context/AnalysisContext';
import { useGithub } from '../hooks/useGithub';
import { cn } from '../utils/cn';

export const SelectionScreen: React.FC = () => {
    const { setRepoDetails, setSelectedBranch, setShowProjectInfo } = useAnalysis();
    const { parseGithubUrl, fetchRepoDetails, fetchBranches, loading, error: githubError } = useGithub();

    const [url, setUrl] = useState('');
    const [branches, setBranches] = useState<string[]>([]);
    const [isFetchingBranches, setIsFetchingBranches] = useState(false);

    useEffect(() => {
        const repoInfo = parseGithubUrl(url);
        if (repoInfo) {
            const getBranches = async () => {
                setIsFetchingBranches(true);
                const branchList = await fetchBranches(repoInfo.owner, repoInfo.repo);
                setBranches(branchList);
                setIsFetchingBranches(false);
            };
            getBranches();
        } else {
            setBranches([]);
        }
    }, [url]);

    const handleSelectBranch = async (branch: string) => {
        const repoInfo = parseGithubUrl(url);
        if (repoInfo) {
            const details = await fetchRepoDetails(repoInfo.owner, repoInfo.repo);
            if (details) {
                setRepoDetails(details);
                setSelectedBranch(branch);
                setShowProjectInfo(true);
            }
        }
    };

    return (
        <div className="w-full max-w-md mx-auto p-6">
            <div className="flex flex-col gap-6">
                <div className="text-center space-y-2">
                    <div className="inline-flex items-center justify-center p-3 rounded-full bg-zinc-900 border border-zinc-800 mb-4 shadow-xl shadow-black/50">
                        <GithubLogo className="w-6 h-6 text-white" />
                    </div>
                    <h1 className="text-2xl font-light tracking-tight text-white">
                        Git Explorer
                    </h1>
                    <p className="text-zinc-500 text-sm">
                        Ingresa un repositorio para comenzar el análisis
                    </p>
                </div>

                <div className="relative group">
                    <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                        <GithubLogo className="w-5 h-5 text-zinc-500 group-focus-within:text-white transition-colors" />
                    </div>
                    <input
                        type="text"
                        placeholder="https://github.com/..."
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        className="w-full bg-zinc-900/50 border border-zinc-800 text-white rounded-xl py-4 pl-12 pr-4 outline-none focus:ring-1 focus:ring-white/20 focus:border-white/20 transition-all placeholder:text-zinc-600"
                    />
                </div>

                {githubError && (
                    <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs text-center animate-in fade-in zoom-in-95 duration-200">
                        {githubError}
                    </div>
                )}

                {branches.length > 0 && (
                    <div className="space-y-3 animate-in fade-in slide-in-from-top-4 duration-300">
                        <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-500 font-medium px-1">
                            Seleccionar Rama
                        </p>
                        <div className="grid gap-2">
                            {branches.slice(0, 5).map((branch) => (
                                <button
                                    key={branch}
                                    onClick={() => handleSelectBranch(branch)}
                                    disabled={loading}
                                    className="group flex items-center justify-between p-4 rounded-xl bg-zinc-900/40 border border-zinc-800 hover:border-zinc-700 hover:bg-zinc-800/40 transition-all duration-200 text-left"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 group-hover:bg-indigo-500 group-hover:text-white transition-colors duration-200">
                                            <GitBranch className="w-4 h-4" />
                                        </div>
                                        <span className="text-sm text-zinc-300 group-hover:text-white font-medium transition-colors">
                                            {branch}
                                        </span>
                                    </div>
                                    <ArrowRight className="w-4 h-4 text-zinc-600 group-hover:text-white translate-x-0 group-hover:translate-x-1 transition-all" />
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {(loading || isFetchingBranches) && (
                    <div className="flex justify-center py-4">
                        <SpinnerGap className="w-6 h-6 text-zinc-500 animate-spin" />
                    </div>
                )}
            </div>
        </div>
    );
};
