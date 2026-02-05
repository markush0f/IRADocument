import type { AIProviderId, AIProvider } from '../types';

export const AI_PROVIDERS: Record<AIProviderId, AIProvider> = {
    openai: {
        name: 'OpenAI',
        models: [
            { id: 'gpt-4', name: 'GPT-4', recommended: true },
            { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
            { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' },
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
