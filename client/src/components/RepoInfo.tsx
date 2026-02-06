import React from 'react';
import { Star, GitFork, Eye, Code, GitBranch, CalendarBlank } from '@phosphor-icons/react';
import { useAnalysis } from '../context/AnalysisContext';

export const RepoInfo: React.FC = () => {
    const { repoDetails, selectedBranch } = useAnalysis();

    if (!repoDetails) return null;

    return (
        <div className="p-10 flex flex-col justify-center">
            {/* Header */}
            <div className="flex items-start gap-6 mb-8 pb-8 border-b border-zinc-800/50">
                <img
                    src={repoDetails.owner.avatar_url}
                    alt={repoDetails.owner.login}
                    className="w-16 h-16 rounded-xl border-2 border-zinc-700/50"
                />
                <div className="flex-1">
                    <h2 className="text-2xl font-extralight tracking-wide text-white mb-2">
                        {repoDetails.name}
                    </h2>
                    <p className="text-zinc-400 text-sm mb-2">
                        {repoDetails.owner.login}/{repoDetails.name}
                    </p>
                    {repoDetails.description && (
                        <p className="text-zinc-300 text-sm leading-relaxed">
                            {repoDetails.description}
                        </p>
                    )}
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-4 mb-8">
                <div className="bg-zinc-950/50 rounded-xl p-4 border border-zinc-800/30">
                    <div className="flex items-center gap-2 text-zinc-500 mb-1">
                        <Star className="w-3 h-3" />
                        <span className="text-xs uppercase tracking-wider">Stars</span>
                    </div>
                    <p className="text-xl font-light text-white">
                        {repoDetails.stargazers_count.toLocaleString()}
                    </p>
                </div>
                <div className="bg-zinc-950/50 rounded-xl p-4 border border-zinc-800/30">
                    <div className="flex items-center gap-2 text-zinc-500 mb-1">
                        <GitFork className="w-3 h-3" />
                        <span className="text-xs uppercase tracking-wider">Forks</span>
                    </div>
                    <p className="text-xl font-light text-white">
                        {repoDetails.forks_count.toLocaleString()}
                    </p>
                </div>
                <div className="bg-zinc-950/50 rounded-xl p-4 border border-zinc-800/30">
                    <div className="flex items-center gap-2 text-zinc-500 mb-1">
                        <Eye className="w-3 h-3" />
                        <span className="text-xs uppercase tracking-wider">Watchers</span>
                    </div>
                    <p className="text-xl font-light text-white">
                        {repoDetails.watchers_count.toLocaleString()}
                    </p>
                </div>
                <div className="bg-zinc-950/50 rounded-xl p-4 border border-zinc-800/30">
                    <div className="flex items-center gap-2 text-zinc-500 mb-1">
                        <Code className="w-3 h-3" />
                        <span className="text-xs uppercase tracking-wider">Language</span>
                    </div>
                    <p className="text-xl font-light text-white">
                        {repoDetails.language || 'N/A'}
                    </p>
                </div>
            </div>

            {/* Branch & Dates */}
            <div className="space-y-4">
                <div className="flex items-center justify-between py-3 px-4 bg-indigo-950/20 border border-indigo-900/30 rounded-lg">
                    <div className="flex items-center gap-2">
                        <GitBranch className="w-4 h-4 text-indigo-400" />
                        <span className="text-xs text-zinc-400">Branch</span>
                    </div>
                    <span className="font-mono text-white font-medium">{selectedBranch}</span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="flex items-center gap-3 py-3 px-4 bg-zinc-950/30 border border-zinc-800/30 rounded-lg">
                        <CalendarBlank className="w-3 h-3 text-zinc-500" />
                        <div>
                            <p className="text-xs text-zinc-500">Created</p>
                            <p className="text-sm text-zinc-300">
                                {new Date(repoDetails.created_at).toLocaleDateString()}
                            </p>
                        </div>
                    </div>
                    <div className="flex items-center gap-3 py-3 px-4 bg-zinc-950/30 border border-zinc-800/30 rounded-lg">
                        <CalendarBlank className="w-3 h-3 text-zinc-500" />
                        <div>
                            <p className="text-xs text-zinc-500">Updated</p>
                            <p className="text-sm text-zinc-300">
                                {new Date(repoDetails.updated_at).toLocaleDateString()}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
