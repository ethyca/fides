import { GVLError } from "./gvl/error/GVLError.js";
import { ConsentLanguages } from "./gvl/gvlmodel/ConsentLanguages.js";
import { DataCategory } from "./gvl/gvlmodel/DataCategory.js";
import { Feature } from "./gvl/gvlmodel/Feature.js";
import { IntMap } from "./gvl/gvlmodel/IntMap.js";
import { Purpose } from "./gvl/gvlmodel/Purpose.js";
import { Stack } from "./gvl/gvlmodel/Stack.js";
import { Vendor } from "./gvl/gvlmodel/Vendor.js";
import { VendorList } from "./gvl/gvlmodel/VendorList.js";
export declare class GVLUrlConfig {
    /**
     * baseUrl - Entities using the vendor-list.json are required by the iab to
     * host their own copy of it to reduce the load on the iab's infrastructure
     * so a 'base' url must be set to be put together with the versioning scheme
     * of the filenames.
     *
     * @param {string} url - the base url to load the vendor-list.json from.  This is
     * broken out from the filename because it follows a different scheme for
     * latest file vs versioned files.
     *
     * ](https://github.com/InteractiveAdvertisingBureau/GDPR-Transparency-and-Consent-Framework/blob/master/TCFv2/IAB%20Tech%20Lab%20-%20Consent%20string%20and%20vendor%20list%20formats%20v2.md#caching-the-global-vendor-list)
     */
    baseUrl: string;
    /**
     * @param {string} - the latest is assumed to be vendor-list.json because
     * that is what the iab uses, but it could be different... if you want
     */
    version: string | number;
    /**
     * @param {string} - the latest is assumed to be vendor-list.json because
     * that is what the iab uses, but it could be different... if you want
     */
    latestFilename: string;
    /**
     * @param {string} - the versioned name is assumed to be
     * vendor-list-v[VERSION].json where [VERSION] will be replaced with the
     * specified version.  But it could be different... if you want just make
     * sure to include the [VERSION] macro if you have a numbering scheme, it's a
     * simple string substitution.
     *
     * eg.
     * ```javascript
     * GVL.baseUrl = "http://www.mydomain.com/iabcmp/";
     * GVL.versionedFilename = "vendorlist?getVersion=[VERSION]";
     * ```
     */
    versionedFilename: string;
    /**
     * @param {string} - Translations of the names and descriptions for Purposes,
     * Special Purposes, Features, and Special Features to non-English languages
     * are contained in a file where attributes containing English content
     * (except vendor declaration information) are translated.  The iab publishes
     * one following the scheme below where the LANG is the iso639-1 language
     * code.  For a list of available translations
     * [please go here](https://register.consensu.org/Translation).
     *
     * eg.
     * ```javascript
     * GVL.baseUrl = "http://www.mydomain.com/iabcmp/";
     * GVL.languageFilename = "purposes?getPurposes=[LANG]";
     * ```
     */
    languageFilename: string;
}
/**
 * class with utilities for managing the global vendor list.  Will use JSON to
 * fetch the vendor list from specified url and will serialize it into this
 * object and provide accessors.  Provides ways to group vendors on the list by
 * purpose and feature.
 */
export declare class GVL implements VendorList {
    vendors: IntMap<Vendor>;
    static DEFAULT_LANGUAGE: string;
    readonly consentLanguages: ConsentLanguages;
    gvlSpecificationVersion: number;
    vendorListVersion: number;
    tcfPolicyVersion: number;
    lastUpdated: string | Date;
    purposes: IntMap<Purpose>;
    specialPurposes: IntMap<Purpose>;
    features: IntMap<Feature>;
    specialFeatures: IntMap<Feature>;
    stacks: IntMap<Stack>;
    dataCategories?: IntMap<DataCategory>;
    language: string;
    private vendorIds;
    private ready;
    private fullVendorList;
    private byPurposeVendorMap;
    private bySpecialPurposeVendorMap;
    private byFeatureVendorMap;
    private bySpecialFeatureVendorMap;
    private baseUrl;
    private languageFilename;
    static fromVendorList(vendorList: VendorList): GVL;
    /**
     * **
     * @param {GVLConfig} - Configuration containing url configuration
     *
     * @throws {GVLError} - If the url is http[s]://vendorlist.consensu.org/...
     * this will throw an error.  IAB Europe requires that that CMPs and Vendors
     * cache their own copies of the GVL to minimize load on their
     * infrastructure.  For more information regarding caching of the
     * vendor-list.json, please see [the TCF documentation on 'Caching the Global
     * Vendor List'
     */
    static fromUrl(config: GVLUrlConfig): Promise<GVL>;
    /**
     * changeLanguage - retrieves the purpose language translation and sets the
     * internal language variable
     *
     * @param {string} lang - ISO 639-1 langauge code to change language to
     * @return {Promise<void | GVLError>} - returns the `readyPromise` and
     * resolves when this GVL is populated with the data from the language file.
     */
    changeLanguage(lang: string): Promise<void | GVLError>;
    /**
     * getJson - Method for getting the JSON that was downloaded to created this
     * `GVL` object
     *
     * @return {VendorList} - The basic JSON structure without the extra
     * functionality and methods of this class.
     */
    getJson(): VendorList;
    private isVendorList;
    private populate;
    private mapVendors;
    private getFilteredVendors;
    /**
     * getVendorsWithConsentPurpose
     *
     * @param {number} purposeId
     * @return {IntMap<Vendor>} - list of vendors that have declared the consent purpose id
     */
    getVendorsWithConsentPurpose(purposeId: number): IntMap<Vendor>;
    /**
     * getVendorsWithLegIntPurpose
     *
     * @param {number} purposeId
     * @return {IntMap<Vendor>} - list of vendors that have declared the legInt (Legitimate Interest) purpose id
     */
    getVendorsWithLegIntPurpose(purposeId: number): IntMap<Vendor>;
    /**
     * getVendorsWithFlexiblePurpose
     *
     * @param {number} purposeId
     * @return {IntMap<Vendor>} - list of vendors that have declared the flexible purpose id
     */
    getVendorsWithFlexiblePurpose(purposeId: number): IntMap<Vendor>;
    /**
     * getVendorsWithSpecialPurpose
     *
     * @param {number} specialPurposeId
     * @return {IntMap<Vendor>} - list of vendors that have declared the special purpose id
     */
    getVendorsWithSpecialPurpose(specialPurposeId: number): IntMap<Vendor>;
    /**
     * getVendorsWithFeature
     *
     * @param {number} featureId
     * @return {IntMap<Vendor>} - list of vendors that have declared the feature id
     */
    getVendorsWithFeature(featureId: number): IntMap<Vendor>;
    /**
     * getVendorsWithSpecialFeature
     *
     * @param {number} specialFeatureId
     * @return {IntMap<Vendor>} - list of vendors that have declared the special feature id
     */
    getVendorsWithSpecialFeature(specialFeatureId: number): IntMap<Vendor>;
    /**
     * narrowVendorsTo - narrows vendors represented in this GVL to the list of ids passed in
     *
     * @param {number[]} vendorIds - list of ids to narrow this GVL to
     * @return {void}
     */
    narrowVendorsTo(vendorIds: number[]): void;
    /**
     * isReady - Whether or not this instance is ready to be used.  This will be
     * immediately and synchronously true if a vendorlist object is passed into
     * the constructor or once the JSON vendorllist is retrieved.
     *
     * @return {boolean} whether or not the instance is ready to be interacted
     * with and all the data is populated
     */
    get isReady(): boolean;
    static isInstanceOf(questionableInstance: unknown): questionableInstance is GVL;
}
