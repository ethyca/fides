import { UserConsentPreference } from "./UserConsentPreference";

/**
 * Insights Response Schema
 */
export type InsightsResponse = {
    Created: string;
    count: number;
    Preference?: UserConsentPreference;
    Notice_title?: string;
    User_geography?: string;
};


