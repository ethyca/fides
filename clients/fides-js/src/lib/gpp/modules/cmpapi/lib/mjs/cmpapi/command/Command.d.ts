import { CmpApiContext } from "../CmpApiContext.js";
import { CommandCallback } from "./CommandCallback.js";
export declare abstract class Command {
    protected callback: CommandCallback;
    protected parameter: any;
    protected success: boolean;
    protected cmpApiContext: CmpApiContext;
    constructor(cmpApiContext: CmpApiContext, callback?: CommandCallback, parameter?: any);
    execute(): any;
    protected invokeCallback(response: any): void;
    protected abstract respond(): any;
}
