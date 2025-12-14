import * as vscode from 'vscode';
import * as path from 'path';
import {
    LanguageClient,
    LanguageClientOptions,
    ServerOptions,
} from 'vscode-languageclient/node';

let client: LanguageClient;

export function activate(context: vscode.ExtensionContext) {
    console.log('Null-Lang extension is now active');

    const pythonPath = vscode.workspace
        .getConfiguration('null')
        .get('pythonPath', 'python');

    const serverOptions: ServerOptions = {
        command: pythonPath,
        args: ['-m', 'tools.null_lsp.server'],
        options: {
            cwd: vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath,
        },
    };

    const clientOptions: LanguageClientOptions = {
        documentSelector: [{ scheme: 'file', language: 'null' }],
        synchronize: {
            fileEvents: vscode.workspace.createFileSystemWatcher('**/.clientrc'),
        },
    };

    client = new LanguageClient(
        'nullLang',
        'Null-Lang Language Server',
        serverOptions,
        clientOptions
    );

    client.start();

    context.subscriptions.push(
        vscode.commands.registerCommand('nullLang.runFile', () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor');
                return;
            }

            const filePath = editor.document.fileName;
            const terminal =
                vscode.window.activeTerminal || vscode.window.createTerminal('Null');
            terminal.show();
            terminal.sendText(`python -m src.null_system.cli run "${filePath}"`);
        }),
        vscode.commands.registerCommand('nullLang.compileFile', () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No active editor');
                return;
            }

            const filePath = editor.document.fileName;
            const terminal =
                vscode.window.activeTerminal || vscode.window.createTerminal('Null');
            terminal.show();
            terminal.sendText(`python -m src.null_system.cli compile "${filePath}"`);
        })
    );

    context.subscriptions.push(client);
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}
