import { PingCommand } from "./PingCommand.js";
import { GetFieldCommand } from "./GetFieldCommand.js";
import { GetSectionCommand } from "./GetSectionCommand.js";
import { HasSectionCommand } from "./HasSectionCommand.js";
import { GppCommand } from "./GppCommand.js";
import { AddEventListenerCommand } from "./AddEventListenerCommand.js";
import { RemoveEventListenerCommand } from "./RemoveEventListenerCommand.js";
export class CommandMap {
    static [GppCommand.ADD_EVENT_LISTENER] = AddEventListenerCommand;
    static [GppCommand.GET_FIELD] = GetFieldCommand;
    static [GppCommand.GET_SECTION] = GetSectionCommand;
    static [GppCommand.HAS_SECTION] = HasSectionCommand;
    static [GppCommand.PING] = PingCommand;
    static [GppCommand.REMOVE_EVENT_LISTENER] = RemoveEventListenerCommand;
}
