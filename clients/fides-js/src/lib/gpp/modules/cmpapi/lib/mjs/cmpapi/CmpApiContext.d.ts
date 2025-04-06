import { CmpStatus } from "./status/CmpStatus.js";
import { CmpDisplayStatus } from "./status/CmpDisplayStatus.js";
import { EventStatus } from "./status/EventStatus.js";
import { EventListenerQueue } from "./EventListenerQueue.js";
import { GppModel } from "../encoder/GppModel.js";
import { SignalStatus } from "./status/SignalStatus.js";
/**
 * Class holds shareable data across cmp api and provides change event listener for GppModel.
 * Within the context of the CmpApi, this class acts much like a global state or database,
 * where CmpApi sets data and Commands read the data.
 */
export declare class CmpApiContext {
    gppVersion: string;
    supportedAPIs: any[];
    readonly eventQueue: EventListenerQueue;
    cmpStatus: CmpStatus;
    cmpDisplayStatus: CmpDisplayStatus;
    signalStatus: SignalStatus;
    applicableSections: number[];
    gppModel: GppModel;
    cmpId: number;
    cmpVersion: number;
    eventStatus: EventStatus;
    reset(): void;
}
