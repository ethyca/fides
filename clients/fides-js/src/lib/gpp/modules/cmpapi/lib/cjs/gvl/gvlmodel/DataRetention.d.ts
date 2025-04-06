import { IntMap } from './IntMap.js';
export interface DataRetention {
    stdRetention?: number;
    purposes: IntMap<number>;
    specialPurposes: IntMap<number>;
}
