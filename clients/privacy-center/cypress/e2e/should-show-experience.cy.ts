import {
  CONSENT_COOKIE_NAME,
  NoticeConsent,
  PrivacyExperience,
} from "fides-js";

import { mockCookie } from "../support/mocks";
import { OVERRIDE, stubConfig, stubTCFExperience } from "../support/stubs";

describe("Fides.shouldShowExperience()", () => {
  interface TestCaseOptions {
    fixture:
      | "experience_modal.json"
      | "experience_banner_modal.json"
      | "experience_tcf_minimal.json"
      | "experience_none.json";
    savedConsent: boolean;
    expiredTcfVersionHash?: boolean;
    shouldShowExperience: boolean;
  }

  const testCases: TestCaseOptions[] = [
    {
      fixture: "experience_modal.json",
      savedConsent: false,
      shouldShowExperience: false,
    },
    {
      fixture: "experience_modal.json",
      savedConsent: true,
      shouldShowExperience: false,
    },
    {
      fixture: "experience_banner_modal.json",
      savedConsent: false,
      shouldShowExperience: true,
    },
    {
      fixture: "experience_banner_modal.json",
      savedConsent: true,
      shouldShowExperience: false,
    },
    {
      fixture: "experience_tcf_minimal.json",
      savedConsent: false,
      shouldShowExperience: true,
    },
    {
      fixture: "experience_tcf_minimal.json",
      savedConsent: true,
      shouldShowExperience: false,
    },
    {
      fixture: "experience_tcf_minimal.json",
      savedConsent: true,
      expiredTcfVersionHash: true,
      shouldShowExperience: true,
    },
    {
      fixture: "experience_none.json",
      savedConsent: false,
      shouldShowExperience: false,
    },
    {
      fixture: "experience_none.json",
      savedConsent: true,
      shouldShowExperience: false,
    },
  ];

  testCases.forEach(
    ({
      fixture,
      savedConsent,
      expiredTcfVersionHash,
      shouldShowExperience,
    }) => {
      describe(`when rendering ${fixture} and saved consent ${savedConsent ? "exists" : "does not exist"} ${expiredTcfVersionHash ? "(with expired tcf_version_hash)" : ""}`, () => {
        it(`Fides.shouldShowExperience() returns ${shouldShowExperience}`, () => {
          cy.fixture(`consent/${fixture}`).then((data) => {
            let experience: PrivacyExperience = data.items[0] || OVERRIDE.EMPTY;
            const tcfEnabled = /tcf/.test(fixture);

            // If the test requires it, generate and save a prior consent cookie
            if (savedConsent) {
              // Mock an opt-out consent for each notice, plus an "example" other notice
              const notices = [
                ...(experience.privacy_notices || []),
                ...[{ notice_key: "example" }],
              ];
              const consent: NoticeConsent = Object.fromEntries(
                notices.map((e) => [e.notice_key, false]),
              );

              // Mock a saved fides_string if tcf is enabled
              const fides_string = tcfEnabled
                ? "CPzevcAPzevcAGXABBENATEIAAIAAAAAAAAAAAAAAAAA"
                : undefined;

              // Save a tcf_version_hash that matches the experience
              let tcf_version_hash = experience.meta?.version_hash;

              // Mock an "expired" hash, if the test demands it
              if (expiredTcfVersionHash) {
                tcf_version_hash = "1a2a3a";
              }

              // Save the mock cookie
              const cookie = mockCookie({
                consent,
                fides_string,
                tcf_version_hash,
              });
              cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));
            }

            // Load the demo page with our stubbed config
            cy.log("using experience = ", experience);
            if (!tcfEnabled) {
              stubConfig({ experience, options: { isOverlayEnabled: true } });
            } else {
              stubTCFExperience({});
            }
          });
          cy.waitUntilFidesInitialized();

          // Check that our test saved the consent cookie correctly
          if (savedConsent) {
            cy.getCookie(CONSENT_COOKIE_NAME).should("exist");
          } else {
            cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
          }

          // Check if shouldShowExperience() returns the expected value
          cy.window()
            .its("Fides")
            .invoke("shouldShowExperience")
            .should("eql", shouldShowExperience);

          // If shouldShowExperience() is true, the banner should show as well
          if (shouldShowExperience) {
            cy.get("div#fides-banner").should("be.visible");
          } else {
            cy.get("div#fides-banner").should("not.exist");
          }
        });
      });
    },
  );
});
