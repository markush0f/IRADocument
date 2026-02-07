import React, { createContext, useContext, useState, useEffect, useRef, type ReactNode } from 'react';
import type {
    GithubRepo,
    AnalysisOptions,
    AIProviderId,
    PipelineStage,
    AgentThought,
    PlanItem,
    SocketMessage
} from '../types';

const API_BASE_URL = ''; // Use empty string for relative paths (proxied)
// Calculate WS URL dynamically based on project_id
const getWsUrl = (projectId: string) => {
    const protocol = globalThis.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${globalThis.location.host}/ws/${projectId}`;
};

interface AnalysisState {
    repoDetails: GithubRepo | null;
    selectedBranch: string | null;
    analysisOptions: AnalysisOptions;
    selectedProvider: AIProviderId | null;
    selectedModel: string | null;
    showProjectInfo: boolean;
    isAnalyzing: boolean;

    // New Pipeline State
    pipelineStage: PipelineStage;
    pipelineMessage: string;
    pipelineProgress: { current: number; total: number; label?: string };
    generatedPlan: PlanItem[] | null;
    agentThoughts: AgentThought[];
}

interface AnalysisContextType extends AnalysisState {
    setRepoDetails: (repo: GithubRepo | null) => void;
    setSelectedBranch: (branch: string | null) => void;
    setAnalysisOptions: (options: AnalysisOptions | ((prev: AnalysisOptions) => AnalysisOptions)) => void;
    setSelectedProvider: (provider: AIProviderId | null) => void;
    setSelectedModel: (model: string | null) => void;
    setShowProjectInfo: (show: boolean) => void;

    startAnalysis: () => Promise<void>;
    stopAnalysis: () => void;
    resetAnalysis: () => void;

    // Pipeline update methods
    updateStage: (stage: PipelineStage, message: string) => void;
    updateProgress: (current: number, total: number, label?: string, message?: string) => void;
    setPlan: (plan: PlanItem[]) => void;
    addThought: (thought: AgentThought) => void;
}

const AnalysisContext = createContext<AnalysisContextType | undefined>(undefined);

export const AnalysisProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    // Config State
    const [repoDetails, setRepoDetails] = useState<GithubRepo | null>(null);
    const [selectedBranch, setSelectedBranch] = useState<string | null>(null);
    const [analysisOptions, setAnalysisOptions] = useState<AnalysisOptions>({
        endpoints: true,
        tree: true,
    });
    const [selectedProvider, setSelectedProvider] = useState<AIProviderId | null>(null);
    const [selectedModel, setSelectedModel] = useState<string | null>(null);
    const [showProjectInfo, setShowProjectInfo] = useState(false);

    // Pipeline State
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [pipelineStage, setPipelineStage] = useState<PipelineStage>('idle');
    const [pipelineMessage, setPipelineMessage] = useState('Esperando inicio...');
    const [pipelineProgress, setPipelineProgress] = useState<{ current: number; total: number; label?: string }>({ current: 0, total: 0 });
    const [generatedPlan, setGeneratedPlan] = useState<PlanItem[] | null>(null);
    const [agentThoughts, setAgentThoughts] = useState<AgentThought[]>([]);

    const wsRef = useRef<WebSocket | null>(null);

    // Effect to handle cleanup of WS on unmount or stop
    useEffect(() => {
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    const connectWebSocket = (projectId: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        console.log(`[Frontend] Connecting to WS: ${getWsUrl(projectId)}`);
        const ws = new WebSocket(getWsUrl(projectId));

        ws.onopen = () => {
            console.log('[Frontend] WS Connected');
        };

        ws.onmessage = (event) => {
            try {
                const msg: SocketMessage = JSON.parse(event.data);
                console.log('[Frontend] WS Received:', msg.type, msg);

                switch (msg.type) {
                    case 'pipeline_stage':
                        setPipelineStage(msg.stage);
                        setPipelineMessage(msg.message);
                        break;
                    case 'pipeline_progress':
                        setPipelineProgress({
                            current: msg.current,
                            total: msg.total,
                            label: msg.page_label
                        });
                        setPipelineMessage(msg.message);
                        break;
                    case 'plan_generated':
                        setGeneratedPlan(msg.plan.tree);
                        break;
                    case 'agent_thought':
                        setAgentThoughts(prev => [...prev, msg]);
                        break;
                }
            } catch (err) {
                console.error('Error parsing WS message:', err);
            }
        };

        ws.onerror = (err) => {
            console.error('WS Error:', err);
            setPipelineMessage('Error de conexión con el servidor');
            setPipelineStage('error');
        };

        ws.onclose = () => {
            console.log('WS Closed');
        };

        wsRef.current = ws;
    };

    const startAnalysis = async () => {
        console.log('[Frontend] Starting analysis...');
        setIsAnalyzing(true);
        setPipelineStage('started');
        setPipelineMessage('Conectando con el servidor...');
        setAgentThoughts([]);
        setGeneratedPlan(null);
        setPipelineProgress({ current: 0, total: 0 });

        try {
            const projectId = repoDetails?.name || 'simulation_demo';
            // 1. Ensure WebSocket is connected
            console.log(`[Frontend] Connecting WebSocket for project: ${projectId}`);
            connectWebSocket(projectId);

            // 2. Wait a bit for connection
            await new Promise(r => setTimeout(r, 1000));
            console.log('[Frontend] WebSocket ready check:', wsRef.current?.readyState);

            // 3. Trigger simulation via API
            console.log(`[Frontend] Triggering simulation via POST to ${API_BASE_URL}/simulate/documentation`);
            const response = await fetch(`${API_BASE_URL}/simulate/documentation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    project_id: repoDetails?.name || 'simulation_demo'
                }),
            });

            console.log('[Frontend] Simulation API Response Status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('[Frontend] Simulation API Error:', errorText);
                throw new Error(`Failed to start simulation: ${response.status} ${errorText}`);
            }
            console.log('[Frontend] Simulation started successfully');

        } catch (error) {
            console.error('Error starting analysis:', error);
            setPipelineStage('error');
            setPipelineMessage('No se pudo iniciar la simulación');
        }
    };

    const stopAnalysis = () => {
        setIsAnalyzing(false);
        setPipelineStage('idle');
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    };

    const resetAnalysis = () => {
        stopAnalysis();
        setShowProjectInfo(false);
        setSelectedBranch(null);
        setAnalysisOptions({ endpoints: true, tree: true });
        setSelectedProvider(null);
        setSelectedModel(null);
        setGeneratedPlan(null);
        setAgentThoughts([]);
    };

    const updateStage = (stage: PipelineStage, message: string) => {
        setPipelineStage(stage);
        setPipelineMessage(message);
    };

    const updateProgress = (current: number, total: number, label?: string, message?: string) => {
        setPipelineProgress({ current, total, label });
        if (message) setPipelineMessage(message);
    };

    const setPlan = (plan: PlanItem[]) => {
        setGeneratedPlan(plan);
    };

    const addThought = (thought: AgentThought) => {
        setAgentThoughts(prev => [...prev, thought]);
    };

    const value = {
        repoDetails,
        selectedBranch,
        analysisOptions,
        selectedProvider,
        selectedModel,
        showProjectInfo,
        isAnalyzing,
        pipelineStage,
        pipelineMessage,
        pipelineProgress,
        generatedPlan,
        agentThoughts,
        setRepoDetails,
        setSelectedBranch,
        setAnalysisOptions,
        setSelectedProvider,
        setSelectedModel,
        setShowProjectInfo,
        startAnalysis,
        stopAnalysis,
        resetAnalysis,
        updateStage,
        updateProgress,
        setPlan,
        addThought
    };

    return (
        <AnalysisContext.Provider value={value}>
            {children}
        </AnalysisContext.Provider>
    );
};

export const useAnalysis = () => {
    const context = useContext(AnalysisContext);
    if (context === undefined) {
        throw new Error('useAnalysis must be used within an AnalysisProvider');
    }
    return context;
};
