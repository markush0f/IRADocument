// WebSocket Message Types
export type PipelineStage = 'idle' | 'started' | 'mining' | 'planning' | 'writing' | 'completed' | 'error';

export interface BaseSocketMessage {
    type: string;
}

// 1. Pipeline Stage Message
export interface PipelineStageMessage extends BaseSocketMessage {
    type: 'pipeline_stage';
    stage: PipelineStage;
    message: string;
}

// 2. Pipeline Progress Message
export interface PipelineProgressMessage extends BaseSocketMessage {
    type: 'pipeline_progress';
    stage: 'mining_files' | 'writing_page';
    current: number;
    total: number;
    page_label?: string;
    page_id?: string;
    message: string;
}

// 3. Plan Generation Message
export interface PlanItem {
    id: string;
    label: string;
    type: 'page' | 'category';
    children?: PlanItem[];
}

export interface PlanGeneratedMessage extends BaseSocketMessage {
    type: 'plan_generated';
    plan: {
        project_name: string;
        tree: PlanItem[];
    };
}

// 4. Agent Thoughts (Discriminated Union)
export interface BaseAgentThought extends BaseSocketMessage {
    type: 'agent_thought';
    timestamp: number;
    id: string;
}

export interface LLMRequestContent {
    messages: {
        role: string;
        content: string;
    } | {
        role: string;
        content: string;
    }[];
}

export interface LLMRequestThought extends BaseAgentThought {
    subtype: 'llm_request';
    data: LLMRequestContent;
}

export interface ToolCall {
    function: {
        name: string;
        arguments: string;
    };
}

export interface ToolCallThought extends BaseAgentThought {
    subtype: 'tool_calls';
    data: {
        calls: ToolCall[];
    };
}

export interface InternalThoughtContent {
    thought: string;
}

export interface InternalThought extends BaseAgentThought {
    subtype: 'thought';
    data: InternalThoughtContent;
}

export interface LLMResponseThought extends BaseAgentThought {
    subtype: 'llm_response';
    data: {
        content: string;
    };
}

export type AgentThought = LLMRequestThought | ToolCallThought | InternalThought | LLMResponseThought;

// Union of all possible socket messages
export type SocketMessage =
    | PipelineStageMessage
    | PipelineProgressMessage
    | PlanGeneratedMessage
    | AgentThought;

// Application State Types
export interface PipelineStatus {
    currentStage: PipelineStage;
    message: string;
    progress: {
        current: number;
        total: number;
        label?: string;
    };
    logs: AgentThought[];
}

// Domain Types
export interface GithubOwner {
    login: string;
    avatar_url: string;
}

export interface GithubRepo {
    name: string;
    owner: GithubOwner;
    description: string;
    stargazers_count: number;
    forks_count: number;
    watchers_count: number;
    language: string;
    created_at: string;
    updated_at: string;
    html_url: string;
}

export interface AIModel {
    id: string;
    name: string;
    recommended?: boolean;
}

export interface AIProvider {
    name: string;
    models: AIModel[];
}

export interface AnalysisOptions {
    endpoints: boolean;
    tree: boolean;
}

export type AIProviderId = 'openai' | 'ollama' | 'gemini';
