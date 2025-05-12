import { EventData } from "./model/EventData.js";
import { PingData } from "./model/PingData.js";
export class EventListenerQueue {
    eventQueue = new Map();
    queueNumber = 1000;
    cmpApiContext;
    constructor(cmpApiContext) {
        this.cmpApiContext = cmpApiContext;
        try {
            // get queued commands
            let events = window["__gpp"]("events") || [];
            for (var i = 0; i < events.length; i++) {
                let eventItem = events[i];
                this.eventQueue.set(eventItem.id, {
                    callback: eventItem.callback,
                    parameter: eventItem.parameter,
                });
            }
        }
        catch (err) {
            console.log(err);
        }
    }
    add(eventItem) {
        this.eventQueue.set(this.queueNumber, eventItem);
        return this.queueNumber++;
    }
    get(listenerId) {
        return this.eventQueue.get(listenerId);
    }
    remove(listenerId) {
        return this.eventQueue.delete(listenerId);
    }
    exec(eventName, data) {
        this.eventQueue.forEach((eventItem, listenerId) => {
            let eventData = new EventData(eventName, listenerId, data, new PingData(this.cmpApiContext));
            let success = true;
            eventItem.callback(eventData, success);
        });
    }
    clear() {
        this.queueNumber = 1000;
        this.eventQueue.clear();
    }
    get size() {
        return this.eventQueue.size;
    }
}
