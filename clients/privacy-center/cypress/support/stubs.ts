import { hostUrl } from "~/constants";

export const stubIdVerification = () => {
  cy.intercept("GET", `${hostUrl}/id-verification/config`, {
    body: {
      identity_verification_required: true,
    },
  }).as("getVerificationConfig");
};
