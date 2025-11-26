import * as vscode from 'vscode';
import axios, { AxiosInstance } from 'axios';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
    TransportKind,
} from 'vscode-languageclient/node';

export interface ValidationResult {
    valid: boolean;
    errors: ValidationIssue[];
    warnings: ValidationIssue[];
    suggestions: string[];
}

export interface ValidationIssue {
    message: string;
    line?: number;
    column?: number;
    endLine?: number;
    endColumn?: number;
    severity: 'error' | 'warning' | 'info';
}

export interface ExplanationResult {
    explanation: string;
    complexity: string;
    tables: string[];
}

export interface PiiResult {
    hasPii: boolean;
    detections: PiiDetection[];
    anonymizedQuery?: string;
}

export interface PiiDetection {
    entityType: string;
    value: string;
    start: number;
    end: number;
    score: number;
}

export interface CompletionResult {
    completions: string[];
}

export class L0l1Client {
    private outputChannel: vscode.OutputChannel;
    private httpClient: AxiosInstance | null = null;
    private lspClient: LanguageClient | null = null;
    private mode: 'api' | 'tcp' | 'embedded' = 'api';

    constructor(outputChannel: vscode.OutputChannel) {
        this.outputChannel = outputChannel;
    }

    async start(): Promise<void> {
        const config = vscode.workspace.getConfiguration('l0l1');
        this.mode = config.get<'api' | 'tcp' | 'embedded'>('serverMode', 'api');

        this.outputChannel.appendLine(`Starting l0l1 client in ${this.mode} mode`);

        switch (this.mode) {
            case 'api':
                await this.startApiClient(config);
                break;
            case 'tcp':
                await this.startLspClient(config);
                break;
            case 'embedded':
                await this.startEmbeddedServer(config);
                break;
        }
    }

    private async startApiClient(config: vscode.WorkspaceConfiguration): Promise<void> {
        const apiUrl = config.get<string>('apiUrl', 'http://localhost:8000');

        this.httpClient = axios.create({
            baseURL: apiUrl,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
            },
        });

        // Test connection
        try {
            const response = await this.httpClient.get('/health');
            this.outputChannel.appendLine(`Connected to l0l1 API: ${JSON.stringify(response.data)}`);
        } catch (error) {
            throw new Error(`Cannot connect to l0l1 API at ${apiUrl}. Is the server running?`);
        }
    }

    private async startLspClient(config: vscode.WorkspaceConfiguration): Promise<void> {
        const host = config.get<string>('tcpHost', 'localhost');
        const port = config.get<number>('tcpPort', 9257);

        const serverOptions: ServerOptions = () => {
            return new Promise((resolve) => {
                const net = require('net');
                const socket = net.connect({ host, port });
                resolve({
                    reader: socket,
                    writer: socket,
                });
            });
        };

        const clientOptions: LanguageClientOptions = {
            documentSelector: [{ scheme: 'file', language: 'sql' }],
            outputChannel: this.outputChannel,
        };

        this.lspClient = new LanguageClient(
            'l0l1-lsp',
            'l0l1 Language Server',
            serverOptions,
            clientOptions
        );

        await this.lspClient.start();
        this.outputChannel.appendLine(`Connected to l0l1 LSP server at ${host}:${port}`);
    }

    private async startEmbeddedServer(config: vscode.WorkspaceConfiguration): Promise<void> {
        const pythonPath = config.get<string>('pythonPath', 'python');

        const serverOptions: ServerOptions = {
            command: pythonPath,
            args: ['-m', 'l0l1.integrations.ide.server'],
            transport: TransportKind.stdio,
        };

        const clientOptions: LanguageClientOptions = {
            documentSelector: [{ scheme: 'file', language: 'sql' }],
            outputChannel: this.outputChannel,
        };

        this.lspClient = new LanguageClient(
            'l0l1-lsp',
            'l0l1 Language Server',
            serverOptions,
            clientOptions
        );

        await this.lspClient.start();
        this.outputChannel.appendLine('Started embedded l0l1 LSP server');
    }

    async stop(): Promise<void> {
        if (this.lspClient) {
            await this.lspClient.stop();
            this.lspClient = null;
        }
        this.httpClient = null;
    }

    async restart(): Promise<void> {
        await this.stop();
        await this.start();
    }

    isConnected(): boolean {
        if (this.mode === 'api') {
            return this.httpClient !== null;
        }
        return this.lspClient !== null && this.lspClient.isRunning();
    }

    async validate(query: string, schemaContext?: string): Promise<ValidationResult> {
        const config = vscode.workspace.getConfiguration('l0l1');
        const workspace = config.get<string>('workspace', 'vscode');

        if (this.mode === 'api' && this.httpClient) {
            try {
                const response = await this.httpClient.post('/sql/validate', {
                    query,
                    workspace_id: workspace,
                    schema_context: schemaContext,
                });

                return {
                    valid: response.data.valid ?? true,
                    errors: (response.data.errors ?? []).map(this.mapIssue),
                    warnings: (response.data.warnings ?? []).map(this.mapIssue),
                    suggestions: response.data.suggestions ?? [],
                };
            } catch (error) {
                this.handleError('Validation failed', error);
                throw error;
            }
        }

        // For LSP mode, validation happens automatically via diagnostics
        return { valid: true, errors: [], warnings: [], suggestions: [] };
    }

    async explain(query: string): Promise<ExplanationResult> {
        const config = vscode.workspace.getConfiguration('l0l1');
        const workspace = config.get<string>('workspace', 'vscode');

        if (this.mode === 'api' && this.httpClient) {
            try {
                const response = await this.httpClient.post('/sql/explain', {
                    query,
                    workspace_id: workspace,
                });

                return {
                    explanation: response.data.explanation ?? '',
                    complexity: response.data.complexity ?? 'unknown',
                    tables: response.data.tables_accessed ?? [],
                };
            } catch (error) {
                this.handleError('Explanation failed', error);
                throw error;
            }
        }

        throw new Error('Explain not available in current mode');
    }

    async checkPii(query: string): Promise<PiiResult> {
        if (this.mode === 'api' && this.httpClient) {
            try {
                const response = await this.httpClient.post('/pii/detect', {
                    query,
                });

                return {
                    hasPii: response.data.has_pii ?? false,
                    detections: (response.data.detections ?? []).map((d: any) => ({
                        entityType: d.entity_type,
                        value: d.value,
                        start: d.start,
                        end: d.end,
                        score: d.score,
                    })),
                };
            } catch (error) {
                this.handleError('PII detection failed', error);
                throw error;
            }
        }

        throw new Error('PII detection not available in current mode');
    }

    async anonymize(query: string): Promise<PiiResult> {
        if (this.mode === 'api' && this.httpClient) {
            try {
                const response = await this.httpClient.post('/pii/anonymize', {
                    query,
                });

                return {
                    hasPii: true,
                    detections: (response.data.replacements ?? []).map((r: any) => ({
                        entityType: r.entity_type,
                        value: r.original,
                        start: 0,
                        end: 0,
                        score: 1.0,
                    })),
                    anonymizedQuery: response.data.anonymized_query,
                };
            } catch (error) {
                this.handleError('Anonymization failed', error);
                throw error;
            }
        }

        throw new Error('Anonymization not available in current mode');
    }

    async complete(partialQuery: string): Promise<CompletionResult> {
        const config = vscode.workspace.getConfiguration('l0l1');
        const workspace = config.get<string>('workspace', 'vscode');

        if (this.mode === 'api' && this.httpClient) {
            try {
                const response = await this.httpClient.post('/sql/complete', {
                    partial_query: partialQuery,
                    workspace_id: workspace,
                    limit: 5,
                });

                return {
                    completions: response.data.completions ?? [],
                };
            } catch (error) {
                this.handleError('Completion failed', error);
                throw error;
            }
        }

        return { completions: [] };
    }

    private mapIssue(issue: any): ValidationIssue {
        if (typeof issue === 'string') {
            return {
                message: issue,
                severity: 'warning',
            };
        }
        return {
            message: issue.message ?? issue,
            line: issue.line,
            column: issue.column,
            endLine: issue.end_line,
            endColumn: issue.end_column,
            severity: issue.severity ?? 'warning',
        };
    }

    private handleError(context: string, error: unknown): void {
        const message = error instanceof Error ? error.message : String(error);
        this.outputChannel.appendLine(`${context}: ${message}`);
    }
}
