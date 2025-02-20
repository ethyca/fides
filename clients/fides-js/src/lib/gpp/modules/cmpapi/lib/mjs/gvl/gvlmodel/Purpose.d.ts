import { GVLMapItem } from './GVLMapItem.js';
export interface Purpose extends GVLMapItem {
    description: string;
    descriptionLegal?: string;
    illustrations?: string[];
}
