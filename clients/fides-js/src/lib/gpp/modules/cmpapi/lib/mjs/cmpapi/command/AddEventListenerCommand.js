import { EventData } from "../model/EventData.js";
import { PingData } from "../model/PingData.js";
import { Command } from "./Command.js";
export class AddEventListenerCommand extends Command {
    respond() {
        let listenerId = this.cmpApiContext.eventQueue.add({
            callback: this.callback,
            parameter: this.parameter,
        });
        let eventData = new EventData("listenerRegistered", listenerId, true, new PingData(this.cmpApiContext));
        this.invokeCallback(eventData);
    }
}
