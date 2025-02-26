import { PingData } from "./PingData.js";
export declare class EventData {
    eventName: string;
    listenerId: number;
    data: any;
    pingData: PingData;
    constructor(eventName: string, listenerId: number, data: any, pingData: PingData);
}
