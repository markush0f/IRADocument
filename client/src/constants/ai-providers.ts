import type { AIProviderId, AIProvider } from '../types';

export const AI_PROVIDERS: Record<AIProviderId, AIProvider> = {
    openai: {
        name: 'OpenAI',
        models: [
            { id: 'gpt-4o-mini', name: 'GPT-4o Mini', recommended: true },
            { id: 'gpt-4o', name: 'GPT-4o' },
            { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
            { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' },
        ]
    },
    gemini: {
        name: 'Google Gemini',
        models: [
            { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash (Estable - Límite Alto)', recommended: true },
            { id: 'gemini-pro-latest', name: 'Gemini Pro Latest (Preview - Límite bajo)' },
            { id: 'gemini-flash-latest', name: 'Gemini Flash Latest (Experimental)' },
            { id: 'gemini-2.5-flash-lite', name: 'Gemini 2.5 Flash Lite' },
            { id: 'deep-research-pro-preview-12-2025', name: 'Deep Research Pro' },
        ]
    },
    ollama: {
        name: 'Ollama',
        models: [
            { id: 'llama2', name: 'Llama 2' },
            { id: 'codellama', name: 'Code Llama' },
            { id: 'mistral', name: 'Mistral' },
            { id: 'mixtral', name: 'Mixtral' },
        ]
    }
};
