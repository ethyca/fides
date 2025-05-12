import { GVLMapItem } from './GVLMapItem.js';
export interface Feature extends GVLMapItem {
    description: string;
    descriptionLegal?: string;
    illustrations?: string[];
}
