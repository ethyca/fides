import palette from "fidesui/src/palette/palette.module.scss";

import type { DashboardData } from "../types";

/**
 * Dummy data for dashboard
 * TODO: Remove when real API integration is complete
 */
export const dummyDashboardData: DashboardData = {
  summary: {
    privacyRequests: {
      total: 480000,
      totalLabel: "Due Soon",
      breakdown: [
        { label: "New", value: 120000, color: palette.FIDESUI_INFO },
        { label: "In Progress", value: 120000, color: palette.FIDESUI_WARNING },
        { label: "Pending Review", value: 120000, color: palette.FIDESUI_NEUTRAL_700 },
        { label: "Errors", value: 120000, color: palette.FIDESUI_ERROR },
      ],
    },
    systemDetection: {
      total: 253,
      totalLabel: "System Assets",
      breakdown: [
        { label: "Classified", value: 240, color: palette.FIDESUI_SUCCESS },
        { label: "In Review", value: 50, color: palette.FIDESUI_WARNING },
        { label: "Unknown", value: 13, color: palette.FIDESUI_NEUTRAL_400 },
      ],
    },
    dataClassification: {
      total: 3000,
      totalLabel: "Data Assets",
      breakdown: [
        { label: "Data Classified", value: 1900, color: palette.FIDESUI_SUCCESS },
        { label: "In Review", value: 1523, color: palette.FIDESUI_WARNING },
        { label: "Personal Data", value: 1750, color: palette.FIDESUI_INFO },
        { label: "Unlabeled", value: 1100, color: palette.FIDESUI_NEUTRAL_400 },
      ],
    },
  },
  consentCategories: {
    timeRange: "30 days",
    categories: [
      {
        category: "Marketing",
        value: 15112893,
        change: -112893,
        // Declining trend with some variation
        trendData: [15200000, 15180000, 15160000, 15140000, 15120000, 15112893],
      },
      {
        category: "Data Sharing",
        value: 15112893,
        change: 112893,
        // Increasing trend with variation (squiggly up)
        trendData: [15000000, 15050000, 15020000, 15080000, 15040000, 15112893],
      },
      {
        category: "Analytics",
        value: 15112893,
        change: -112893,
        // Declining trend with more variation (squiggly down)
        trendData: [15200000, 15150000, 15180000, 15130000, 15160000, 15112893],
      },
      {
        category: "Consent Category",
        value: 15112893,
        change: 112893,
        // Increasing trend with variation
        trendData: [15000000, 15030000, 15010000, 15070000, 15050000, 15112893],
      },
      {
        category: "Consent Category",
        value: 15112893,
        change: 112893,
        // More squiggly increasing trend
        trendData: [15000000, 15060000, 15020000, 15090000, 15040000, 15112893],
      },
    ],
  },
  dataClassification: {
    systems: [
      {
        systemName: "Website Monitor",
        categories: [
          { name: "User.contact.email", value: 400, fill: palette.FIDESUI_SANDSTONE },
          { name: "User.contact.phone", value: 350, fill: palette.FIDESUI_NECTAR },
          { name: "User.demographic.age", value: 300, fill: palette.FIDESUI_LIMESTONE },
          { name: "User.demographic.gender", value: 280, fill: palette.FIDESUI_TERRACOTTA },
          { name: "User.location", value: 250, fill: palette.FIDESUI_SANDSTONE },
          { name: "User.unique_id", value: 220, fill: palette.FIDESUI_NECTAR },
          { name: "User.device.cookie_id", value: 200, fill: palette.FIDESUI_LIMESTONE },
          { name: "User.browser", value: 180, fill: palette.FIDESUI_TERRACOTTA },
        ],
      },
      {
        systemName: "BigQuery Warehouse",
        categories: [
          { name: "User.contact.email", value: 450, fill: palette.FIDESUI_SANDSTONE },
          { name: "User.contact.phone", value: 380, fill: palette.FIDESUI_NECTAR },
          { name: "User.demographic.age", value: 320, fill: palette.FIDESUI_LIMESTONE },
          { name: "User.demographic.gender", value: 290, fill: palette.FIDESUI_TERRACOTTA },
          { name: "User.location", value: 270, fill: palette.FIDESUI_SANDSTONE },
          { name: "User.unique_id", value: 240, fill: palette.FIDESUI_NECTAR },
          { name: "User.device.cookie_id", value: 210, fill: palette.FIDESUI_LIMESTONE },
          { name: "User.browser", value: 190, fill: palette.FIDESUI_TERRACOTTA },
        ],
      },
      {
        systemName: "Amazon S3",
        categories: [
          { name: "User.contact.email", value: 420, fill: palette.FIDESUI_SANDSTONE },
          { name: "User.contact.phone", value: 360, fill: palette.FIDESUI_NECTAR },
          { name: "User.demographic.age", value: 310, fill: palette.FIDESUI_LIMESTONE },
          { name: "User.demographic.gender", value: 285, fill: palette.FIDESUI_TERRACOTTA },
          { name: "User.location", value: 260, fill: palette.FIDESUI_SANDSTONE },
          { name: "User.unique_id", value: 230, fill: palette.FIDESUI_NECTAR },
          { name: "User.device.cookie_id", value: 205, fill: palette.FIDESUI_LIMESTONE },
          { name: "User.browser", value: 185, fill: palette.FIDESUI_TERRACOTTA },
        ],
      },
    ],
  },
  helios: {
    discoveredFields: [
      { name: "Unlabeled", value: 450, color: palette.FIDESUI_NEUTRAL_400 },
      { name: "In review", value: 320, color: palette.FIDESUI_WARNING },
      { name: "Approved", value: 280, color: palette.FIDESUI_SUCCESS },
      { name: "Confirmed", value: 150, color: palette.FIDESUI_INFO },
    ],
    classificationActivity: [
      { date: "2024-01", discovered: 120, reviewed: 80, approved: 60 },
      { date: "2024-02", discovered: 150, reviewed: 110, approved: 90 },
      { date: "2024-03", discovered: 180, reviewed: 140, approved: 100 },
      { date: "2024-04", discovered: 200, reviewed: 160, approved: 130 },
      { date: "2024-05", discovered: 220, reviewed: 180, approved: 150 },
      { date: "2024-06", discovered: 250, reviewed: 200, approved: 180 },
    ],
    dataCategories: [
      { name: "User.contact.email", value: 400, fill: palette.FIDESUI_INFO },
      {
        name: "User.contact.phone",
        value: 350,
        fill: palette.FIDESUI_SUCCESS,
      },
      {
        name: "User.demographic.age",
        value: 300,
        fill: palette.FIDESUI_WARNING,
      },
      {
        name: "User.demographic.gender",
        value: 280,
        fill: palette.FIDESUI_TERRACOTTA,
      },
      { name: "User.location", value: 250, fill: palette.FIDESUI_OLIVE },
      {
        name: "User.unique_id",
        value: 220,
        fill: palette.FIDESUI_SANDSTONE,
      },
      {
        name: "User.device.cookie_id",
        value: 200,
        fill: palette.FIDESUI_MARBLE,
      },
      { name: "User.browser", value: 180, fill: palette.FIDESUI_NECTAR },
    ],
  },
  janus: {
    consentRates: [
      { date: "2024-01", optIn: 65, optOut: 35 },
      { date: "2024-02", optIn: 68, optOut: 32 },
      { date: "2024-03", optIn: 70, optOut: 30 },
      { date: "2024-04", optIn: 72, optOut: 28 },
      { date: "2024-05", optIn: 74, optOut: 26 },
      { date: "2024-06", optIn: 75, optOut: 25 },
    ],
  },
  lethe: {
    privacyRequestsNeedingApproval: 12,
    pendingManualTasks: 8,
  },
};
