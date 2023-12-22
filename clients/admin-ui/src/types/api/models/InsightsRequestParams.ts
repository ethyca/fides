
export enum TimeInterval {
    seconds = "seconds",
    hours = "hours",
    days = "days",
    weeks = "weeks",
    months = "months",
    years = "years",
}

export enum GroupByOptions {
    dsr_policy = "dsr_policy",
    status = "status",
    country = "country",
    preference = "preference",
    notice = "notice",
}

export enum RecordType {
    consent = "consent",
    dsr = "dsr",
}

/**
 * Insights Request Params Schema
 */
export type InsightsRequestParams = {
    record_type?: RecordType;
    time_interval?: TimeInterval;
    group_by?: GroupByOptions;
    created_gt?: string;
    created_lt?: string;
};