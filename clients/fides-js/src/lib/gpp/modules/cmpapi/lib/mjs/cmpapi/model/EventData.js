export class EventData {
    eventName;
    listenerId;
    data;
    pingData;
    constructor(eventName, listenerId, data, pingData) {
        this.eventName = eventName;
        this.listenerId = listenerId;
        this.data = data;
        this.pingData = pingData;
    }
}
