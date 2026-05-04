export interface DimensionTrend {
  points: number[];
  delta: number;
}

export const TREND_DATA: Record<string, DimensionTrend> = {
  Coverage: {
    points: [62, 64, 63, 66, 68, 70, 69, 72, 74, 76, 77, 78],
    delta: 4,
  },
  "Classification Health": {
    points: [70, 71, 69, 68, 67, 65, 66, 64, 63, 64, 64, 64],
    delta: -3,
  },
  "Consent Alignment": {
    points: [74, 75, 76, 78, 77, 79, 80, 80, 81, 81, 82, 82],
    delta: 2,
  },
  "DSR Compliance": {
    points: [65, 66, 67, 68, 69, 70, 70, 71, 71, 72, 71, 71],
    delta: 1,
  },
  "Policy Enforcement": {
    points: [62, 60, 58, 60, 59, 57, 58, 56, 57, 58, 58, 58],
    delta: -2,
  },
  "AI Readiness": {
    points: [55, 53, 50, 48, 46, 45, 44, 43, 43, 42, 42, 42],
    delta: -8,
  },
  "Assessment Coverage": {
    points: [60, 62, 63, 64, 65, 66, 67, 68, 68, 69, 69, 69],
    delta: 5,
  },
};
