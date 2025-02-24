import { CommandCallback } from "./command/CommandCallback.js";
export interface CustomCommands {
    [commandName: string]: (callback: CommandCallback, parameter?: any) => void;
}
