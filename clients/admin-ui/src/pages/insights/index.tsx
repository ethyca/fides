import {Box, Center, Flex, Heading, Spinner} from "@fidesui/react";
import type { NextPage } from "next";
import dynamic from "next/dynamic";
import React, {useEffect, useMemo, useState} from "react";

import Layout from "~/features/common/Layout";
import {
    useGetInsightsAggregateQuery,
    useGetInsightsTimeSeriesQuery
} from "~/features/plus/plus.slice";
import {GroupByOptions, RecordType, TimeInterval} from "~/types/api/models/InsightsRequestParams";
import SelectDropdown from "common/dropdown/SelectDropdown";
import {ItemOption} from "common/dropdown/types";
import {ConnectorParameterOption} from "datastore-connections/add-connection/types";
import {CONNECTOR_PARAMETERS_OPTIONS, STEPS} from "datastore-connections/add-connection/constants";
import {reset, setStep} from "~/features/connection-type";
import {setTestingStatus} from "~/features/datastore-connections";

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

const GEO_STYLES: React.CSSProperties = {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    minWidth: 460,
    minHeight: 220,
    flex: 1,
    padding: 8,
    margin: 8,
    border: "1px solid #eee",
    borderRadius: "4px",
}

/**
 * LABELS
 */
const INTERVAL = TimeInterval.weeks;
const LABEL_INTERVAL = "Weekly";

const LABEL_SETTINGS_SECTION = "Dashboard";

const LABEL_REQUESTS_SECTION = "Privacy Requests";
const LABEL_REQUESTS_TOTAL = "Total Privacy Requests";
const LABEL_REQUESTS_BY_POLICY = "Privacy Requests by Policy";
const LABEL_REQUESTS_BY_STATUS = "Privacy Requests by Status";
const LABEL_REQUESTS_TIMESERIES = "Privacy Requests";
const LABEL_REQUESTS_TIMESERIES_BY_POLICY = "Privacy Requests by Policy";

const LABEL_PREFS_SECTION = "Consent Preferences";
const LABEL_PREFS_TOTAL = "Total Preferences";
const LABEL_PREFS_BY_NOTICE = "Preferences by Notice";
const LABEL_PREFS_TIMESERIES = "Preferences";
const LABEL_PREFS_BY_PREFERENCE = "Preferences by Value";
const LABEL_PREFS_TIMESERIES_BY_PREFERENCE = "Preferences by Value";

const InsightsPage: NextPage = () => {

    type DateRange = {
        label: string;
        value: string;
        startDate: string;
        endDate: string;
    }

    // need to map selected date val to end and start dates
    const dateRangeMap = new Map<string, DateRange>();
    const today = new Date()
    const todayFormatted = today.toISOString()
    const prior30DaysDate = new Date(new Date().setDate(today.getDate() - 30)).toISOString()
    const prior90DaysDate = new Date(new Date().setDate(today.getDate() - 90)).toISOString()
    const prior180DaysDate = new Date(new Date().setDate(today.getDate() - 180)).toISOString()
    const prior365DaysDate = new Date(new Date().setDate(today.getDate() - 365)).toISOString()
    dateRangeMap.set("30", {label: "Last 30 days", value: "30", endDate: todayFormatted, startDate: prior30DaysDate})
    dateRangeMap.set("90", {label: "Last 90 days", value: "90", endDate: todayFormatted, startDate: prior90DaysDate})
    dateRangeMap.set("180", {label: "Last 180 days", value: "180", endDate: todayFormatted, startDate: prior180DaysDate})
    dateRangeMap.set("365", {label: "Last year", value: "365", endDate: todayFormatted, startDate: prior365DaysDate})

    // options for the date selector
    const dateRangeOptions: Map<string, ItemOption> = new Map<string, ItemOption>();
    dateRangeOptions.set("Last 30 days", {value: "30"})
    dateRangeOptions.set("Last 90 days", {value: "90"})
    dateRangeOptions.set("Last 180 days", {value: "180"})
    dateRangeOptions.set("Last year", {value: "365"})

    const [dateRange, setDateRange] = useState(
        dateRangeMap.get("180")
    );

    const intervalOptions: Map<string, ItemOption> = new Map<string, ItemOption>([
        ["Daily", { value: TimeInterval.days }],
        ["Weekly", { value: TimeInterval.weeks }],
        ["Monthly", { value: TimeInterval.months }],
    ]);
    const [interval, setInterval] = useState(TimeInterval.weeks);
    const handleIntervalChange = (value?: string) => {
        console.log("handleIntervalChange", value);
        if (value) {
            setInterval(value);
        }
    };

    const { data: privacyRequestByPolicy, isLoading: isPrivacyRequestByPolicyLoading } =
        useGetInsightsAggregateQuery({
            record_type: RecordType.dsr,
            group_by: GroupByOptions.dsr_policy,
            created_gt: dateRange.startDate,
            created_lt: dateRange.endDate,
        });
    const { data: privacyRequestByStatus, isLoading: isPrivacyRequestByStatusLoading } =
        useGetInsightsAggregateQuery({
            record_type: RecordType.dsr,
            group_by: GroupByOptions.status,
            created_gt: dateRange.startDate,
            created_lt: dateRange.endDate,
        });
    const { data: privacyRequestByDay, isLoading: isPrivacyRequestByDayLoading } =
        useGetInsightsTimeSeriesQuery({
            record_type: RecordType.dsr,
            time_interval: interval,
            created_gt: dateRange.startDate,
            created_lt: dateRange.endDate,
        });
    const { data: privacyRequestByDayAndPolicy, isLoading: isPrivacyRequestByDayAndPolicyLoading } =
        useGetInsightsTimeSeriesQuery({
            record_type: RecordType.dsr,
            group_by: GroupByOptions.dsr_policy,
            time_interval: interval,
            created_gt: dateRange.startDate,
            created_lt: dateRange.endDate,
        });
    const { data: consentByNotice, isLoading: isConsentByNoticeLoading } =
        useGetInsightsAggregateQuery({
            record_type: RecordType.consent,
            group_by: GroupByOptions.notice,
            created_gt: dateRange.startDate,
            created_lt: dateRange.endDate,
        });
    const { data: consentByDay, isLoading: isConsentByDayLoading } =
        useGetInsightsTimeSeriesQuery({
            record_type: RecordType.consent,
            time_interval: interval,
            created_gt: dateRange.startDate,
            created_lt: dateRange.endDate,
        });
    const { data: consentByPreference, isLoading: isConsentByPreferenceLoading } =
        useGetInsightsAggregateQuery({
            record_type: RecordType.consent,
            group_by: GroupByOptions.preference,
            created_gt: dateRange.startDate,
            created_lt: dateRange.endDate,
        });
    const { data: consentByDayAndPreference, isLoading: isConsentByDaysAndPreferenceLoading } =
        useGetInsightsTimeSeriesQuery({
            record_type: RecordType.consent,
            time_interval: interval,
            group_by: GroupByOptions.preference,
            created_gt: dateRange.startDate,
            created_lt: dateRange.endDate,
        });
    const { data: consentByCountry, isLoading: isConsentByCountryLoading } =
        useGetInsightsAggregateQuery({
            record_type: RecordType.consent,
            group_by: GroupByOptions.country,
            created_gt: dateRange.startDate,
            created_lt: dateRange.endDate,
        });

    // handle date range change
    const handleDateChange = (value?: string) => {
        if (value) {
            setDateRange(dateRangeMap.get(value))
        }
    };

    // privacy request aggregate
    const privacyRequestTotal = useMemo(() => privacyRequestByPolicy?.map(i => i.count)?.reduce((sum, el) => sum + el), [privacyRequestByPolicy]) || 0


    // privacy request by policy bar chart
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

    // privacy request by status bar chart
    const privacyRequestByStatusBar = useMemo(() => {
        return [
            {
                y: privacyRequestByStatus?.map(i => i.status),
                x: privacyRequestByStatus?.map(i => i.count),
                type: 'bar',
                orientation: 'h'
            }
        ];
    }, [privacyRequestByStatus])


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

    // consent by country map
    const consentByCountryMap = useMemo(() => {
        const onlyUS = consentByCountry?.filter(consent => {
            return consent && consent["User geography"]?.length < 3
        })
        const usLocations = onlyUS?.map(i => i["User geography"])
        const usSize = onlyUS?.map(i => i.count)
        return [{
            type: 'scattergeo',
            mode: 'markers',
            locationmode: 'USA-states',
            locations: usLocations,
            marker: {
                size: usSize,
                sizemode: 'diameter',
                sizeref: 100,
                cmin: 0,
                cmax: 10000,
                line: {
                    color: 'black'
                }
            },
            name: 'world consent'
        }];
    }, [consentByCountry])



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

    const geoLayout = {
        geo: {
            scope: 'usa',
            resolution: 100
        },
        title: {
            text: "Preferences by US State",
            font: {
                family: "Inter",
                size: 16,
            }
        },
    };

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
            legend: {
                x: 1,
                y: 1,
                xanchor: "right",
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
                    <Flex justifyContent="center" alignItems="center" mb={1}>
                        <Box flex={1}>
                            <Heading {...SECTION_HEADING_PROPS}>
                                {LABEL_SETTINGS_SECTION}
                            </Heading>
                        </Box>
                        <Box fontSize="sm" mr={1}>
                            Date Range:
                        </Box>
                        <Box mr={2}>
                            <SelectDropdown
                                label={dateRange.label}
                                list={dateRangeOptions}
                                hasClear={false}
                                menuButtonProps={{  }}
                                onChange={handleDateChange}
                                selectedValue={dateRange.value}
                            />
                        </Box>
                        <Box fontSize="sm" mr={1}>
                            Interval:
                        </Box>
                        <Box>
                            <SelectDropdown
                                list={intervalOptions}
                                hasClear={false}
                                menuButtonProps={{  }}
                                onChange={handleIntervalChange}
                                selectedValue={interval}
                            />
                        </Box>
                    </Flex>
                </div>
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
                        <div style={CHART_STYLES}>
                            {isPrivacyRequestByStatusLoading && (
                                <Center>
                                    <Spinner />
                                </Center>
                            )}
                            {!isPrivacyRequestByStatusLoading && (
                                <Plot
                                    data={privacyRequestByStatusBar} layout={getBarChartPlotlyLayout(LABEL_REQUESTS_BY_STATUS)}
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
                                    data={privacyRequestByPolicyTimeseries} layout={getTimeSeriesPlotlyLayout(LABEL_REQUESTS_TIMESERIES_BY_POLICY)}
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

                    {/*row 3 consent*/}
                    <div style={{display: "flex", textAlign: "center"}}>
                        <div style={GEO_STYLES}>
                            {isConsentByCountryLoading && (
                                <Center>
                                    <Spinner />
                                </Center>
                            )}
                            {!isConsentByCountryLoading && (
                                <Plot
                                    data={consentByCountryMap} layout={geoLayout}
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