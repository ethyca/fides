/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import { computeSummary } from "./compute-summary";
import { mockAssessmentGroups } from "./data";

export const privacyAssessmentsHandlers = () => {
  const apiBase = "/api/v1";

  return [
    rest.get(`${apiBase}/plus/privacy-assessments/summary`, (_req, res, ctx) =>
      res(ctx.status(200), ctx.json(computeSummary(mockAssessmentGroups))),
    ),
  ];
};
