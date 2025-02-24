import { CommandCallback } from "./command/CommandCallback.js";
import { CmpApiContext } from "./CmpApiContext.js";
import { CustomCommands } from "./CustomCommands.js";
export declare type APIArgs = [string, CommandCallback?, any?, number?];
export declare class CallResponder {
    private callQueue;
    private readonly customCommands;
    private cmpApiContext;
    constructor(cmpApiContext: CmpApiContext, customCommands?: CustomCommands);
    /**
     * Handler for all page call commands
     * @param {string} command
     * @param {CommandCallback} callback
     * @param {any} param
     * @param {number} version
     */
    apiCall(command: string, callback?: CommandCallback, parameter?: any, version?: number): void;
    purgeQueuedCalls(): void;
    private isCustomCommand;
    private isBuiltInCommand;
}
