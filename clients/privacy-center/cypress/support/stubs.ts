import { API_URL } from "./constants";

export const stubIdVerification = () => {
  cy.intercept("GET", `${API_URL}/id-verification/config`, {
    body: {
      identity_verification_required: true,
    },
  }).as("getVerificationConfig");
};
