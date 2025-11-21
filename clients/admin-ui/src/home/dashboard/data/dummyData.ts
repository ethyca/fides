import palette from "fidesui/src/palette/palette.module.scss";

import type { DashboardData } from "../types";

/**
 * Dummy data for dashboard
 * TODO: Remove when real API integration is complete
 */
export const dummyDashboardData: DashboardData = {
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

