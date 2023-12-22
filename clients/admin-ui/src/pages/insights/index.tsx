import {Center, Heading, Spinner} from "@fidesui/react";
import type { NextPage } from "next";
import dynamic from "next/dynamic";
import React, {useEffect, useMemo, useState} from "react";

import Layout from "~/features/common/Layout";
import {
    useGetInsightsAggregateQuery,
    useGetInsightsTimeSeriesQuery
} from "~/features/plus/plus.slice";
import {GroupByOptions, RecordType, TimeInterval} from "~/types/api/models/InsightsRequestParams";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false, })

/**
 * STYLES
 */
const SECTION_HEADING_PROPS = {
    marginBottom: 1,
    fontSize: "1.25rem",
    fontWeight: "semibold",
};

const SECTION_STYLES: React.CSSProperties = {
    marginBottom: 24,
};

const KPI_STYLES: React.CSSProperties = {
    display: "flex",
    flexDirection: "column",
    justifyContent: "center",
    minWidth: 240,
    minHeight: 220,
    flex: 1,
    padding: 8,
    margin: 8,
    border: "1px solid #eee",
    borderRadius: "4px",
}

const KPI_VALUE_STYLES: React.CSSProperties = {
    fontSize: "3rem",
    fontWeight: 200,
}

const KPI_LABEL_STYLES: React.CSSProperties = {
    textAlign: "center",
    marginLeft: "auto",
    marginRight: "auto",
    fontSize: "1rem",
    fontWeight: 100,
}

const CHART_STYLES: React.CSSProperties = {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    minWidth: 460,
    minHeight: 220,
    flex: 2,
    padding: 8,
    margin: 8,
    border: "1px solid #eee",
    borderRadius: "4px",
}

/**
 * LABELS
 */
const INTERVAL = TimeInterval.days;
const LABEL_INTERVAL = "Daily";

const LABEL_REQUESTS_SECTION = "Privacy Requests";
const LABEL_REQUESTS_TOTAL = "Total Privacy Requests";
const LABEL_REQUESTS_BY_POLICY = "Privacy Requests by Policy";
const LABEL_REQUESTS_TIMESERIES = `${LABEL_INTERVAL} Privacy Requests`;
const LABEL_REQUESTS_TIMESERIES_BY_POLICY = `${LABEL_INTERVAL} Privacy Requests by Policy`;

const LABEL_PREFS_SECTION = "Consent Preferences";
const LABEL_PREFS_TOTAL = "Total Preferences";
const LABEL_PREFS_BY_NOTICE = "Preferences by Notice";
const LABEL_PREFS_TIMESERIES = `${LABEL_INTERVAL} Preferences`;
const LABEL_PREFS_BY_PREFERENCE = "Preferences by Value";
const LABEL_PREFS_TIMESERIES_BY_PREFERENCE = `${LABEL_INTERVAL} Preferences by Value`;

const InsightsPage: NextPage = () => {
    const START_DATE = "2023-01-01T00:00:00.000Z";
    const END_DATE = "2024-01-01T00:00:00.000Z";

    const { data: privacyRequestByPolicy, isLoading: isPrivacyRequestByPolicyLoading } =
        useGetInsightsAggregateQuery({
            record_type: RecordType.dsr,
            group_by: GroupByOptions.dsr_policy,
            created_gt: START_DATE,
            created_lt: END_DATE,
        });
    const { data: privacyRequestByDay, isLoading: isPrivacyRequestByDayLoading } =
        useGetInsightsTimeSeriesQuery({
            record_type: RecordType.dsr,
            time_interval: INTERVAL,
            created_gt: START_DATE,
            created_lt: END_DATE,
        });
    const { data: privacyRequestByDayAndPolicy, isLoading: isPrivacyRequestByDayAndPolicyLoading } =
        useGetInsightsTimeSeriesQuery({
            record_type: RecordType.dsr,
            group_by: GroupByOptions.dsr_policy,
            time_interval: INTERVAL,
            created_gt: START_DATE,
            created_lt: END_DATE,
        });
    const { data: privacyRequestByStatus, isLoading: isPrivacyRequestByStatusLoading } =
        useGetInsightsAggregateQuery({
            record_type: RecordType.dsr,
            group_by: GroupByOptions.status,
            created_gt: START_DATE,
            created_lt: END_DATE,
        });
    const { data: consentByNotice, isLoading: isConsentByNoticeLoading } =
        useGetInsightsAggregateQuery({
            record_type: RecordType.consent,
            group_by: GroupByOptions.notice,
            created_gt: START_DATE,
            created_lt: END_DATE,
        });
    const { data: consentByDay, isLoading: isConsentByDayLoading } =
        useGetInsightsTimeSeriesQuery({
            record_type: RecordType.consent,
            time_interval: INTERVAL,
            created_gt: START_DATE,
            created_lt: END_DATE,
        });
    const { data: consentByPreference, isLoading: isConsentByPreferenceLoading } =
        useGetInsightsAggregateQuery({
            record_type: RecordType.consent,
            group_by: GroupByOptions.preference,
            created_gt: START_DATE,
            created_lt: END_DATE,
        });
    const { data: consentByDayAndPreference, isLoading: isConsentByDaysAndPreferenceLoading } =
        useGetInsightsTimeSeriesQuery({
            record_type: RecordType.consent,
            time_interval: INTERVAL,
            group_by: GroupByOptions.preference,
            created_gt: START_DATE,
            created_lt: END_DATE,
        });


    // privacy request aggregate
    const privacyRequestTotal = useMemo(() => privacyRequestByPolicy?.map(i => i.count).reduce((sum, el) => sum + el), [privacyRequestByPolicy]) || 0


    // policy by status bar chart
    const privacyRequestByPolicyBar = useMemo(() => {
        return [
            {
                y: privacyRequestByPolicy?.map(i => i.dsr_policy),
                x: privacyRequestByPolicy?.map(i => i.count),
                type: 'bar',
                orientation: 'h'
            }
        ];
    }, [privacyRequestByPolicy])


    // privacy request by day bar chart
    const privacyRequestsByDayBar = useMemo(() => {
        return [
            {
                y: privacyRequestByDay?.map(i => i.count),
                x: privacyRequestByDay?.map(i => i.Created),
                type: 'bar',
            }
        ];
    }, [privacyRequestByDay])

    //privacy request by day and policy chart
    const privacyRequestByPolicyTimeseries = useMemo(() => {
        // group by policy
        const uniquePolicy = [...new Set(privacyRequestByDayAndPolicy?.map(item => item.dsr_policy))];

        // push a new trace by policy
        const traces: { type: string; mode: string; x: string[]; y: number[]; line: { color: string; }; }[] = []
        uniquePolicy.forEach(policy => {
            const data = privacyRequestByDayAndPolicy?.filter(item => item.dsr_policy === policy)
            traces.push({
                type: "scatter",
                mode: "lines",
                name: policy,
                x: data.map(i => i.Created),
                y: data.map(i => i.count),
            })
        })
        return traces;
    }, [privacyRequestByDayAndPolicy]);


    // consent aggregate
    const consentTotal = useMemo(() => consentByNotice?.map(i => i.count).reduce((sum, el) => sum + el), [consentByNotice]) || 0


    // consent by notice bar chart
    const consentByNoticeBar = useMemo(() => {
        return [
            {
                y: consentByNotice?.map(i => i["Notice title"]),
                x: consentByNotice?.map(i => i.count),
                type: 'bar',
                orientation: 'h'
            }
        ];
    }, [consentByNotice])


    // consent by day bar chart
    const consentByDayBar = useMemo(() => {
        return [
            {
                y: consentByDay?.map(i => i.count),
                x: consentByDay?.map(i => i.Created),
                type: 'bar',
            }
        ];
    }, [consentByDay])


    // consent by preference bar chart
    const consentByPreferenceBar = useMemo(() => {
        return [
            {
                y: consentByPreference?.map(i => i.Preference),
                x: consentByPreference?.map(i => i.count),
                type: 'bar',
                orientation: 'h'
            }
        ];
    }, [consentByPreference])


    // consent by notice type timeseries
    const consentByNoticeTypeTimeseries = useMemo(() => {
        // group by preference
        const uniquePreferenceType = [...new Set(consentByDayAndPreference?.map(item => item.Preference))];

        // push a new trace by Notice title
        const traces: { type: string; mode: string; x: string[]; y: number[]; line: { color: string; }; }[] = []
        uniquePreferenceType.forEach(preferenceType => {
            const dataForPreference = consentByDayAndPreference?.filter(item => item.Preference === preferenceType)
            traces.push({
                type: "scatter",
                mode: "lines",
                name: preferenceType,
                x: dataForPreference.map(i => i.Created),
                y: dataForPreference.map(i => i.count),
            })
        })
        return traces;
    }, [consentByDayAndPreference]);


    /**
     * PLOTLY LAYOUTS
     */
    const layoutBase = {
        autosize: false,
        width: 400,
        height: 200,
        yaxis: {
            showgrid: false,
            zeroline: false,
        },
        xaxis: {
            showgrid: false,
            zeroline: false
        }
    }

    const getBarChartPlotlyLayout = (title?: string): Partial<Plotly.Layout> => {
        return {
            ...layoutBase,
            margin: {
                t: 48,
                l: 160,
                r: 48,
                b: 24,
            },
            title: {
                text: title,
                font: {
                    family: "Inter",
                    size: 16,
                }
            },
        }
    };

    const getTimeSeriesPlotlyLayout = (title?: string): Partial<Plotly.Layout> => {
        return {
            ...layoutBase,
            margin: {
                t: 48,
                l: 48,
                r: 48,
                b: 24,
            },
            yaxis: {
                type: 'linear',
                showgrid: false,
                zeroline: false,
            },
            xaxis: {
                type: 'date',
                tickformat: '%m/%d',
                showgrid: false,
                zeroline: false,
            },
            title: {
                text: title,
                font: {
                    family: "Inter",
                    size: 16,
                }
            },
        }
    }

    return (

        <>
            <Layout title="Insights">
                <div style={SECTION_STYLES}>
                    <Heading {...SECTION_HEADING_PROPS}>
                        {LABEL_REQUESTS_SECTION}
                    </Heading>
                    <hr/>
                    {/* privacy request charts */}
                    <div style={{display: "flex", textAlign: "center"}}>
                        <div style={KPI_STYLES}>
                            {isPrivacyRequestByPolicyLoading && (
                                <Center>
                                    <Spinner />
                                </Center>
                            )}
                            {!isPrivacyRequestByPolicyLoading && (
                                <div style={KPI_VALUE_STYLES}>{privacyRequestTotal}</div>
                            )}
                            <div style={KPI_LABEL_STYLES}>{LABEL_REQUESTS_TOTAL}</div>
                        </div>
                        <div style={CHART_STYLES}>
                            {isPrivacyRequestByPolicyLoading && (
                                <Center>
                                    <Spinner />
                                </Center>
                            )}
                            {!isPrivacyRequestByPolicyLoading && (
                                <Plot
                                    data={privacyRequestByPolicyBar} layout={getBarChartPlotlyLayout(LABEL_REQUESTS_BY_POLICY)}
                                />
                            )}
                        </div>
                        <div style={CHART_STYLES}>
                            {isPrivacyRequestByDayLoading && (
                                <Center>
                                    <Spinner />
                                </Center>
                            )}
                            {!isPrivacyRequestByDayLoading && (
                                <Plot
                                    data={privacyRequestsByDayBar} layout={getTimeSeriesPlotlyLayout(LABEL_REQUESTS_TIMESERIES)}
                                />
                            )}
                        </div>
                    </div>
                    <div style={{display: "flex", textAlign: "center"}}>
                        <div style={KPI_STYLES}>
                        </div>
                        <div style={CHART_STYLES}>
                            {isPrivacyRequestByPolicyLoading && (
                                <Center>
                                    <Spinner />
                                </Center>
                            )}
                            {!isPrivacyRequestByPolicyLoading && (
                                <Plot
                                    data={privacyRequestByPolicyBar} layout={getBarChartPlotlyLayout(LABEL_REQUESTS_BY_POLICY)}
                                />
                            )}
                        </div>
                        <div style={CHART_STYLES}>
                            {isPrivacyRequestByDayAndPolicyLoading && (
                                <Center>
                                    <Spinner />
                                </Center>
                            )}
                            {!isPrivacyRequestByDayAndPolicyLoading && (
                                <Plot
                                    data={privacyRequestByDayAndPolicy} layout={getTimeSeriesPlotlyLayout(LABEL_REQUESTS_TIMESERIES_BY_POLICY)}
                                />
                            )}
                        </div>
                    </div>
                </div>

                <div style={SECTION_STYLES}>
                    <Heading {...SECTION_HEADING_PROPS}>
                        {LABEL_PREFS_SECTION}
                    </Heading>
                    <hr/>

                    {/*row 1 consent*/}
                    <div style={{display: "flex", textAlign: "center"}}>
                        <div style={KPI_STYLES}>
                            {isConsentByNoticeLoading && (
                                <Center>
                                    <Spinner />
                                </Center>
                            )}
                            {!isConsentByNoticeLoading && (
                                <div style={KPI_VALUE_STYLES}>{consentTotal}</div>
                            )}
                            <div style={KPI_LABEL_STYLES}>{LABEL_PREFS_TOTAL}</div>
                        </div>
                        <div style={CHART_STYLES}>
                            {isConsentByNoticeLoading && (
                                <Center>
                                    <Spinner />
                                </Center>
                            )}
                            {!isConsentByNoticeLoading && (
                                <Plot
                                    data={consentByNoticeBar} layout={getBarChartPlotlyLayout(LABEL_PREFS_BY_NOTICE)}
                                />
                            )}
                        </div>
                        <div style={CHART_STYLES}>
                            {isConsentByDayLoading && (
                                <Center>
                                    <Spinner />
                                </Center>
                            )}
                            {!isConsentByDayLoading && (
                                <Plot
                                    data={consentByDayBar} layout={getTimeSeriesPlotlyLayout(LABEL_PREFS_TIMESERIES)}
                                />
                            )}
                        </div>
                    </div>

                    {/*row 2 consent*/}
                    <div style={{display: "flex", textAlign: "center"}}>
                        <div style={KPI_STYLES}>
                        </div>
                        <div style={CHART_STYLES}>
                            {isConsentByPreferenceLoading && (
                                <Center>
                                    <Spinner />
                                </Center>
                            )}
                            {!isConsentByPreferenceLoading && (
                                <Plot
                                    data={consentByPreferenceBar} layout={getBarChartPlotlyLayout(LABEL_PREFS_BY_PREFERENCE)}
                                />
                            )}
                        </div>
                        <div style={CHART_STYLES}>
                            {isConsentByDaysAndPreferenceLoading && (
                                <Center>
                                    <Spinner />
                                </Center>
                            )}
                            {!isConsentByDaysAndPreferenceLoading && (
                                <Plot
                                    data={consentByNoticeTypeTimeseries} layout={getTimeSeriesPlotlyLayout(LABEL_PREFS_TIMESERIES_BY_PREFERENCE)}
                                />
                            )}
                        </div>
                    </div>
                </div>

            </Layout>
        </>
    );
};

export default InsightsPage;