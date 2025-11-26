import * as vscode from 'vscode';

export class StatusBar implements vscode.Disposable {
    private statusBarItem: vscode.StatusBarItem;
    private isConnected: boolean = false;
    private isWorking: boolean = false;

    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Right,
            100
        );
        this.statusBarItem.command = 'l0l1.showOutput';
        this.update();

        // Only show when SQL file is active
        vscode.window.onDidChangeActiveTextEditor((editor) => {
            if (editor && editor.document.languageId === 'sql') {
                this.statusBarItem.show();
            } else {
                const config = vscode.workspace.getConfiguration('l0l1');
                if (!config.get<boolean>('showStatusBar', true)) {
                    this.statusBarItem.hide();
                }
            }
        });

        // Check initial state
        const editor = vscode.window.activeTextEditor;
        if (editor && editor.document.languageId === 'sql') {
            this.statusBarItem.show();
        }
    }

    setConnected(connected: boolean): void {
        this.isConnected = connected;
        this.update();
    }

    setWorking(working: boolean): void {
        this.isWorking = working;
        this.update();
    }

    private update(): void {
        if (this.isWorking) {
            this.statusBarItem.text = '$(sync~spin) l0l1';
            this.statusBarItem.tooltip = 'l0l1: Processing...';
            this.statusBarItem.backgroundColor = undefined;
        } else if (this.isConnected) {
            this.statusBarItem.text = '$(check) l0l1';
            this.statusBarItem.tooltip = 'l0l1: Connected';
            this.statusBarItem.backgroundColor = undefined;
        } else {
            this.statusBarItem.text = '$(warning) l0l1';
            this.statusBarItem.tooltip = 'l0l1: Disconnected - Click to view output';
            this.statusBarItem.backgroundColor = new vscode.ThemeColor(
                'statusBarItem.warningBackground'
            );
        }

        const config = vscode.workspace.getConfiguration('l0l1');
        if (config.get<boolean>('showStatusBar', true)) {
            this.statusBarItem.show();
        }
    }

    dispose(): void {
        this.statusBarItem.dispose();
    }
}
