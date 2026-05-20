/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import { mockPrivacyAssessmentsResponse } from "./data";

export const privacyAssessmentsHandlers = () => {
  const apiBase = "/api/v1";
  const plusBase = `${apiBase}/plus`;

  return [
    rest.get(`${plusBase}/privacy-assessments`, (_req, res, ctx) =>
      res(ctx.status(200), ctx.json(mockPrivacyAssessmentsResponse)),
    ),
  ];
};
