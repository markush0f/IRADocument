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
            { id: 'gemini-2.0-flash-lite', name: 'Gemini 2.0 Flash Lite', recommended: true },
            { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash' },
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
