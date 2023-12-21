import {Center, Heading, Spinner} from "@fidesui/react";
import type { NextPage } from "next";
import dynamic from "next/dynamic";
import React, {useEffect, useMemo, useState} from "react";

import Layout from "~/features/common/Layout";
import {useGetAnalyticsAggregateQuery, useGetAnalyticsTimeSeriesQuery} from "~/features/plus/plus.slice";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false, })

const InsightsPage: NextPage = () => {
    const [isLoading, setIsLoading] = useState(true);
    // const { data: consentSeries, isLoading: isConsentSeriesLoading } =
    //     useGetAnalyticsAggregateQuery({
    //         record_type: "consent",
    //         time_interval: "days",
    //         group_by: "notice",
    //         created_gt: "2023-12-20T14:20:34.000Z",
    //         created_lt: "2023-12-22T14:20:34.000Z "
    //     });
    const { data: consentSeries, isLoading: isConsentSeriesLoading } =
        useGetAnalyticsTimeSeriesQuery({
            record_type: "consent",
            time_interval: "seconds",
            group_by: "notice",
            created_gt: "2023-12-20T14:20:34.000Z",
            created_lt: "2023-12-22T14:20:34.000Z"
        });

    useEffect(() => {


        setIsLoading(false);

    },[])



    // Aggregate endpoint api/v1/plus/analytics/aggregate
    // response body example:
    const privacyRequestPolicyAction = [{
        "Notice_title": "Access",
        "count": 5
    }, {
        "Notice_title": "Erasure",
        "count": 2
    }, {
        "Notice_title": "Consent",
        "count": 10
    },
    ]

    // privacy requests by notice type bar
    const privacyRequestsPolicyActionBar = [
        {
            y: privacyRequestPolicyAction.map(i => i.Notice_title),
            x: privacyRequestPolicyAction.map(i => i.count),
            type: 'bar',
            orientation: 'h'
        }
    ];


    const privacyRequestSeries = [{
        "Created": "2013-10-05 22:34:00",
        "count": 5
    }, {
        "Created": "2013-10-05 22:32:00",
        "count": 7
    },{
        "Created": "2013-10-06 10:32:00",
        "count": 1
    }, {
        "Created": "2013-10-06 22:32:00",
        "count": 3
    },{
        "Created": "2013-10-07 08:32:00",
        "count": 3
    }, {
        "Created": "2013-10-07 06:32:00",
        "count": 5
    }];


    // requests per day bar chart
    const privacyRequestsByDayBar = [
        {
            y: privacyRequestSeries.map(i => i.Created),
            x: privacyRequestSeries.map(i => i.count),
            type: 'bar',
        }
    ];

    // todo- get from endpoint
    // Time series endpoint: api/v1/plus/analytics/time-series?record_type=consent&time_interval=days&group_by=notice&created_gt=2023-12-20T14:20:34.000Z&created_lt=2023-12-22T14:20:34.000Z
    // response body example:
    // const consentSeries = [{
    //     "Created": "2013-10-05 22:34:00",
    //     "Notice_title": "Essential",
    //     "count": 1
    // }, {
    //     "Created": "2013-10-05 22:32:00",
    //     "Notice_title": "Data Sales",
    //     "count": 1
    // },{
    //     "Created": "2013-10-06 10:32:00",
    //     "Notice_title": "Essential",
    //     "count": 2
    // }, {
    //     "Created": "2013-10-06 22:32:00",
    //     "Notice_title": "Data Sales",
    //     "count": 2
    // },{
    //     "Created": "2013-10-07 08:32:00",
    //     "Notice_title": "Essential",
    //     "count": 4
    // }, {
    //     "Created": "2013-10-07 06:32:00",
    //     "Notice_title": "Data Sales",
    //     "count": 2
    // }];


    const consentByNoticeTypeTimeseries = useMemo(() => {
        // group by notice
        const uniqueNotices = [...new Set(consentSeries?.map(item => item.Notice_title))];

        // push a new trace by Notice title
        const traces: { type: string; mode: string; x: string[]; y: number[]; line: { color: string; }; }[] = []
        uniqueNotices.forEach(uniqueNoticeTitle => {
            const dataForNotice = consentSeries?.filter(item => item.Notice_title === uniqueNoticeTitle)
            traces.push({
                type: "scatter",
                mode: "lines",
                name: uniqueNoticeTitle,
                x: dataForNotice.map(i => i.Created),
                y: dataForNotice.map(i => i.count),
            })
        })
        return traces;
    }, [consentSeries]);



    const layoutBase = {
        autosize: false,
        width: 450,
        height: 200,

        yaxis: {
            "showgrid": false,
            "zeroline": false
        },
        xaxis: {
            "showgrid": false,
            "zeroline": false
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

    const layoutTimeSeries = {
        ... layoutBase,
        margin: {
            t: 20,
            l: 50,
            r: 50,
            b: 20
        },
        xaxis: {
            type: 'date',
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
                                    130
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
                                    data={privacyRequestsPolicyActionBar} layout={layoutHorizontalBar}
                                />
                            </div>
                            <div style={{flex: 2}}>
                                <Plot
                                    data={privacyRequestsByDayBar} layout={layoutTimeSeries}
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
                        {/* consent charts */}
                        <div style={{display: "flex", textAlign: "center"}}>
                            <div style={{flex: 1, position: "relative"}}>
                                <Heading style={{paddingTop:"50px", marginBottom: 0}} mb={8} fontSize="7xl" fontWeight="semibold">
                                    14,098
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
                                    data={privacyRequestsPolicyActionBar} layout={layoutHorizontalBar}
                                />
                            </div>
                            <div style={{flex: 2}}>
                                <Plot
                                    data={consentByNoticeTypeTimeseries} layout={layoutTimeSeries}
                                />
                            </div>
                        </div>

                        {/* consent chart labels */}
                        <div style={{display: "flex"}}>
                            <div style={{flex: 1}}>
                                <div>Number of requests created in report period</div>
                            </div>
                            <div style={{flex: 2}}>
                                <div>Number of requests created in report period by policy action</div>
                            </div>
                            <div style={{flex: 2}}>
                                <div>Privacy requests by notice type</div>
                            </div>

                        </div>
                    </div>

                </Layout>
            )}
        </>
    );
};

export default InsightsPage;