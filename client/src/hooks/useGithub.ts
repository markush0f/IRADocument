import { useState } from 'react';
import type { GithubRepo } from '../types';

export const useGithub = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const parseGithubUrl = (url: string) => {
        const regex = /github\.com\/([^/]+)\/([^/]+)/;
        const match = url.match(regex);
        if (match) {
            return { owner: match[1], repo: match[2].replace('.git', '') };
        }
        return null;
    };

    const fetchRepoDetails = async (owner: string, repo: string): Promise<GithubRepo | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await fetch(`https://api.github.com/repos/${owner}/${repo}`);
            if (!response.ok) throw new Error('Repository not found');
            const data = await response.json();
            return data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Error fetching repository');
            return null;
        } finally {
            setLoading(false);
        }
    };

    const fetchBranches = async (owner: string, repo: string): Promise<string[]> => {
        try {
            const response = await fetch(`https://api.github.com/repos/${owner}/${repo}/branches`);
            if (!response.ok) return [];
            const data = await response.json();
            return data.map((b: any) => b.name);
        } catch {
            return [];
        }
    };

    return {
        loading,
        error,
        parseGithubUrl,
        fetchRepoDetails,
        fetchBranches,
    };
};
