import { GppCommand } from "./command/GppCommand.js";
import { CommandMap } from "./command/CommandMap.js";
export class CallResponder {
    callQueue;
    customCommands;
    cmpApiContext;
    constructor(cmpApiContext, customCommands) {
        this.cmpApiContext = cmpApiContext;
        if (customCommands) {
            /**
             * The addEventListener command and removeEventListener are the only ones
             * that shouldn't be overwritten. The addEventListener command utilizes
             * getTCData command, so overridding the TCData response should happen
             * there.
             */
            let command = GppCommand.ADD_EVENT_LISTENER;
            if (customCommands?.[command]) {
                throw new Error(`Built-In Custom Commmand for ${command} not allowed`);
            }
            command = GppCommand.REMOVE_EVENT_LISTENER;
            if (customCommands?.[command]) {
                throw new Error(`Built-In Custom Commmand for ${command} not allowed`);
            }
            this.customCommands = customCommands;
        }
        try {
            // get queued commands
            this.callQueue = window["__gpp"]() || [];
        }
        catch (err) {
            this.callQueue = [];
        }
        finally {
            window["__gpp"] = this.apiCall.bind(this);
            this.purgeQueuedCalls();
        }
    }
    /**
     * Handler for all page call commands
     * @param {string} command
     * @param {CommandCallback} callback
     * @param {any} param
     * @param {number} version
     */
    apiCall(command, callback, parameter, version) {
        if (typeof command !== "string") {
            callback(null, false);
        }
        else if (callback && typeof callback !== "function") {
            throw new Error("invalid callback function");
        }
        else if (this.isCustomCommand(command)) {
            this.customCommands[command](callback, parameter);
        }
        else if (this.isBuiltInCommand(command)) {
            new CommandMap[command](this.cmpApiContext, callback, parameter).execute();
        }
        else {
            if (callback) {
                callback(null, false);
            }
        }
    }
    purgeQueuedCalls() {
        const queueCopy = this.callQueue;
        this.callQueue = [];
        queueCopy.forEach((args) => {
            window["__gpp"](...args);
        });
    }
    isCustomCommand(command) {
        return this.customCommands && typeof this.customCommands[command] === "function";
    }
    isBuiltInCommand(command) {
        return CommandMap[command] !== undefined;
    }
}
