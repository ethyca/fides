import * as vscode from 'vscode';
import * as child_process from 'child_process';
import * as path from 'path';

const PARSE_ON_SAVE_CONFIG = "conf.fidesctl.parseOnSave";
const FIDES_CONFIG_PATH_CONFIG = "conf.fidesctl.confFilePath";
const FIDES_MANIFEST_PATH_CONFIG = "conf.fidesctl.manifestFilePath";

export function activate(context: vscode.ExtensionContext) {
	let outputChannel = vscode.window.createOutputChannel("Fidesctl");
	let rootpath = vscode.workspace.rootPath;

	let disposables = [];

	disposables.push(vscode.commands.registerCommand('fidesctl-config-parser.fidesctlConfigure', () => {
		vscode.window.showInputBox({ "title": "Enter conf(fidesctl.toml) file path:" })
			.then(inputConfigFilePath => {
				let fidesConfigPath = vscode.workspace.getConfiguration().get(FIDES_CONFIG_PATH_CONFIG);
				outputChannel.appendLine(`Current ${FIDES_CONFIG_PATH_CONFIG} config value:${fidesConfigPath}`);

				vscode.workspace.getConfiguration().update(FIDES_CONFIG_PATH_CONFIG, inputConfigFilePath, vscode.ConfigurationTarget.Workspace);
				outputChannel.appendLine(`Set ${FIDES_CONFIG_PATH_CONFIG} config to ${inputConfigFilePath}`);

				vscode.window.showInputBox({ "title": "Enter manifest file path:" })
					.then(inputManifestPath => { 
						if(!path.isAbsolute(inputManifestPath!)){
							inputManifestPath = path.join(rootpath!,inputManifestPath!);
						}

						let fidesManifestPath = vscode.workspace.getConfiguration().get(FIDES_MANIFEST_PATH_CONFIG);
						outputChannel.appendLine(`Current ${FIDES_MANIFEST_PATH_CONFIG} config value:${fidesManifestPath}`);

						vscode.workspace.getConfiguration().update(FIDES_MANIFEST_PATH_CONFIG, inputManifestPath, vscode.ConfigurationTarget.Workspace);
						outputChannel.appendLine(`Set ${FIDES_MANIFEST_PATH_CONFIG} config to ${inputManifestPath}`);
					});
			});
	}));

	disposables.push(vscode.commands.registerCommand('fidesctl-config-parser.fidesctlEnableParseOnSave', () => {
		let fidesConfigPath = vscode.workspace.getConfiguration().get(FIDES_CONFIG_PATH_CONFIG);
		let fidesManifestPath = vscode.workspace.getConfiguration().get(FIDES_MANIFEST_PATH_CONFIG);

		if(!fidesConfigPath || !fidesManifestPath){
			vscode.window.showErrorMessage(`Use "Fidesctl Configure Plugin" to configure parsing`);
			outputChannel.appendLine(`Could not enable manifest parse on save as plugin is not configured`);
			return;
		}

		let parseOnSave = vscode.workspace.getConfiguration().get(PARSE_ON_SAVE_CONFIG);
		outputChannel.appendLine(`Current ${PARSE_ON_SAVE_CONFIG} config value:${parseOnSave}`);

		vscode.workspace.getConfiguration().update(PARSE_ON_SAVE_CONFIG, true, vscode.ConfigurationTarget.Workspace);
		vscode.window.showInformationMessage(`Enabled parsing manifest files on save`);

		outputChannel.appendLine(`Set ${PARSE_ON_SAVE_CONFIG} config to true`);
	}));

	disposables.push(vscode.commands.registerCommand('fidesctl-config-parser.fidesctlDisableParseOnSave', () => {
		let parseOnSave = vscode.workspace.getConfiguration().get(PARSE_ON_SAVE_CONFIG);
		outputChannel.appendLine(`Current ${PARSE_ON_SAVE_CONFIG} config value:${parseOnSave}`);

		vscode.workspace.getConfiguration().update(PARSE_ON_SAVE_CONFIG, false, vscode.ConfigurationTarget.Workspace);
		vscode.window.showInformationMessage(`Disabled parsing manifest files on save`);

		outputChannel.appendLine(`Set ${PARSE_ON_SAVE_CONFIG} config to false`);
	}));

	disposables.push(vscode.commands.registerCommand('fidesctl-config-parser.fidesctlParse', () => {
		parseManifest();
	}));

	disposables.push(vscode.workspace.onDidSaveTextDocument((document: vscode.TextDocument) => {
		if (vscode.workspace.getConfiguration().get(PARSE_ON_SAVE_CONFIG)) {
			let fidesManifestPath = vscode.workspace.getConfiguration().get(FIDES_MANIFEST_PATH_CONFIG);
			let savedFile = document.fileName;
			if(savedFile.includes(`${fidesManifestPath}`)){
				parseManifest();
			}
		}
	}));

	disposables.forEach(disposable => context.subscriptions.push(disposable));

	let parseManifest = () => {
		let fidesConfigPath = vscode.workspace.getConfiguration().get(FIDES_CONFIG_PATH_CONFIG);
		let fidesManifestPath = vscode.workspace.getConfiguration().get(FIDES_MANIFEST_PATH_CONFIG);

		if(!fidesConfigPath || !fidesManifestPath){
			vscode.window.showErrorMessage(`Use "Fidesctl Configure Plugin" to configure parsing`);
			outputChannel.appendLine(`Could not parse manifest as plugin is not configured`);
			return;
		}

		outputChannel.appendLine(`Parsing manifest at path ${fidesManifestPath}`);
		child_process.exec(`fidesctl parse ${fidesManifestPath}`,
			{ env: { ...process.env, FIDESCTL_CONFIG_PATH: `${fidesConfigPath}` } },
			(err: child_process.ExecException | null, stdout: string, stderr: string) => {
				if (err) {
					vscode.window.showErrorMessage(`Failed to parse fidesctl manifest`);
					outputChannel.appendLine(`Failed to parse fidesctl manifest`);
					outputChannel.appendLine(err.message);
					console.error(err);
				} else {
					vscode.window.showInformationMessage(`Successfully parsed fidesctl manifest`);
					outputChannel.appendLine(`Successfully parsed fidesctl manifest`);
					outputChannel.appendLine(stdout);
					console.log(stdout);
				}
			});
	};
}

// this method is called when your extension is deactivated
export function deactivate() { }
