import * as vscode from 'vscode';
import * as fs from 'fs';
import { L0l1Client, ValidationIssue } from './client';

export class DiagnosticsProvider implements vscode.Disposable {
    private diagnosticCollection: vscode.DiagnosticCollection;
    private client: L0l1Client;

    constructor(client: L0l1Client) {
        this.client = client;
        this.diagnosticCollection = vscode.languages.createDiagnosticCollection('l0l1');
    }

    async validateDocument(document: vscode.TextDocument): Promise<void> {
        if (document.languageId !== 'sql') {
            return;
        }

        if (!this.client.isConnected()) {
            return;
        }

        try {
            const config = vscode.workspace.getConfiguration('l0l1');
            const schemaFile = config.get<string>('schemaFile', '');
            let schemaContext: string | undefined;

            if (schemaFile && fs.existsSync(schemaFile)) {
                schemaContext = fs.readFileSync(schemaFile, 'utf-8');
            }

            const result = await this.client.validate(document.getText(), schemaContext);
            const diagnostics: vscode.Diagnostic[] = [];

            // Add errors
            result.errors.forEach((issue) => {
                diagnostics.push(this.createDiagnostic(document, issue, vscode.DiagnosticSeverity.Error));
            });

            // Add warnings
            result.warnings.forEach((issue) => {
                diagnostics.push(this.createDiagnostic(document, issue, vscode.DiagnosticSeverity.Warning));
            });

            // Add PII detection if enabled
            if (config.get<boolean>('enablePiiDetection', true)) {
                try {
                    const piiResult = await this.client.checkPii(document.getText());
                    piiResult.detections.forEach((detection) => {
                        const startPos = document.positionAt(detection.start);
                        const endPos = document.positionAt(detection.end);
                        const range = new vscode.Range(startPos, endPos);

                        diagnostics.push(
                            new vscode.Diagnostic(
                                range,
                                `PII detected: ${detection.entityType} (${(detection.score * 100).toFixed(0)}% confidence)`,
                                vscode.DiagnosticSeverity.Warning
                            )
                        );
                    });
                } catch {
                    // PII detection is optional, don't fail validation
                }
            }

            this.diagnosticCollection.set(document.uri, diagnostics);
        } catch (error) {
            // Clear diagnostics on error
            this.diagnosticCollection.delete(document.uri);
        }
    }

    private createDiagnostic(
        document: vscode.TextDocument,
        issue: ValidationIssue,
        severity: vscode.DiagnosticSeverity
    ): vscode.Diagnostic {
        let range: vscode.Range;

        if (issue.line !== undefined) {
            const startLine = Math.max(0, issue.line - 1);
            const startChar = issue.column ?? 0;
            const endLine = issue.endLine !== undefined ? issue.endLine - 1 : startLine;
            const endChar = issue.endColumn ?? document.lineAt(endLine).text.length;

            range = new vscode.Range(
                new vscode.Position(startLine, startChar),
                new vscode.Position(endLine, endChar)
            );
        } else {
            // Highlight entire document if no line info
            range = new vscode.Range(
                document.positionAt(0),
                document.positionAt(document.getText().length)
            );
        }

        const diagnostic = new vscode.Diagnostic(range, issue.message, severity);
        diagnostic.source = 'l0l1';

        return diagnostic;
    }

    clearDiagnostics(document: vscode.TextDocument): void {
        this.diagnosticCollection.delete(document.uri);
    }

    dispose(): void {
        this.diagnosticCollection.dispose();
    }
}
