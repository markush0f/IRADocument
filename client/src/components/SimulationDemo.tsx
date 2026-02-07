import React, { useState, useEffect, useRef } from 'react';
import type {
    PipelineStage,
    AgentThought,
    PlanItem,
    SocketMessage,
} from '../types';
import { Play, X, CheckCircle2, Loader2 } from 'lucide-react';
import { ThoughtConsole } from './ThoughtConsole';

const API_BASE_URL = '';

const getWsUrl = (projectId: string): string => {
    const protocol = globalThis.location.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${globalThis.location.host}/ws/${projectId}`;
};

const SimulationDemo: React.FC = () => {
    const [projectId, setProjectId] = useState('simulation_demo');
    const [isRunning, setIsRunning] = useState(false);
    const [pipelineStage, setPipelineStage] = useState<PipelineStage>('idle');
    const [pipelineMessage, setPipelineMessage] = useState('Listo para comenzar');
    const [progress, setProgress] = useState({ current: 0, total: 0, label: '' });
    const [generatedPlan, setGeneratedPlan] = useState<PlanItem[] | null>(null);
    const [agentThoughts, setAgentThoughts] = useState<AgentThought[]>([]);
    const wsRef = useRef<WebSocket | null>(null);

    const connectWebSocket = (pid: string) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        console.log(`[SimDemo] Connecting to WS: ${getWsUrl(pid)}`);
        const ws = new WebSocket(getWsUrl(pid));

        ws.onopen = () => {
            console.log('[SimDemo] WS Connected');
        };

        ws.onmessage = (event) => {
            try {
                const msg: SocketMessage = JSON.parse(event.data);
                console.log('[SimDemo] WS Received:', msg.type, msg);

                switch (msg.type) {
                    case 'pipeline_stage':
                        setPipelineStage(msg.stage);
                        setPipelineMessage(msg.message);
                        break;
                    case 'pipeline_progress':
                        setProgress({
                            current: msg.current,
                            total: msg.total,
                            label: msg.page_label || '',
                        });
                        setPipelineMessage(msg.message);
                        break;
                    case 'plan_generated':
                        setGeneratedPlan(msg.plan.tree);
                        break;
                    case 'agent_thought':
                        setAgentThoughts((prev) => [...prev, msg]);
                        break;
                }
            } catch (err) {
                console.error('[SimDemo] Error parsing WS message:', err);
            }
        };

        ws.onerror = (err) => {
            console.error('[SimDemo] WS Error:', err);
            setPipelineMessage('Error de conexión con el servidor');
            setPipelineStage('error');
        };

        ws.onclose = () => {
            console.log('[SimDemo] WS Closed');
        };

        wsRef.current = ws;
    };

    const startSimulation = async () => {
        console.log('[SimDemo] Starting simulation...');
        setIsRunning(true);
        setPipelineStage('started');
        setPipelineMessage('Conectando con el servidor...');
        setAgentThoughts([]);
        setGeneratedPlan(null);
        setProgress({ current: 0, total: 0, label: '' });

        try {
            connectWebSocket(projectId);
            await new Promise((r) => setTimeout(r, 1000));

            console.log(`[SimDemo] Triggering simulation via POST to ${API_BASE_URL}/simulate/documentation`);
            const response = await fetch(`${API_BASE_URL}/simulate/documentation`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    project_id: projectId,
                }),
            });

            console.log('[SimDemo] Simulation API Response Status:', response.status);

            if (!response.ok) {
                const errorText = await response.text();
                console.error('[SimDemo] Simulation API Error:', errorText);
                throw new Error(`Failed to start simulation: ${response.status} ${errorText}`);
            }
            console.log('[SimDemo] Simulation started successfully');
        } catch (error) {
            console.error('[SimDemo] Error starting simulation:', error);
            setPipelineStage('error');
            setPipelineMessage('No se pudo iniciar la simulación');
        }
    };

    const stopSimulation = () => {
        setIsRunning(false);
        setPipelineStage('idle');
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    };

    useEffect(() => {
        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, []);

    useEffect(() => {
        if (pipelineStage === 'completed' || pipelineStage === 'error') {
            setIsRunning(false);
        }
    }, [pipelineStage]);

    const renderSidebar = (items: PlanItem[], depth = 0) => {
        return items.map((item) => (
            <div key={item.id} style={{ marginLeft: `${depth * 16}px` }} className="py-1">
                <div className="flex items-center gap-2">
                    {item.type === 'category' ? (
                        <span className="text-purple-400">📁</span>
                    ) : (
                        <span className="text-blue-400">📄</span>
                    )}
                    <span className="text-gray-200">{item.label}</span>
                </div>
                {item.children && renderSidebar(item.children, depth + 1)}
            </div>
        ));
    };

    const getStageIcon = () => {
        switch (pipelineStage) {
            case 'completed':
                return <CheckCircle2 className="w-6 h-6 text-green-400" />;
            case 'error':
                return <X className="w-6 h-6 text-red-400" />;
            case 'idle':
                return <Play className="w-6 h-6 text-gray-400" />;
            default:
                return <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />;
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-gray-900 p-8">
            <div className="max-w-7xl mx-auto">
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-white mb-2">
                        Simulación de Documentación
                    </h1>
                    <p className="text-gray-400">
                        Prueba el pipeline de generación de documentación en tiempo real
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Control Panel */}
                    <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
                        <h2 className="text-xl font-semibold text-white mb-4">Panel de Control</h2>

                        <div className="mb-4">
                            <label htmlFor="projectIdInput" className="block text-sm font-medium text-gray-300 mb-2">
                                Project ID
                            </label>
                            <input
                                id="projectIdInput"
                                type="text"
                                value={projectId}
                                onChange={(e) => setProjectId(e.target.value)}
                                disabled={isRunning}
                                className="w-full px-4 py-2 bg-gray-900/50 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
                                placeholder="Enter project ID"
                            />
                        </div>

                        <button
                            onClick={isRunning ? stopSimulation : startSimulation}
                            className={`w-full flex items-center justify-center gap-2 px-6 py-3 rounded-lg font-medium transition-all ${
                                isRunning
                                    ? 'bg-red-500 hover:bg-red-600'
                                    : 'bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600'
                            } text-white`}
                        >
                            {isRunning ? (
                                <>
                                    <X className="w-5 h-5" />
                                    Detener Simulación
                                </>
                            ) : (
                                <>
                                    <Play className="w-5 h-5" />
                                    Iniciar Simulación
                                </>
                            )}
                        </button>

                        {/* Status Display */}
                        <div className="mt-6 p-4 bg-gray-900/50 rounded-lg">
                            <div className="flex items-center gap-3 mb-3">
                                {getStageIcon()}
                                <div>
                                    <div className="text-sm text-gray-400">Estado</div>
                                    <div className="font-medium text-white capitalize">
                                        {pipelineStage}
                                    </div>
                                </div>
                            </div>
                            <p className="text-gray-300 text-sm">{pipelineMessage}</p>

                            {progress.total > 0 && (
                                <div className="mt-4">
                                    <div className="flex justify-between text-sm text-gray-400 mb-1">
                                        <span>{progress.label || 'Progreso'}</span>
                                        <span>
                                            {progress.current} / {progress.total}
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-700 rounded-full h-2">
                                        <div
                                            className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all duration-300"
                                            style={{
                                                width: `${(progress.current / progress.total) * 100}%`,
                                            }}
                                        />
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Sidebar Preview */}
                    <div className="bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
                        <h2 className="text-xl font-semibold text-white mb-4">
                            Vista Previa del Sidebar
                        </h2>
                        <div className="bg-gray-900/50 rounded-lg p-4 max-h-[400px] overflow-y-auto">
                            {generatedPlan ? (
                                renderSidebar(generatedPlan)
                            ) : (
                                <p className="text-gray-500 text-center py-8">
                                    El plan de documentación aparecerá aquí...
                                </p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Thought Console */}
                <div className="mt-6">
                    <ThoughtConsole thoughts={agentThoughts} />
                </div>
            </div>
        </div>
    );
};

export default SimulationDemo;
