import { GVLMapItem } from './GVLMapItem.js';
export interface Stack extends GVLMapItem {
    purposes: number[];
    specialFeatures: number[];
    description: string;
}
