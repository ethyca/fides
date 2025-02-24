import { IntMap } from './IntMap.js';
import { Feature } from './Feature.js';
import { Purpose } from './Purpose.js';
import { Stack } from './Stack.js';
import { DataCategory } from './DataCategory.js';
export interface Declarations {
    purposes: IntMap<Purpose>;
    specialPurposes: IntMap<Purpose>;
    features: IntMap<Feature>;
    specialFeatures: IntMap<Feature>;
    stacks: IntMap<Stack>;
    dataCategories?: IntMap<DataCategory>;
}
