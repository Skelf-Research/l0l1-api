import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { L0l1Client } from './client';
import { StatusBar } from './statusBar';

export function registerCommands(
    context: vscode.ExtensionContext,
    client: L0l1Client,
    statusBar: StatusBar,
    outputChannel: vscode.OutputChannel
): void {
    // Validate document
    context.subscriptions.push(
        vscode.commands.registerCommand('l0l1.validateDocument', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor || editor.document.languageId !== 'sql') {
                vscode.window.showWarningMessage('Please open a SQL file to validate');
                return;
            }

            await validateAndShowResults(client, editor.document.getText(), outputChannel);
        })
    );

    // Validate selection
    context.subscriptions.push(
        vscode.commands.registerCommand('l0l1.validateSelection', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                return;
            }

            const selection = editor.selection;
            const text = selection.isEmpty
                ? editor.document.getText()
                : editor.document.getText(selection);

            await validateAndShowResults(client, text, outputChannel);
        })
    );

    // Explain query
    context.subscriptions.push(
        vscode.commands.registerCommand('l0l1.explainQuery', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                return;
            }

            const selection = editor.selection;
            const query = selection.isEmpty
                ? editor.document.getText()
                : editor.document.getText(selection);

            try {
                statusBar.setWorking(true);
                const result = await client.explain(query);

                const panel = vscode.window.createWebviewPanel(
                    'l0l1Explanation',
                    'SQL Explanation',
                    vscode.ViewColumn.Beside,
                    {}
                );

                panel.webview.html = getExplanationHtml(query, result);
            } catch (error) {
                const message = error instanceof Error ? error.message : String(error);
                vscode.window.showErrorMessage(`Failed to explain query: ${message}`);
            } finally {
                statusBar.setWorking(false);
            }
        })
    );

    // Check PII
    context.subscriptions.push(
        vscode.commands.registerCommand('l0l1.checkPii', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                return;
            }

            const selection = editor.selection;
            const query = selection.isEmpty
                ? editor.document.getText()
                : editor.document.getText(selection);

            try {
                statusBar.setWorking(true);
                const result = await client.checkPii(query);

                if (!result.hasPii) {
                    vscode.window.showInformationMessage('No PII detected in query');
                    return;
                }

                const items = result.detections.map((d) => ({
                    label: `$(shield) ${d.entityType}`,
                    description: d.value,
                    detail: `Confidence: ${(d.score * 100).toFixed(0)}%`,
                }));

                const selected = await vscode.window.showQuickPick(items, {
                    title: `Found ${result.detections.length} PII item(s)`,
                    placeHolder: 'Select to view details',
                });

                if (selected) {
                    vscode.window.showInformationMessage(
                        `${selected.label}: ${selected.description}`
                    );
                }
            } catch (error) {
                const message = error instanceof Error ? error.message : String(error);
                vscode.window.showErrorMessage(`PII check failed: ${message}`);
            } finally {
                statusBar.setWorking(false);
            }
        })
    );

    // Anonymize PII
    context.subscriptions.push(
        vscode.commands.registerCommand('l0l1.anonymizePii', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                return;
            }

            const selection = editor.selection;
            const query = selection.isEmpty
                ? editor.document.getText()
                : editor.document.getText(selection);

            try {
                statusBar.setWorking(true);
                const result = await client.anonymize(query);

                if (!result.anonymizedQuery || result.anonymizedQuery === query) {
                    vscode.window.showInformationMessage('No PII found to anonymize');
                    return;
                }

                const choice = await vscode.window.showInformationMessage(
                    `Found ${result.detections.length} PII item(s). Replace with anonymized version?`,
                    'Replace',
                    'Copy to Clipboard',
                    'Cancel'
                );

                if (choice === 'Replace') {
                    await editor.edit((editBuilder) => {
                        const range = selection.isEmpty
                            ? new vscode.Range(
                                  editor.document.positionAt(0),
                                  editor.document.positionAt(editor.document.getText().length)
                              )
                            : selection;
                        editBuilder.replace(range, result.anonymizedQuery!);
                    });
                } else if (choice === 'Copy to Clipboard') {
                    await vscode.env.clipboard.writeText(result.anonymizedQuery);
                    vscode.window.showInformationMessage('Anonymized query copied to clipboard');
                }
            } catch (error) {
                const message = error instanceof Error ? error.message : String(error);
                vscode.window.showErrorMessage(`Anonymization failed: ${message}`);
            } finally {
                statusBar.setWorking(false);
            }
        })
    );

    // Complete query
    context.subscriptions.push(
        vscode.commands.registerCommand('l0l1.completeQuery', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                return;
            }

            const position = editor.selection.active;
            const textUntilPosition = editor.document.getText(
                new vscode.Range(new vscode.Position(0, 0), position)
            );

            try {
                statusBar.setWorking(true);
                const result = await client.complete(textUntilPosition);

                if (result.completions.length === 0) {
                    vscode.window.showInformationMessage('No completions available');
                    return;
                }

                const items = result.completions.map((c, i) => ({
                    label: `$(symbol-snippet) Suggestion ${i + 1}`,
                    description: c.length > 60 ? c.substring(0, 60) + '...' : c,
                    detail: c,
                    completion: c,
                }));

                const selected = await vscode.window.showQuickPick(items, {
                    title: 'SQL Completions',
                    placeHolder: 'Select a completion',
                });

                if (selected) {
                    await editor.edit((editBuilder) => {
                        editBuilder.replace(
                            new vscode.Range(new vscode.Position(0, 0), position),
                            selected.completion
                        );
                    });
                }
            } catch (error) {
                const message = error instanceof Error ? error.message : String(error);
                vscode.window.showErrorMessage(`Completion failed: ${message}`);
            } finally {
                statusBar.setWorking(false);
            }
        })
    );

    // Set schema
    context.subscriptions.push(
        vscode.commands.registerCommand('l0l1.setSchema', async () => {
            const options: vscode.OpenDialogOptions = {
                canSelectMany: false,
                filters: {
                    'SQL Files': ['sql'],
                    'All Files': ['*'],
                },
                title: 'Select Schema File',
            };

            const fileUri = await vscode.window.showOpenDialog(options);
            if (fileUri && fileUri[0]) {
                const config = vscode.workspace.getConfiguration('l0l1');
                await config.update('schemaFile', fileUri[0].fsPath, vscode.ConfigurationTarget.Workspace);
                vscode.window.showInformationMessage(`Schema set to: ${path.basename(fileUri[0].fsPath)}`);
            }
        })
    );

    // Clear schema
    context.subscriptions.push(
        vscode.commands.registerCommand('l0l1.clearSchema', async () => {
            const config = vscode.workspace.getConfiguration('l0l1');
            await config.update('schemaFile', '', vscode.ConfigurationTarget.Workspace);
            vscode.window.showInformationMessage('Schema context cleared');
        })
    );

    // Show output
    context.subscriptions.push(
        vscode.commands.registerCommand('l0l1.showOutput', () => {
            outputChannel.show();
        })
    );

    // Server commands
    context.subscriptions.push(
        vscode.commands.registerCommand('l0l1.startServer', async () => {
            try {
                await client.start();
                statusBar.setConnected(true);
                vscode.window.showInformationMessage('l0l1 server started');
            } catch (error) {
                const message = error instanceof Error ? error.message : String(error);
                vscode.window.showErrorMessage(`Failed to start server: ${message}`);
            }
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('l0l1.stopServer', async () => {
            await client.stop();
            statusBar.setConnected(false);
            vscode.window.showInformationMessage('l0l1 server stopped');
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('l0l1.restartServer', async () => {
            try {
                await client.restart();
                statusBar.setConnected(true);
                vscode.window.showInformationMessage('l0l1 server restarted');
            } catch (error) {
                const message = error instanceof Error ? error.message : String(error);
                vscode.window.showErrorMessage(`Failed to restart server: ${message}`);
            }
        })
    );
}

async function validateAndShowResults(
    client: L0l1Client,
    query: string,
    outputChannel: vscode.OutputChannel
): Promise<void> {
    try {
        const config = vscode.workspace.getConfiguration('l0l1');
        const schemaFile = config.get<string>('schemaFile', '');
        let schemaContext: string | undefined;

        if (schemaFile && fs.existsSync(schemaFile)) {
            schemaContext = fs.readFileSync(schemaFile, 'utf-8');
        }

        const result = await client.validate(query, schemaContext);

        if (result.valid && result.errors.length === 0 && result.warnings.length === 0) {
            vscode.window.showInformationMessage('SQL query is valid');
            return;
        }

        const items: vscode.QuickPickItem[] = [];

        result.errors.forEach((e) => {
            items.push({
                label: '$(error) Error',
                description: e.message,
                detail: e.line ? `Line ${e.line}` : undefined,
            });
        });

        result.warnings.forEach((w) => {
            items.push({
                label: '$(warning) Warning',
                description: w.message,
                detail: w.line ? `Line ${w.line}` : undefined,
            });
        });

        result.suggestions.forEach((s) => {
            items.push({
                label: '$(lightbulb) Suggestion',
                description: s,
            });
        });

        await vscode.window.showQuickPick(items, {
            title: `Validation Results (${result.errors.length} errors, ${result.warnings.length} warnings)`,
            placeHolder: 'Select an issue to view details',
        });
    } catch (error) {
        const message = error instanceof Error ? error.message : String(error);
        vscode.window.showErrorMessage(`Validation failed: ${message}`);
        outputChannel.appendLine(`Validation error: ${message}`);
    }
}

function getExplanationHtml(query: string, result: { explanation: string; complexity: string; tables: string[] }): string {
    const escapedQuery = query.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const escapedExplanation = result.explanation.replace(/</g, '&lt;').replace(/>/g, '&gt;');

    return `<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            font-family: var(--vscode-font-family);
            padding: 20px;
            color: var(--vscode-foreground);
            background-color: var(--vscode-editor-background);
        }
        h2 {
            color: var(--vscode-textLink-foreground);
            border-bottom: 1px solid var(--vscode-panel-border);
            padding-bottom: 8px;
        }
        .query {
            background-color: var(--vscode-textBlockQuote-background);
            padding: 12px;
            border-radius: 4px;
            font-family: var(--vscode-editor-font-family);
            white-space: pre-wrap;
            margin: 16px 0;
        }
        .explanation {
            line-height: 1.6;
        }
        .meta {
            display: flex;
            gap: 16px;
            margin-top: 16px;
            padding: 12px;
            background-color: var(--vscode-textBlockQuote-background);
            border-radius: 4px;
        }
        .meta-item {
            display: flex;
            flex-direction: column;
        }
        .meta-label {
            font-size: 0.85em;
            color: var(--vscode-descriptionForeground);
        }
        .meta-value {
            font-weight: bold;
        }
        .tables {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .table-tag {
            background-color: var(--vscode-badge-background);
            color: var(--vscode-badge-foreground);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <h2>SQL Query</h2>
    <div class="query">${escapedQuery}</div>

    <h2>Explanation</h2>
    <div class="explanation">${escapedExplanation}</div>

    <div class="meta">
        <div class="meta-item">
            <span class="meta-label">Complexity</span>
            <span class="meta-value">${result.complexity}</span>
        </div>
        <div class="meta-item">
            <span class="meta-label">Tables</span>
            <div class="tables">
                ${result.tables.map((t) => `<span class="table-tag">${t}</span>`).join('')}
            </div>
        </div>
    </div>
</body>
</html>`;
}
