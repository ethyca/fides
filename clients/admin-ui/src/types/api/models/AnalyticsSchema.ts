import { UserConsentPreference } from "./UserConsentPreference";

/**
 * Analytics Schema
 */
export type AnalyticsSchema = {
    Created: string;
    count: number;
    Preference?: UserConsentPreference;
    Notice_title?: string;
    User_geography?: string;
};


