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

const InsightsPage: NextPage = () => {
    const [isLoading, setIsLoading] = useState(true);
    const { data: privacyRequestByPolicy, isLoading: isPrivacyRequestByPolicyLoading } =
        useGetInsightsAggregateQuery({
            record_type: RecordType.dsr,
            // todo- group by policy once that's working
            group_by: GroupByOptions.status,
            created_gt: "2022-12-20T14:20:34.000Z",
            created_lt: "2023-12-22T14:20:34.000Z"
        });
    const { data: privacyRequestByDay, isLoading: isPrivacyRequestByDayLoading } =
        useGetInsightsTimeSeriesQuery({
            record_type: RecordType.dsr,
            time_interval: TimeInterval.days,
            created_gt: "2022-12-20T14:20:34.000Z",
            created_lt: "2023-12-22T14:20:34.000Z"
        });
    const { data: consentByNotice, isLoading: isConsentByNoticeLoading } =
        useGetInsightsAggregateQuery({
            record_type: RecordType.consent,
            group_by: GroupByOptions.notice,
            created_gt: "2023-12-20T14:20:34.000Z",
            created_lt: "2023-12-22T14:20:34.000Z"
        });
    const { data: consentByDay, isLoading: isConsentByDayLoading } =
        useGetInsightsTimeSeriesQuery({
            record_type: RecordType.consent,
            time_interval: TimeInterval.days,
            created_gt: "2023-12-20T14:20:34.000Z",
            created_lt: "2023-12-22T14:20:34.000Z"
        });
    const { data: consentByPreference, isLoading: isConsentByPreferenceLoading } =
        useGetInsightsAggregateQuery({
            record_type: RecordType.consent,
            group_by: GroupByOptions.preference,
            created_gt: "2023-12-20T14:20:34.000Z",
            created_lt: "2023-12-22T14:20:34.000Z"
        });
    const { data: consentByDayAndPreference, isLoading: isConsentByDaysAndPreferenceLoading } =
        useGetInsightsTimeSeriesQuery({
            record_type: RecordType.consent,
            time_interval: TimeInterval.days,
            group_by: GroupByOptions.preference,
            created_gt: "2023-12-20T14:20:34.000Z",
            created_lt: "2023-12-22T14:20:34.000Z"
        });

    useEffect(() => {


        setIsLoading(false);

    },[])




    const privacyRequestPolicyAction = [{
        "Notice title": "Access",
        "count": 5
    }, {
        "Notice title": "Erasure",
        "count": 2
    }, {
        "Notice title": "Consent",
        "count": 10
    },
    ]

    // privacy requests by notice type bar
    const privacyRequestsPolicyActionBar = [
        {
            y: privacyRequestPolicyAction.map(i => i["Notice title"]),
            x: privacyRequestPolicyAction.map(i => i.count),
            type: 'bar',
            orientation: 'h'
        }
    ];


    // privacy request aggregate
    const privacyRequestTotal = useMemo(() => privacyRequestByPolicy?.map(i => i.count).reduce((sum, el) => sum + el), [privacyRequestByPolicy])


    // policy by status bar chart
    const privacyRequestByPolicyBar = useMemo(() => {
        return [
            {
                // todo- change to "policy"
                y: privacyRequestByPolicy?.map(i => i.status),
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

    // consent aggregate
    const consentTotal = useMemo(() => consentByNotice?.map(i => i.count).reduce((sum, el) => sum + el), [consentByNotice])


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



    const layoutBase = {
        autosize: false,
        width: 450,
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

    const layoutHorizontalBar = {
        ... layoutBase,
        margin: {
            t: 20,
            l: 80,
            r: 50,
            b: 20
        },
    }

    const layoutTimeSeriesBar = {
        ... layoutBase,
        margin: {
            t: 20,
            l: 50,
            r: 50,
            b: 20
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
        }
    }

    const layoutTimeSeriesLine = {
        ... layoutBase,
        margin: {
            t: 20,
            l: 50,
            r: 50,
            b: 20
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
        }
    }

    return (

        <>
            {isLoading && (
                <Layout title="Insights">
                    <Center>
                        <Spinner />
                    </Center>
                </Layout>
            )}
            {!isLoading && (
                <Layout title="Insights">
                    <div style={{paddingBottom: "50px"}}>
                        <Heading style={{marginBottom: "10px"}} mb={8} fontSize="2xl" fontWeight="semibold">
                            Privacy Requests
                        </Heading>
                        <hr/>
                        {/* privacy request charts */}
                        <div style={{display: "flex", textAlign: "center"}}>
                            <div style={{flex: 1, position: "relative"}}>
                                <Heading style={{paddingTop:"50px", marginBottom: 0}} mb={8} fontSize="7xl" fontWeight="semibold">
                                    {privacyRequestTotal}
                                </Heading>
                                <Heading style={{position: "absolute",
                                    bottom: 0,
                                    textAlign: "center",
                                    marginLeft: "auto",
                                    marginRight: "auto",
                                    left: 0,
                                    right: 0}} mb={8} fontSize="2xl" fontWeight="normal">
                                    Total Requests
                                </Heading>
                            </div>
                            <div style={{flex: 2}}>
                                <Plot
                                    data={privacyRequestByPolicyBar} layout={layoutHorizontalBar}
                                />
                            </div>
                            <div style={{flex: 2}}>
                                <Plot
                                    data={privacyRequestsByDayBar} layout={layoutTimeSeriesBar}
                                />
                            </div>
                        </div>

                        {/* privacy request chart labels */}
                        <div style={{display: "flex"}}>
                            <div style={{flex: 1}}>
                                <div>Number of requests created in report period</div>
                            </div>
                            <div style={{flex: 2}}>
                                <div>Number of requests created in report period by policy action</div>
                            </div>
                            <div style={{flex: 2}}>
                                <div>Number of requests per day created in report period</div>
                            </div>

                        </div>
                    </div>

                    <div style={{paddingBottom: "50px"}}>
                        <Heading style={{marginBottom: "10px"}} mb={8} fontSize="2xl" fontWeight="semibold">
                            Consent
                        </Heading>
                        <hr/>

                        {/*row 1 consent*/}
                        <div style={{display: "flex", textAlign: "center"}}>
                            <div style={{flex: 1, position: "relative"}}>
                                <Heading style={{paddingTop:"50px", marginBottom: 0}} mb={8} fontSize="7xl" fontWeight="semibold">
                                    {consentTotal}
                                </Heading>
                                <Heading style={{position: "absolute",
                                    bottom: 0,
                                    textAlign: "center",
                                    marginLeft: "auto",
                                    marginRight: "auto",
                                    left: 0,
                                    right: 0}} mb={8} fontSize="2xl" fontWeight="normal">
                                    Total Preferences
                                </Heading>
                            </div>
                            <div style={{flex: 2}}>
                                <Plot
                                    data={consentByNoticeBar} layout={layoutHorizontalBar}
                                />
                            </div>
                            <div style={{flex: 2}}>
                                <Plot
                                    data={consentByDayBar} layout={layoutTimeSeriesBar}
                                />
                            </div>
                        </div>

                        {/* row 1 consent chart labels */}
                        <div style={{display: "flex"}}>
                            <div style={{flex: 1}}>
                                <div>Number of preferences created in report period</div>
                            </div>
                            <div style={{flex: 2}}>
                                <div>Number of preferences created in report period by notice</div>
                            </div>
                            <div style={{flex: 2}}>
                                <div>Number of preferences per day created in report period</div>
                            </div>

                        </div>

                        {/*row 2 consent*/}
                        <div style={{display: "flex", textAlign: "center"}}>
                            <div style={{flex: 1, position: "relative"}}>
                            </div>
                            <div style={{flex: 2}}>
                                <Plot
                                    data={consentByPreferenceBar} layout={layoutHorizontalBar}
                                />
                            </div>
                            <div style={{flex: 2}}>
                                <Plot
                                    data={consentByNoticeTypeTimeseries} layout={layoutTimeSeriesLine}
                                />
                            </div>
                        </div>

                        {/* row 2 consent chart labels */}
                        <div style={{display: "flex"}}>
                            <div style={{flex: 1}}>
                            </div>
                            <div style={{flex: 2}}>
                                <div>Number of preferences created in report period by preference value</div>
                            </div>
                            <div style={{flex: 2}}>
                                <div>Number of preferences per day created in report period by preference value</div>
                            </div>

                        </div>
                    </div>

                </Layout>
            )}
        </>
    );
};

export default InsightsPage;