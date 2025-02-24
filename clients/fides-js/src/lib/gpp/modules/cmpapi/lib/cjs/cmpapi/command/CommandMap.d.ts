import { PingCommand } from "./PingCommand.js";
import { GetFieldCommand } from "./GetFieldCommand.js";
import { GetSectionCommand } from "./GetSectionCommand.js";
import { HasSectionCommand } from "./HasSectionCommand.js";
import { GppCommand } from "./GppCommand.js";
import { AddEventListenerCommand } from "./AddEventListenerCommand.js";
import { RemoveEventListenerCommand } from "./RemoveEventListenerCommand.js";
export declare class CommandMap {
    static [GppCommand.ADD_EVENT_LISTENER]: typeof AddEventListenerCommand;
    static [GppCommand.GET_FIELD]: typeof GetFieldCommand;
    static [GppCommand.GET_SECTION]: typeof GetSectionCommand;
    static [GppCommand.HAS_SECTION]: typeof HasSectionCommand;
    static [GppCommand.PING]: typeof PingCommand;
    static [GppCommand.REMOVE_EVENT_LISTENER]: typeof RemoveEventListenerCommand;
}
