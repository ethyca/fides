import { CmpApiContext } from "./CmpApiContext.js";
import { CommandCallback } from "./command/CommandCallback.js";
interface EventItem {
    callback: CommandCallback;
    parameter?: any;
}
export declare class EventListenerQueue {
    private eventQueue;
    private queueNumber;
    private cmpApiContext;
    constructor(cmpApiContext: CmpApiContext);
    add(eventItem: EventItem): number;
    get(listenerId: number): EventItem;
    remove(listenerId: number): boolean;
    exec(eventName: string, data: any): void;
    clear(): void;
    get size(): number;
}
export {};
