import * as vscode from 'vscode';
import { L0l1Client } from './client';
import { registerCommands } from './commands';
import { StatusBar } from './statusBar';
import { DiagnosticsProvider } from './diagnostics';

let client: L0l1Client;
let statusBar: StatusBar;
let diagnosticsProvider: DiagnosticsProvider;

export async function activate(context: vscode.ExtensionContext): Promise<void> {
    const outputChannel = vscode.window.createOutputChannel('l0l1 SQL');
    outputChannel.appendLine('l0l1 SQL extension activating...');

    // Initialize status bar
    statusBar = new StatusBar();
    context.subscriptions.push(statusBar);

    // Initialize client
    client = new L0l1Client(outputChannel);

    // Initialize diagnostics provider
    diagnosticsProvider = new DiagnosticsProvider(client);
    context.subscriptions.push(diagnosticsProvider);

    // Register commands
    registerCommands(context, client, statusBar, outputChannel);

    // Start client based on configuration
    const config = vscode.workspace.getConfiguration('l0l1');
    if (config.get<boolean>('enable', true)) {
        try {
            await client.start();
            statusBar.setConnected(true);
            outputChannel.appendLine('l0l1 client started successfully');
        } catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            outputChannel.appendLine(`Failed to start l0l1 client: ${message}`);
            statusBar.setConnected(false);
            vscode.window.showWarningMessage(
                `l0l1: Failed to connect to server. ${message}`
            );
        }
    }

    // Watch for configuration changes
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration(async (e) => {
            if (e.affectsConfiguration('l0l1')) {
                outputChannel.appendLine('Configuration changed, restarting client...');
                await client.restart();
            }
        })
    );

    // Set up document listeners
    setupDocumentListeners(context, config);

    outputChannel.appendLine('l0l1 SQL extension activated');
}

function setupDocumentListeners(
    context: vscode.ExtensionContext,
    config: vscode.WorkspaceConfiguration
): void {
    // Validate on save
    if (config.get<boolean>('validateOnSave', true)) {
        context.subscriptions.push(
            vscode.workspace.onDidSaveTextDocument(async (document) => {
                if (document.languageId === 'sql') {
                    await diagnosticsProvider.validateDocument(document);
                }
            })
        );
    }

    // Validate on type (with debounce)
    if (config.get<boolean>('validateOnType', false)) {
        let timeout: NodeJS.Timeout | undefined;
        const delay = config.get<number>('validateDelay', 500);

        context.subscriptions.push(
            vscode.workspace.onDidChangeTextDocument(async (e) => {
                if (e.document.languageId === 'sql') {
                    if (timeout) {
                        clearTimeout(timeout);
                    }
                    timeout = setTimeout(async () => {
                        await diagnosticsProvider.validateDocument(e.document);
                    }, delay);
                }
            })
        );
    }

    // Validate on open
    context.subscriptions.push(
        vscode.workspace.onDidOpenTextDocument(async (document) => {
            if (document.languageId === 'sql') {
                await diagnosticsProvider.validateDocument(document);
            }
        })
    );

    // Validate already open SQL documents
    vscode.workspace.textDocuments.forEach(async (document) => {
        if (document.languageId === 'sql') {
            await diagnosticsProvider.validateDocument(document);
        }
    });
}

export async function deactivate(): Promise<void> {
    if (client) {
        await client.stop();
    }
}
