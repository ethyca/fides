import { EventData } from "../model/EventData.js";
import { PingData } from "../model/PingData.js";
import { Command } from "./Command.js";
export class RemoveEventListenerCommand extends Command {
    respond() {
        let listenerId = this.parameter;
        let removed = this.cmpApiContext.eventQueue.remove(listenerId);
        let eventData = new EventData("listenerRemoved", listenerId, removed, new PingData(this.cmpApiContext));
        this.invokeCallback(eventData);
    }
}
