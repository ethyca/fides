import {
  ComponentType,
  CONSENT_COOKIE_NAME,
  ConsentFlagType,
  ConsentMechanism,
  ConsentMethod,
  ConsentNonApplicableFlagMode,
  encodeNoticeConsentString,
  ExperienceConfig,
  FidesCookie,
  FidesInitOptions,
  Layer1ButtonOption,
  PrivacyNotice,
  RecordConsentServedRequest,
  REQUEST_SOURCE,
  UserConsentPreference,
} from "fides-js";

import { TEST_OVERRIDE_WINDOW_PATH } from "../support/constants";
import {
  mockPrivacyNotice,
  mockPrivacyNoticeTranslation,
} from "../support/mocks";
import { OVERRIDE, overrideTranslation, stubConfig } from "../support/stubs";

const PRIVACY_NOTICE_KEY_1 = "advertising";
const PRIVACY_NOTICE_KEY_2 = "essential";
const PRIVACY_NOTICE_KEY_3 = "analytics_opt_out";

describe("Consent overlay", () => {
  describe("when overlay is disabled", () => {
    describe("when both experience and legacy consent exist", () => {
      beforeEach(() => {
        stubConfig({
          options: {
            isOverlayEnabled: false,
          },
        });
      });

      it("sets Fides.consent object with default consent based on legacy consent", () => {
        cy.window().its("Fides").its("consent").should("eql", {
          data_sales: true,
          tracking: false,
        });
      });

      it("does not render banner", () => {
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("div#fides-banner").should("not.exist");
        });
      });

      it("does not render modal link", () => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    describe("when only legacy consent exists", () => {
      beforeEach(() => {
        stubConfig(
          {
            options: {
              isOverlayEnabled: false,
            },
            experience: OVERRIDE.UNDEFINED,
          },
          {},
          {},
        );
      });

      it("sets Fides.consent object with default consent based on legacy consent", () => {
        cy.window().its("Fides").its("consent").should("eql", {
          data_sales: true,
          tracking: false,
        });
      });

      it("does not render banner", () => {
        cy.get("div#fides-banner").should("not.exist");
      });

      it("does not render modal link", () => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });
  });

  describe("when experience is Headless", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      cy.fixture("consent/fidesjs_options_banner_modal.json").then((config) => {
        stubConfig({
          experience: {
            experience_config: {
              ...config.experience.experience_config,
              ...{ component: ComponentType.HEADLESS },
            },
          },
        });
      });
    });

    it("should not render the banner or modal", () => {
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").should("not.have.been.called");
        cy.get("div#fides-banner").should("not.exist");
        // can display the modal link but it shouldn't do anything
        cy.get("#fides-modal-link").click();
        cy.getByTestId("consent-modal").should("not.exist");
      });
    });
  });

  describe("when overlay is enabled", () => {
    describe("when animation is not disabled", () => {
      beforeEach(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubConfig(
          {
            options: {
              isOverlayEnabled: true,
            },
          },
          undefined,
          undefined,
          { disable_animations: "false" },
        );
      });
      it("slides banner from the bottom automaticallly", () => {
        cy.get("div#fides-banner-container.fides-banner-hidden")
          .should(
            "have.css",
            "transition",
            "transform 1s ease 0s, visibility 1s ease 0s",
          )
          .should("have.css", "transform", "matrix(1, 0, 0, 1, 0, 313.5)");
        cy.get("div#fides-banner").should("not.be.visible");
        cy.get("div#fides-banner-container").should(
          "have.css",
          "transform",
          "matrix(1, 0, 0, 1, 0, 0)",
        );
        cy.get("div#fides-banner").should("be.visible");
      });
      it("slides banner to the bottom when dismissed", () => {
        cy.get("div#fides-banner-container").should(
          "have.css",
          "transform",
          "matrix(1, 0, 0, 1, 0, 0)",
        );
        cy.get("div#fides-banner").should("be.visible");
        cy.get("div#fides-banner-container").within(() => {
          cy.get("button.fides-close-button").click();
        });
        cy.get("div#fides-banner").should("exist");
        cy.get("div#fides-banner").should("not.be.visible");
        cy.get("div#fides-banner-container").should(
          "have.css",
          "transform",
          "matrix(1, 0, 0, 1, 0, 313.5)",
        );
      });
    });
    describe("when overlay is shown", () => {
      beforeEach(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubConfig({
          options: {
            isOverlayEnabled: true,
          },
        });
      });

      it("should render the expected HTML banner", () => {
        cy.get("div#fides-banner").within(() => {
          cy.get(
            "div#fides-banner-description.fides-banner-description",
          ).contains("[banner-opts] We use cookies and similar methods");
          cy.get("div#fides-button-group").within(() => {
            cy.get(
              "button.fides-banner-button.fides-banner-button-tertiary",
            ).contains("Manage preferences");
            cy.get(
              "button.fides-banner-button.fides-banner-button-primary",
            ).contains("Opt out of all");
            cy.get(
              "button.fides-banner-button.fides-banner-button-primary",
            ).contains("Opt in to all");
            // Order matters - it should always be secondary, then primary!
            cy.get("button.fides-manage-preferences-button").should(
              "have.class",
              "fides-banner-button-tertiary",
            );
            cy.get("button.fides-reject-all-button").should(
              "have.class",
              "fides-banner-button-primary",
            );
            cy.get("button.fides-accept-all-button").should(
              "have.class",
              "fides-banner-button-primary",
            );
          });
        });
      });

      it("renders modal link", () => {
        cy.get("#fides-modal-link").should("be.visible");
      });

      it("should allow accepting all", () => {
        cy.get("div#fides-banner").within(() => {
          cy.contains("button", "Opt in to all").should("be.visible").click();
        });
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );
            expect(cookieKeyConsent.consent)
              .property(PRIVACY_NOTICE_KEY_1)
              .is.eql(true);
            expect(cookieKeyConsent.consent)
              .property(PRIVACY_NOTICE_KEY_2)
              .is.eql(true);
            expect(cookieKeyConsent.consent)
              .property(PRIVACY_NOTICE_KEY_3)
              .is.eql(true);
            expect(cookieKeyConsent.fides_meta)
              .property("consentMethod")
              .is.eql(ConsentMethod.ACCEPT);
          });
          cy.get("#fides-banner").should("not.be.visible");
        });
      });

      it("should support rejecting all consent options but keeping notice-only true", () => {
        cy.get("div#fides-banner").within(() => {
          cy.contains("button", "Opt out of all").should("be.visible").click();
        });
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );
            expect(cookieKeyConsent.consent)
              .property(PRIVACY_NOTICE_KEY_1)
              .is.eql(false);
            // Notice-only should stay true
            expect(cookieKeyConsent.consent)
              .property(PRIVACY_NOTICE_KEY_2)
              .is.eql(true);
            expect(cookieKeyConsent.consent)
              .property(PRIVACY_NOTICE_KEY_3)
              .is.eql(false);
            expect(cookieKeyConsent.fides_meta)
              .property("consentMethod")
              .is.eql(ConsentMethod.REJECT);
          });
        });
      });

      it("should not render the banner if fidesDisableBanner is true", () => {
        stubConfig({
          options: {
            isOverlayEnabled: true,
            fidesDisableBanner: true,
          },
        });
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("@FidesUIShown").should("not.have.been.called");
          cy.get("div#fides-banner").should("not.exist");
          // can still open the modal
          cy.get("#fides-modal-link").click();
          cy.getByTestId("consent-modal").should("be.visible");
        });
      });

      describe("modal", () => {
        it("should open modal when experience component = OVERLAY", () => {
          cy.contains("button", "Manage preferences").click();
          cy.getByTestId("consent-modal").should("be.visible");
        });

        it("can toggle the notices", () => {
          cy.contains("button", "Manage preferences").click();
          // Notice should start off toggled off
          cy.getByTestId("toggle-Advertising").within(() => {
            cy.get("input").should("not.be.checked");
          });
          // Opt-out notice should start toggled on
          cy.getByTestId("toggle-Analytics").within(() => {
            cy.get("input").should("be.checked");
          });
          cy.getByTestId("toggle-Advertising").click();
          // Notice-only should start off toggled on
          cy.getByTestId("toggle-Essential").within(() => {
            cy.get("input").should("be.checked");
          });

          cy.getByTestId("Save-btn").click();
          // Modal should close after saving
          cy.getByTestId("consent-modal").should("not.be.visible");

          // check that consent was sent to Fides API
          let generatedUserDeviceId: string;
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            const expected = {
              // browser_identity.fides_user_device_id is intentionally left out here
              // so we can later assert to be any string
              preferences: [
                {
                  privacy_notice_history_id:
                    "pri_notice-history-advertising-en-000",
                  preference: "opt_in",
                },
                {
                  privacy_notice_history_id:
                    "pri_notice-history-analytics-en-000",
                  preference: "opt_in",
                },
                {
                  privacy_notice_history_id:
                    "pri_notice-history-essential-en-000",
                  preference: "acknowledge",
                },
              ],
              privacy_experience_config_history_id:
                "pri_exp-history-banner-modal-en-000",
              user_geography: "us_ca",
              method: ConsentMethod.SAVE,
              served_notice_history_id: body.served_notice_history_id,
            };
            // uuid is generated automatically if the user has no saved consent cookie
            generatedUserDeviceId = body.browser_identity.fides_user_device_id;
            expect(generatedUserDeviceId).to.be.a("string");
            cy.wrap(body.preferences).should(
              "deep.include.members",
              expected.preferences,
            );
            cy.wrap(expected.preferences).should(
              "deep.include.members",
              body.preferences,
            );
            expect(body.privacy_experience_config_history_id).to.eql(
              expected.privacy_experience_config_history_id,
            );
            expect(body.user_geography).to.eql(expected.user_geography);
            expect(body.method).to.eql(expected.method);
          });

          // check that the cookie updated
          cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
            cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
              const cookieKeyConsent: FidesCookie = JSON.parse(
                decodeURIComponent(cookie!.value),
              );
              expect(cookieKeyConsent.identity.fides_user_device_id).is.eql(
                generatedUserDeviceId,
              );
              expect(cookieKeyConsent.consent)
                .property(PRIVACY_NOTICE_KEY_1)
                .is.eql(true);
              expect(cookieKeyConsent.consent)
                .property(PRIVACY_NOTICE_KEY_2)
                .is.eql(true);
              expect(cookieKeyConsent.consent)
                .property(PRIVACY_NOTICE_KEY_3)
                .is.eql(true);
              expect(cookieKeyConsent.fides_meta)
                .property("consentMethod")
                .is.eql(ConsentMethod.SAVE);
            });
          });

          // check that window.Fides.consent updated
          cy.window()
            .its("Fides")
            .its("consent")
            .should("eql", {
              [PRIVACY_NOTICE_KEY_1]: true,
              [PRIVACY_NOTICE_KEY_2]: true,
              [PRIVACY_NOTICE_KEY_3]: true,
            });
        });

        describe("branding link", () => {
          const setupBrandingLinkTest = (
            options: Partial<FidesInitOptions> = {},
          ) => {
            cy.fixture("consent/fidesjs_options_banner_modal.json").then(
              (config) => {
                stubConfig({
                  ...config,
                  options,
                });
              },
            );
          };

          it("doesn't render the branding link when not configured", () => {
            setupBrandingLinkTest({
              showFidesBrandLink: false,
            });
            cy.get("div#fides-modal").within(() => {
              cy.get("a.fides-brand").should("not.exist");
            });
          });

          it("renders the branding link when configured", () => {
            setupBrandingLinkTest({
              showFidesBrandLink: true,
            });
            cy.get("div#fides-modal").within(() => {
              cy.get("a.fides-brand-link").should("exist");
              cy.get("a.fides-brand-link").should(
                "have.attr",
                "href",
                "https://ethyca.com/",
              );
            });
          });
        });

        describe("saving preferences", () => {
          it("skips saving preferences to API when disable save is set", () => {
            stubConfig({
              options: {
                fidesDisableSaveApi: true,
              },
            });
            cy.waitUntilFidesInitialized().then(() => {
              cy.get("#fides-modal-link").click();
              cy.getByTestId("consent-modal").within(() => {
                cy.get("button").contains("Opt out of all").click();
                // timeout means API call not made, which is expected
                cy.on("fail", (error) => {
                  if (error.message.indexOf("Timed out retrying") !== 0) {
                    throw error;
                  }
                });
                // check that preferences aren't sent to Fides API
                cy.wait("@patchPrivacyPreference", {
                  requestTimeout: 100,
                }).then((xhr) => {
                  assert.isNull(xhr?.response?.body);
                });
              });
            });
          });

          it("skips saving preferences to API when disable save is set via cookie", () => {
            cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
            cy.getCookie("fides_disable_save_api").should("not.exist");
            cy.setCookie("fides_disable_save_api", "true");
            stubConfig({});
            cy.waitUntilFidesInitialized().then(() => {
              cy.get("#fides-modal-link").click();
              cy.getByTestId("consent-modal").within(() => {
                cy.get("button").contains("Opt out of all").click();
                // timeout means API call not made, which is expected
                cy.on("fail", (error) => {
                  if (error.message.indexOf("Timed out retrying") !== 0) {
                    throw error;
                  }
                });
                // check that preferences aren't sent to Fides API
                cy.wait("@patchPrivacyPreference", {
                  requestTimeout: 100,
                }).then((xhr) => {
                  assert.isNull(xhr?.response?.body);
                });
              });
            });
          });

          it("skips saving preferences to API when disable save is set via query param", () => {
            cy.getCookie("fides_string").should("not.exist");
            stubConfig({}, null, null, { fides_disable_save_api: "true" });
            cy.waitUntilFidesInitialized().then(() => {
              cy.get("#fides-modal-link").click();
              cy.getByTestId("consent-modal").within(() => {
                cy.get("button").contains("Opt out of all").click();
                // timeout means API call not made, which is expected
                cy.on("fail", (error) => {
                  if (error.message.indexOf("Timed out retrying") !== 0) {
                    throw error;
                  }
                });
                // check that preferences aren't sent to Fides API
                cy.wait("@patchPrivacyPreference", {
                  requestTimeout: 100,
                }).then((xhr) => {
                  assert.isNull(xhr?.response?.body);
                });
              });
            });
          });

          it("skips saving preferences to API when disable save is set via window obj", () => {
            cy.getCookie("fides_string").should("not.exist");
            stubConfig({}, null, null, null, {
              fides_disable_save_api: "true",
            });
            cy.waitUntilFidesInitialized().then(() => {
              cy.get("#fides-modal-link").click();
              cy.getByTestId("consent-modal").within(() => {
                cy.get("button").contains("Opt out of all").click();
                // timeout means API call not made, which is expected
                cy.on("fail", (error) => {
                  if (error.message.indexOf("Timed out retrying") !== 0) {
                    throw error;
                  }
                });
                // check that preferences aren't sent to Fides API
                cy.wait("@patchPrivacyPreference", {
                  requestTimeout: 100,
                }).then((xhr) => {
                  assert.isNull(xhr?.response?.body);
                });
              });
            });
          });
        });
      });

      describe("experience descriptions", () => {
        describe("when experience uses rich HTML descriptions", () => {
          // Shared helper that overrides the experience config description with
          // an HTML example and allows toggling the allowHTMLDescription option
          const setupHTMLDescriptionTest = (
            options: Partial<FidesInitOptions> = {},
          ) => {
            const HTMLDescription = `
            This test is overriding the <pre>experience_config.description</pre> with a <strong>HTML</strong> description, which is used to allow users to configure banners with <a href='https://example.com'>clickable links</a> and...

            ...multiple paragraphs with ease. However, it's not enabled by default unless the <pre>options.allowHTMLDescription</pre> flag is <pre>true</pre> to reduce the likelihood of XSS attacks.
            `;
            cy.fixture("consent/fidesjs_options_banner_modal.json").then(
              (config) => {
                const newExperienceTranslationsConfig = [
                  overrideTranslation(
                    config.experience.experience_config.translations[0],
                    { banner_description: HTMLDescription },
                  ),
                ];
                stubConfig({
                  experience: {
                    experience_config: {
                      ...config.experience.experience_config,
                      ...{ translations: newExperienceTranslationsConfig },
                    },
                  },
                  options,
                });
              },
            );
          };

          it("does not render HTML by default", () => {
            setupHTMLDescriptionTest({ allowHTMLDescription: false });
            cy.get("div#fides-banner").within(() => {
              cy.get(
                "div#fides-banner-description.fides-banner-description",
              ).contains("This test is overriding");
              cy.get("div#fides-banner-description.fides-banner-description")
                .contains("a", "clickable links")
                .should("not.exist");
            });
          });

          it("renders HTML when options.allowHTMLDescription = true", () => {
            setupHTMLDescriptionTest({ allowHTMLDescription: true });
            cy.get("div#fides-banner").within(() => {
              cy.get(
                "div#fides-banner-description.fides-banner-description",
              ).contains("This test is overriding");
              cy.get("div#fides-banner-description.fides-banner-description")
                .contains("a", "clickable links")
                .should("exist");
            });
          });
        });

        describe("when experience uses different descriptions for modal & banner", () => {
          beforeEach(() => {
            const bannerDescription =
              "This test is overriding the banner description separately from modal!";
            const modalDescription =
              "This test is overriding the modal description separately from banner!";
            cy.fixture("consent/fidesjs_options_banner_modal.json").then(
              (config) => {
                const newExperienceTranslationsConfig = [
                  overrideTranslation(
                    config.experience.experience_config.translations[0],
                    {
                      description: modalDescription,
                      banner_description: bannerDescription,
                    },
                  ),
                ];
                stubConfig({
                  experience: {
                    experience_config: {
                      ...config.experience.experience_config,
                      ...{ translations: newExperienceTranslationsConfig },
                    },
                  },
                });
              },
            );
          });

          it("renders the expected modal & banner descriptions", () => {
            cy.get("div#fides-banner").within(() => {
              cy.get(
                "div#fides-banner-description.fides-banner-description",
              ).contains(
                "This test is overriding the banner description separately from modal!",
              );
            });

            cy.contains("button", "Manage preferences").click();
            cy.getByTestId("consent-modal").should("be.visible");

            cy.get("div#fides-modal").within(() => {
              cy.get(".fides-modal-description").contains(
                "This test is overriding the modal description separately from banner!",
              );
            });
          });
        });
      });

      describe("titles", () => {
        describe("when experience uses different titles for modal & banner", () => {
          beforeEach(() => {
            const bannerTitle =
              "This test is overriding the banner title separately from modal!";
            const modalTitle =
              "This test is overriding the modal title separately from banner!";
            cy.fixture("consent/fidesjs_options_banner_modal.json").then(
              (config) => {
                const newExperienceTranslationsConfig = [
                  overrideTranslation(
                    config.experience.experience_config.translations[0],
                    { title: modalTitle, banner_title: bannerTitle },
                  ),
                ];
                stubConfig({
                  experience: {
                    experience_config: {
                      ...config.experience.experience_config,
                      ...{ translations: newExperienceTranslationsConfig },
                    },
                  },
                });
              },
            );
          });

          it("renders the expected modal & banner title", () => {
            cy.get("div#fides-banner").within(() => {
              cy.get(".fides-banner-title")
                .first()
                .contains(
                  "This test is overriding the banner title separately from modal!",
                );
            });

            cy.contains("button", "Manage preferences").click();
            cy.getByTestId("consent-modal").should("be.visible");

            cy.get("div#fides-modal").within(() => {
              cy.get(".fides-modal-title").contains(
                "This test is overriding the modal title separately from banner!",
              );
            });
          });
        });
      });

      it("can persist state between modal and banner", () => {
        cy.get("div#fides-banner").within(() => {
          cy.get("button").contains("Opt in to all").click();
        });
        // Now check that the change persisted by opening the modal
        cy.get("[id='fides-modal-link']").click();
        cy.getByTestId("toggle-Advertising").within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.checked");
        });
        // Now reject all
        cy.getByTestId("fides-modal-content").within(() => {
          cy.get("button").contains("Opt out of all").click();
        });
        // Check the modal again
        cy.get("[id='fides-modal-link']").click();
        cy.getByTestId("toggle-Advertising").within(() => {
          cy.get("input").should("not.be.checked");
        });
        // Notice-only should still be checked
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.checked");
        });
      });

      it("handles legacy notices when experience fetched server-side", () => {
        const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
        const CREATED_DATE = "2022-12-24T12:00:00.000Z";
        const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
        const legacyNotices = {
          data_sales: false,
          tracking: false,
          analytics: true,
        };
        const originalCookie = {
          identity: { fides_user_device_id: uuid },
          fides_meta: {
            version: "0.9.0",
            createdAt: CREATED_DATE,
            updatedAt: UPDATED_DATE,
          },
          consent: legacyNotices,
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));

        // we need to visit the page after the cookie exists, so the Fides.consent obj is initialized with the original
        // cookie values
        stubConfig({
          options: {
            isOverlayEnabled: true,
          },
        });

        cy.contains("button", "Manage preferences").click();

        // UI should reflect client-side fetched experience (fidesjs_options_banner_modal.json)
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.disabled");
          cy.get("input").should("be.checked");
        });
        cy.getByTestId("toggle-Advertising").within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId("toggle-Analytics").within(() => {
          cy.get("input").should("be.checked");
        });

        // Save new preferences
        cy.getByTestId("toggle-Advertising").click();
        cy.getByTestId("Save-btn").click();

        // New privacy notice values only, no legacy ones
        const expectedConsent = {
          [PRIVACY_NOTICE_KEY_1]: true,
          [PRIVACY_NOTICE_KEY_2]: true,
          [PRIVACY_NOTICE_KEY_3]: true,
        };

        // check that consent was sent to Fides API
        cy.wait("@patchPrivacyPreference").then((interception) => {
          const { body } = interception.request;
          const expected = {
            browser_identity: { fides_user_device_id: uuid },
            preferences: [
              {
                privacy_notice_history_id:
                  "pri_notice-history-advertising-en-000",
                preference: "opt_in",
              },
              {
                privacy_notice_history_id:
                  "pri_notice-history-analytics-en-000",
                preference: "opt_in",
              },
              {
                privacy_notice_history_id:
                  "pri_notice-history-essential-en-000",
                preference: "acknowledge",
              },
            ],
            privacy_experience_config_history_id:
              "pri_exp-history-banner-modal-en-000",
            user_geography: "us_ca",

            method: ConsentMethod.SAVE,
            served_notice_history_id: body.served_notice_history_id,
            source: REQUEST_SOURCE,
          };
          cy.wrap(body.preferences).should(
            "deep.include.members",
            expected.preferences,
          );
          cy.wrap(expected.preferences).should(
            "deep.include.members",
            body.preferences,
          );
          expect(body.served_notice_history_id).to.be.a("string");
        });

        // check that the cookie updated
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );
            expect(cookieKeyConsent.consent).eql(expectedConsent);
          });
        });

        // check that window.Fides.consent updated
        cy.window().its("Fides").its("consent").should("eql", expectedConsent);
      });

      it("handles legacy notices when experience fetched client-side", () => {
        const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
        const CREATED_DATE = "2022-12-24T12:00:00.000Z";
        const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
        const legacyNotices = {
          data_sales: false,
          tracking: false,
          analytics: true,
        };
        const originalCookie = {
          identity: { fides_user_device_id: uuid },
          fides_meta: {
            version: "0.9.0",
            createdAt: CREATED_DATE,
            updatedAt: UPDATED_DATE,
          },
          consent: legacyNotices,
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));

        // we need to visit the page after the cookie exists, so the Fides.consent obj is initialized with the original
        // cookie values
        stubConfig({
          experience: OVERRIDE.UNDEFINED,
          geolocation: {
            country: "US",
            location: "US-CA",
            region: "CA",
          },
          options: {
            isOverlayEnabled: true,
          },
        });

        cy.contains("button", "Manage preferences").click();

        // UI should reflect client-side fetched experience (overlay_experience.json)
        cy.getByTestId("toggle-Advertising").within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId("toggle-Analytics").within(() => {
          cy.get("input").should("be.checked");
        });

        // Save new preferences
        cy.getByTestId("toggle-Advertising").click();
        cy.getByTestId("Save-btn").click();

        // New privacy notice values only, no legacy ones
        const expectedConsent = {
          advertising: true,
          analytics_opt_out: true,
          essential: true,
        };

        // check that consent was sent to Fides API
        cy.wait("@patchPrivacyPreference").then((interception) => {
          const { body } = interception.request;
          const expected = {
            browser_identity: { fides_user_device_id: uuid },
            preferences: [
              {
                privacy_notice_history_id:
                  "pri_notice-history-advertising-en-000",
                preference: "opt_in",
              },
              {
                privacy_notice_history_id:
                  "pri_notice-history-analytics-en-000",
                preference: "opt_in",
              },
              {
                privacy_notice_history_id:
                  "pri_notice-history-essential-en-000",
                preference: "acknowledge",
              },
            ],
            privacy_experience_config_history_id:
              "pri_exp-history-banner-modal-en-000",
            user_geography: "us_ca",
            method: ConsentMethod.SAVE,
            served_notice_history_id: body.served_notice_history_id,
            source: REQUEST_SOURCE,
          };
          cy.wrap(body.preferences).should(
            "deep.include.members",
            expected.preferences,
          );
          cy.wrap(expected.preferences).should(
            "deep.include.members",
            body.preferences,
          );
          expect(body.served_notice_history_id).to.be.a("string");
        });

        // check that the cookie updated
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );
            expect(cookieKeyConsent.consent).eql(expectedConsent);
          });
        });

        // check that window.Fides.consent updated
        cy.window().its("Fides").its("consent").should("eql", expectedConsent);
      });

      it("disables notice-only notices from opting out", () => {
        cy.contains("button", "Manage preferences").click();
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.disabled");
          cy.get("input").should("be.checked");
        });
      });

      describe("when dismissing banner and modal", () => {
        // TODO (PROD-1792): Fix peculiar dismiss issues
        it.skip("saves default consent preferences, but only when no saved consent cookie exists", () => {
          // Open & dismiss the modal as a net new user
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
          cy.get("#fides-modal-link").click();
          cy.get("#fides-modal .fides-close-button").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { method, preferences } = interception.request.body;
            expect(method).to.eq("dismiss");
            expect(preferences.map((p: any) => p.preference)).to.eql([
              "opt_out",
              "opt_in",
              "acknowledge",
            ]);
          });
          cy.get("@FidesUpdated").should("have.been.calledOnce");

          // Re-open the modal and dismiss again
          cy.waitUntilCookieExists(CONSENT_COOKIE_NAME);
          cy.get("#fides-modal-link").click();
          cy.get("#fides-modal .fides-close-button").click();
          // We shouldn't fire a second FidesUpdated event yet!
          cy.get("@FidesUpdated").should("have.been.calledOnce");

          // Re-open the modal, change preferences and save
          cy.get("#fides-modal-link").click();
          cy.get(
            "#fides-modal .fides-modal-notices .fides-toggle-input:first",
          ).click();
          cy.get("#fides-modal #fides-save-button").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { method, preferences } = interception.request.body;
            expect(method).to.eq("save");
            expect(preferences.map((p: any) => p.preference)).to.eql([
              "opt_in",
              "opt_in",
              "acknowledge",
            ]);
          });
          cy.get("@FidesUpdated").should("have.been.calledTwice");

          // Re-open & dismiss a few more times to confirm that saved preferences are respected
          cy.get("#fides-modal-link").click();
          cy.get(
            "#fides-modal .fides-modal-notices .fides-toggle-input:first",
          ).should("be.checked");
          cy.get("#fides-modal #fides-save-button").click();
          cy.get("#fides-modal-link").click();
          cy.get(
            "#fides-modal .fides-modal-notices .fides-toggle-input:first",
          ).should("be.checked");
          cy.get("#fides-modal #fides-save-button").click();
          // We still should not fire any FidesUpdated events
          cy.get("@FidesUpdated").should("have.been.calledTwice");
        });

        // TODO (PROD-1792): resurface consent banner after dismissing
        it.skip("resurfaces the banner on future visits after dismissing", () => {});
      });
    });

    describe("cookie enforcement tests", () => {
      beforeEach(() => {
        const cookies = [
          { name: "cookie1", path: "/" },
          { name: "cookie2", path: "/" },
        ];
        cookies.forEach((cookie) => {
          cy.setCookie(cookie.name, "value", { path: cookie.path });
        });
        stubConfig({
          experience: {
            privacy_notices: [
              mockPrivacyNotice({
                title: "one",
                notice_key: "one",
                id: "pri_notice-one",
                consent_mechanism: ConsentMechanism.OPT_OUT,
                cookies: [cookies[0]],
              }),
              mockPrivacyNotice({
                title: "two",
                notice_key: "two",
                id: "pri_notice-two",
                consent_mechanism: ConsentMechanism.OPT_OUT,
                cookies: [cookies[1]],
              }),
            ],
          },
          options: {
            isOverlayEnabled: true,
          },
        });
      });

      it("can remove all cookies when rejecting all", () => {
        cy.get("div#fides-banner").within(() => {
          cy.contains("button", "Opt out of all").click();
        });
        cy.get("@FidesUpdated")
          .should("have.been.calledOnce")
          .its("lastCall.args.0.detail.extraDetails.consentMethod")
          .then((consentMethod) => {
            expect(consentMethod).to.eql(ConsentMethod.REJECT);
          });
        cy.getAllCookies().then((allCookies) => {
          expect(allCookies.map((c) => c.name)).to.eql([CONSENT_COOKIE_NAME]);
        });
      });

      it("can remove just the cookies associated with notices that were opted out", () => {
        cy.contains("button", "Manage preferences").click();
        // opt out of the first notice
        cy.getByTestId("toggle-one").click();
        cy.getByTestId("Save-btn").click();
        cy.get("@FidesUpdated")
          .should("have.been.calledOnce")
          .its("lastCall.args.0.detail.extraDetails.consentMethod")
          .then((consentMethod) => {
            expect(consentMethod).to.eql(ConsentMethod.SAVE);
          });
        cy.getAllCookies().then((allCookies) => {
          expect(allCookies.map((c) => c.name)).to.eql([
            CONSENT_COOKIE_NAME,
            "cookie2",
          ]);
        });
      });
    });

    describe("when there are only notice-only notices", () => {
      const expected = [
        {
          privacy_notice_history_id: "pri_notice-history-one",
          preference: "acknowledge",
        },
        {
          privacy_notice_history_id: "pri_notice-history-two",
          preference: "acknowledge",
        },
      ];

      beforeEach(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubConfig({
          experience: {
            privacy_notices: [
              mockPrivacyNotice(
                {
                  title: "one",
                  id: "pri_notice-one",
                  notice_key: "one",
                  consent_mechanism: ConsentMechanism.NOTICE_ONLY,
                },
                [
                  mockPrivacyNoticeTranslation({
                    title: "one",
                    privacy_notice_history_id: "pri_notice-history-one",
                  }),
                ],
              ),
              mockPrivacyNotice(
                {
                  title: "two",
                  id: "pri_notice-two",
                  notice_key: "two",
                  consent_mechanism: ConsentMechanism.NOTICE_ONLY,
                },
                [
                  mockPrivacyNoticeTranslation({
                    title: "two",
                    privacy_notice_history_id: "pri_notice-history-two",
                  }),
                ],
              ),
            ],
          },
          options: {
            isOverlayEnabled: true,
          },
        });
      });

      it("renders an acknowledge button in the banner", () => {
        cy.get("div#fides-banner").within(() => {
          cy.get("button").contains("OK");
          cy.get("button").contains("Opt in to all").should("not.exist");
          cy.get("button").contains("OK").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            cy.wrap(body.preferences).should("deep.include.members", expected);
            cy.wrap(expected).should("deep.include.members", body.preferences);
          });
        });
      });

      it("renders an acknowledge button in the modal", () => {
        cy.get("#fides-modal-link").click();
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt in to all").should("not.exist");
          cy.get("button").contains("OK").click();
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            cy.wrap(body.preferences).should("deep.include.members", expected);
            cy.wrap(expected).should("deep.include.members", body.preferences);
          });
        });
      });
    });

    describe("when preferences are automatically applied", () => {
      describe("when GPC flag is found, and notices apply to GPC", () => {
        beforeEach(() => {
          cy.on("window:before:load", (win) => {
            // eslint-disable-next-line no-param-reassign
            win.navigator.globalPrivacyControl = true;
          });
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
          stubConfig({
            experience: {
              privacy_notices: [
                mockPrivacyNotice({
                  title: "Advertising with gpc enabled",
                  id: "pri_notice-advertising",
                  has_gpc_flag: true,
                }),
              ],
            },
          });
        });

        it("sends GPC consent override downstream to Fides API", () => {
          // check that consent was sent to Fides API
          let generatedUserDeviceId: string;
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            const expected = {
              // browser_identity.fides_user_device_id is intentionally left out here
              // so we can later assert to be any string
              preferences: [
                {
                  privacy_notice_history_id:
                    "pri_notice-history-mock-advertising-en-000",
                  preference: "opt_out",
                },
              ],
              privacy_experience_config_history_id:
                "pri_exp-history-banner-modal-en-000",
              user_geography: "us_ca",

              method: ConsentMethod.GPC,
              served_notice_history_id: body.served_notice_history_id,
            };
            // uuid is generated automatically if the user has no saved consent cookie
            generatedUserDeviceId = body.browser_identity.fides_user_device_id;
            expect(generatedUserDeviceId).to.be.a("string");
            expect(body.preferences).to.eql(expected.preferences);
            expect(body.privacy_experience_config_history_id).to.eql(
              expected.privacy_experience_config_history_id,
            );
            expect(body.user_geography).to.eql(expected.user_geography);
            expect(body.method).to.eql(expected.method);
          });
        });

        it("stores consent in cookie", () => {
          cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
            cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
              const cookieKeyConsent: FidesCookie = JSON.parse(
                decodeURIComponent(cookie!.value),
              );
              expect(cookieKeyConsent.consent)
                .property(PRIVACY_NOTICE_KEY_1)
                .is.eql(false);
              expect(cookieKeyConsent.fides_meta)
                .property("consentMethod")
                .is.eql(ConsentMethod.GPC);
            });
          });
        });

        it("updates Fides consent obj", () => {
          cy.window()
            .its("Fides")
            .its("consent")
            .should("eql", {
              [PRIVACY_NOTICE_KEY_1]: false,
            });
        });

        it("shows indicators that GPC has been applied", () => {
          // In the banner
          cy.get("div#fides-banner").should("be.visible");
          cy.get("div#fides-banner").within(() => {
            cy.get("span").contains("Global Privacy Control");
          });
          // And in the modal
          cy.get("button").contains("Manage preferences").click();
          cy.get("div.fides-gpc-banner").contains(
            "Global Privacy Control detected",
          );
          cy.get("span").contains("Advertising with gpc enabled");
          cy.get("span").contains("Global Privacy Control Applied");
        });

        it("sends GPC consent override from a Headless experience", () => {
          cy.on("window:before:load", (win) => {
            // eslint-disable-next-line no-param-reassign
            win.navigator.globalPrivacyControl = true;
          });
          cy.fixture("consent/fidesjs_options_banner_modal.json").then(
            (config) => {
              stubConfig({
                experience: {
                  experience_config: {
                    ...config.experience.experience_config,
                    ...{ component: ComponentType.HEADLESS },
                  },
                },
              });
            },
          );
          cy.wait("@patchPrivacyPreference");
        });
      });

      describe("when GPC flag is found, and no notices apply to GPC", () => {
        beforeEach(() => {
          cy.on("window:before:load", (win) => {
            // eslint-disable-next-line no-param-reassign
            win.navigator.globalPrivacyControl = true;
          });
          stubConfig({
            experience: {
              privacy_notices: [
                mockPrivacyNotice({
                  title: "Advertising with GPC disabled",
                  id: "pri_notice-advertising",
                  has_gpc_flag: false,
                }),
              ],
            },
          });
        });

        it("does not set user consent preference automatically", () => {
          // timeout means API call not made, which is expected
          cy.on("fail", (error) => {
            if (error.message.indexOf("Timed out retrying") !== 0) {
              throw error;
            }
          });
          // check that preferences aren't sent to Fides API
          cy.wait("@patchPrivacyPreference", {
            requestTimeout: 500,
          }).then((xhr) => {
            assert.isNull(xhr?.response?.body);
          });
          // check that Fides consent obj is empty
          cy.window().its("Fides").its("consent").should("eql", {});
          // check that preferences do not exist in cookie
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        });

        it("does not show gpc indicator but does show it was detected and the info banner", () => {
          // In the banner
          cy.get("div.fides-gpc-banner").contains(
            "Global Privacy Control detected",
          );
          // And in the modal
          cy.get("button").contains("Manage preferences").click();
          cy.get("div.fides-gpc-banner").should("be.visible");
          cy.get("div.fides-gpc-badge").should("not.exist");
        });
      });

      describe("when no GPC flag is found, and notices apply to GPC", () => {
        beforeEach(() => {
          cy.on("window:before:load", (win) => {
            // eslint-disable-next-line no-param-reassign
            win.navigator.globalPrivacyControl = undefined;
          });
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
          stubConfig({
            experience: {
              privacy_notices: [
                mockPrivacyNotice({
                  title: "Advertising with gpc enabled",
                  id: "pri_notice-advertising",
                  has_gpc_flag: true,
                }),
              ],
            },
          });
        });

        it("does not set user consent preference automatically", () => {
          // timeout means API call not made, which is expected
          cy.on("fail", (error) => {
            if (error.message.indexOf("Timed out retrying") !== 0) {
              throw error;
            }
          });
          // check that preferences aren't sent to Fides API
          cy.wait("@patchPrivacyPreference", {
            requestTimeout: 500,
          }).then((xhr) => {
            assert.isNull(xhr?.response?.body);
          });
          // check that Fides consent obj is empty
          cy.window().its("Fides").its("consent").should("eql", {});
          // check that preferences do not exist in cookie
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        });

        it("does not show any gpc indicators", () => {
          // In the banner
          cy.get("div#fides-banner").within(() => {
            cy.get("span.fides-gpc-badge").should("not.exist");
          });
          // And in the modal
          cy.get("button").contains("Manage preferences").click();
          cy.get("div.fides-gpc-banner").should("not.exist");
          cy.get("div.fides-gpc-badge").should("not.exist");
        });
      });

      describe("when GPC flag is found, and notices apply to GPC and acknowledge button is used", () => {
        beforeEach(() => {
          cy.on("window:before:load", (win) => {
            // eslint-disable-next-line no-param-reassign
            win.navigator.globalPrivacyControl = true;
          });
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
          stubConfig({
            experience: {
              privacy_notices: [
                mockPrivacyNotice({
                  title: "Advertising with gpc enabled",
                  id: "pri_notice-advertising",
                  has_gpc_flag: true,
                }),
                mockPrivacyNotice({
                  title: "one",
                  id: "pri_notice-one",
                  notice_key: "one",
                  consent_mechanism: ConsentMechanism.NOTICE_ONLY,
                }),
              ],
            },
            experienceConfig: {
              layer1_button_options: Layer1ButtonOption.ACKNOWLEDGE,
            },
          });
        });

        it("does not get overridden by banner acknowledge button", () => {
          cy.get("@FidesUpdated")
            .should("have.been.calledOnce")
            .its("lastCall.args.0.detail.extraDetails.consentMethod")
            .then((consentMethod) => {
              expect(consentMethod).to.eql(ConsentMethod.GPC);
            });
          cy.get("div#fides-banner").within(() => {
            cy.get("button").contains("OK").click();
          });
          cy.get("@FidesUpdated")
            .should("have.been.calledTwice")
            .its("lastCall.args.0.detail.extraDetails.consentMethod")
            .then((consentMethod) => {
              expect(consentMethod).to.eql(ConsentMethod.ACKNOWLEDGE);
            });
          cy.get("#fides-modal-link").click();
          cy.get(".fides-notice-toggle")
            .contains("Applied")
            .parents(".fides-notice-toggle-title")
            .within(() => {
              cy.get(".fides-gpc-label").contains("Applied");
            });
        });
      });

      describe("when Fides string with Notice Consent is found", () => {
        const consent = {};
        consent[PRIVACY_NOTICE_KEY_1] = true;
        const noticeConsentString = encodeNoticeConsentString(consent);
        beforeEach(() => {
          cy.on("window:before:load", (win) => {
            // eslint-disable-next-line no-param-reassign
            win.navigator.globalPrivacyControl = false;
          });
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
          cy.fixture("consent/experience_banner_modal.json").then(
            (experience) => {
              const mockPrivacyNotice = experience.items[0].privacy_notices[0];
              stubConfig({
                experience: {
                  privacy_notices: [mockPrivacyNotice],
                },
                options: {
                  fidesString: `,,,${noticeConsentString}`,
                },
              });
            },
          );
        });

        it("sends Fides String with Notice Consent downstream to Fides API", () => {
          // check that consent was sent to Fides API
          let generatedUserDeviceId: string;
          cy.wait("@patchPrivacyPreference").then((interception) => {
            const { body } = interception.request;
            const expected = {
              // browser_identity.fides_user_device_id is intentionally left out here
              // so we can later assert to be any string
              preferences: [
                {
                  privacy_notice_history_id:
                    "pri_notice-history-advertising-en-000",
                  preference: "opt_in",
                },
              ],
              privacy_experience_config_history_id:
                "pri_exp-history-banner-modal-en-000",
              user_geography: "us_ca",

              method: ConsentMethod.SCRIPT,
              served_notice_history_id: body.served_notice_history_id,
            };
            // uuid is generated automatically if the user has no saved consent cookie
            generatedUserDeviceId = body.browser_identity.fides_user_device_id;
            expect(generatedUserDeviceId).to.be.a("string");
            expect(body.preferences).to.eql(expected.preferences);
            expect(body.privacy_experience_config_history_id).to.eql(
              expected.privacy_experience_config_history_id,
            );
            expect(body.user_geography).to.eql(expected.user_geography);
            expect(body.method).to.eql(expected.method);
          });
        });

        it("stores consent in cookie", () => {
          cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
            cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
              const cookieKeyConsent: FidesCookie = JSON.parse(
                decodeURIComponent(cookie!.value),
              );
              expect(cookieKeyConsent.consent)
                .property(PRIVACY_NOTICE_KEY_1)
                .is.eql(true);
              expect(cookieKeyConsent.fides_meta)
                .property("consentMethod")
                .is.eql(ConsentMethod.SCRIPT);
            });
          });
        });

        it("updates Fides consent obj", () => {
          cy.window()
            .its("Fides")
            .its("consent")
            .should("eql", {
              [PRIVACY_NOTICE_KEY_1]: true,
            });
        });

        it("sends consent override from a Headless experience", () => {
          cy.fixture("consent/fidesjs_options_banner_modal.json").then(
            (config) => {
              stubConfig({
                experience: {
                  experience_config: {
                    ...config.experience.experience_config,
                    ...{ component: ComponentType.HEADLESS },
                  },
                },
                options: {
                  fidesString: `,,,${noticeConsentString}`,
                },
              });
            },
          );
          cy.wait("@patchPrivacyPreference");
        });
      });

      describe("when Notice Consent string is found and takes precedence over GPC", () => {
        beforeEach(() => {
          cy.on("window:before:load", (win) => {
            // eslint-disable-next-line no-param-reassign
            win.navigator.globalPrivacyControl = true;
          });
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
          const consent = {};
          consent[PRIVACY_NOTICE_KEY_1] = true;
          const noticeConsentString = encodeNoticeConsentString(consent);
          stubConfig({
            experience: {
              privacy_notices: [
                mockPrivacyNotice({
                  title: "Advertising with gpc enabled",
                  id: "pri_notice-advertising",
                  has_gpc_flag: true,
                  notice_key: PRIVACY_NOTICE_KEY_1,
                }),
              ],
            },
            options: {
              fidesString: `,,,${noticeConsentString}`,
            },
          });
        });

        it("applies Notice Consent string preferences and overrides GPC", () => {
          // Verify the GPC badge shows as overridden
          cy.get("#fides-modal-link").click();
          cy.get(".fides-notice-toggle")
            .contains("Advertising with gpc enabled")
            .parents(".fides-notice-toggle-title")
            .within(() => {
              cy.get(".fides-gpc-label .fides-gpc-badge").contains(
                "Overridden",
              );
            });
        });
      });
    });

    describe("when experience component is not an overlay", () => {
      beforeEach(() => {
        cy.fixture("consent/fidesjs_options_banner_modal.json").then(
          (config) => {
            stubConfig({
              experience: {
                experience_config: {
                  ...config.experience.experience_config,
                  ...{ component: ComponentType.PRIVACY_CENTER },
                },
              },
            });
          },
        );
      });

      it("does not render banner", () => {
        cy.get("div#fides-banner").should("not.exist");
      });

      it("does not render modal link", () => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    describe("when experience is not provided, and valid geolocation is provided", () => {
      beforeEach(() => {
        stubConfig({
          experience: OVERRIDE.UNDEFINED,
          geolocation: {
            country: "US",
            location: "US-CA",
            region: "CA",
          },
        });
      });

      it("fetches experience and renders the banner", () => {
        cy.wait("@getPrivacyExperience").then((interception) => {
          expect(interception.request.query.region).to.eq("us_ca");
        });
        cy.get("div#fides-banner").should("exist");
        cy.get("div#fides-banner").within(() => {
          cy.contains("button", "Opt in to all").should("exist");
          cy.get(
            "div#fides-banner-description.fides-banner-description",
          ).contains("[banner] We use cookies and similar methods");
        });
      });

      it("renders modal link", () => {
        cy.get("#fides-modal-link").should("be.visible");
      });
    });

    describe("when experience is provided, and geolocation is not provided", () => {
      beforeEach(() => {
        stubConfig({
          geolocation: OVERRIDE.UNDEFINED,
          options: {
            isGeolocationEnabled: true,
            geolocationApiUrl: "https://some-geolocation-url.com",
          },
        });
      });

      it("fetches geolocation and renders the banner", () => {
        // we still need geolocation because it is needed to save consent preference
        cy.wait("@getGeolocation");
        cy.get("div#fides-banner").should("exist");
        cy.get("div#fides-banner").within(() => {
          cy.contains("button", "Opt in to all").should("exist");
          cy.get(
            "div#fides-banner-description.fides-banner-description",
          ).contains("[banner-opts] We use cookies and similar methods");
        });
      });

      it("renders modal link", () => {
        cy.get("#fides-modal-link").should("be.visible");
      });
    });

    describe("when experience is empty, and geolocation is not provided", () => {
      beforeEach(() => {
        stubConfig({
          geolocation: OVERRIDE.UNDEFINED,
          experience: OVERRIDE.EMPTY,
          options: {
            isGeolocationEnabled: true,
            geolocationApiUrl: "https://some-geolocation-url.com",
          },
        });
      });

      it("does fetches geolocation and does not render the banner", () => {
        // we still need geolocation because it is needed to save consent preference
        cy.wait("@getGeolocation");
        cy.get("div#fides-banner").should("not.exist");
      });

      it("does not render modal link", () => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    describe("when experience is empty, and geolocation is provided", () => {
      beforeEach(() => {
        stubConfig({
          geolocation: {
            country: "US",
            location: "US-CA",
            region: "CA",
          },
          experience: OVERRIDE.EMPTY,
          options: {
            isGeolocationEnabled: true,
            geolocationApiUrl: "https://some-geolocation-url.com",
          },
        });
      });

      it("does not geolocate and does not render the banner", () => {
        cy.get("div#fides-banner").should("not.exist");
      });

      it("does not render modal link", () => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    describe("when neither experience nor geolocation is provided, but geolocationApiUrl is defined", () => {
      describe("when geolocation is successful", () => {
        it("fetches geolocation and experience renders the banner", () => {
          const geoLocationUrl = "https://some-geolocation-api.com";
          stubConfig({
            experience: OVERRIDE.UNDEFINED,
            geolocation: OVERRIDE.UNDEFINED,
            options: {
              isGeolocationEnabled: true,
              geolocationApiUrl: geoLocationUrl,
            },
          });
          cy.wait("@getGeolocation");
          cy.wait("@getPrivacyExperience").then((interception) => {
            expect(interception.request.query.region).to.eq("us_ca");
          });
          cy.get("div#fides-banner").should("exist");
          cy.get("div#fides-banner").within(() => {
            cy.contains("button", "Opt in to all").should("exist");
            cy.get(
              "div#fides-banner-description.fides-banner-description",
            ).contains("[banner] We use cookies and similar methods");
          });
          cy.get("#fides-modal-link").should("be.visible");
        });

        describe("when custom experience fn is provided in Fides.init()", () => {
          it("should skip calling Fides API cor experience and instead call the custom fn", () => {
            cy.fixture("consent/experience_privacy_center.json").then(
              (privacyExperience) => {
                const apiOptions = {
                  /* eslint-disable @typescript-eslint/no-unused-vars */
                  getPrivacyExperienceFn: async (
                    userLocationString: string,
                    fidesUserDeviceId?: string | null,
                  ) => privacyExperience.items[0],
                  /* eslint-enable @typescript-eslint/no-unused-vars */
                };
                const spyObject = cy.spy(apiOptions, "getPrivacyExperienceFn");
                stubConfig({
                  options: {
                    isOverlayEnabled: true,
                    apiOptions,
                  },
                  geolocation: {
                    country: "US",
                    location: "US-CA",
                    region: "CA",
                  },
                  experience: OVERRIDE.UNDEFINED,
                });
                cy.waitUntilFidesInitialized().then(() => {
                  // eslint-disable-next-line @typescript-eslint/no-unused-expressions
                  expect(spyObject).to.be.called;
                  const spy = spyObject.getCalls();
                  const { args } = spy[0];
                  expect(args[0]).to.equal("us_ca");
                  // timeout means Fides API call not made, which is expected
                  cy.on("fail", (error) => {
                    if (error.message.indexOf("Timed out retrying") !== 0) {
                      throw error;
                    }
                  });
                  // check that  Fides experience API is not called
                  cy.wait("@getPrivacyExperience", {
                    requestTimeout: 100,
                  }).then((xhr) => {
                    assert.isNull(xhr?.response?.body);
                  });
                });
              },
            );
          });
        });
      });

      describe("when geolocation is not successful", () => {
        beforeEach(() => {
          // mock failed geolocation api call
          const mockFailedGeolocationCall = {
            body: {},
          };
          stubConfig(
            {
              experience: OVERRIDE.UNDEFINED,
              geolocation: OVERRIDE.UNDEFINED,
              options: {
                isGeolocationEnabled: true,
                geolocationApiUrl: "https://some-geolocation-api.com",
              },
            },
            mockFailedGeolocationCall,
          );
        });

        it("does not render banner", () => {
          cy.wait("@getGeolocation");
          cy.get("div#fides-banner").should("not.exist");
        });

        it("hides the modal link", () => {
          cy.get("#fides-modal-link").should("not.be.visible");
        });
      });
    });

    describe("when experience is not provided, and geolocation is invalid", () => {
      beforeEach(() => {
        stubConfig({
          experience: OVERRIDE.UNDEFINED,
          geolocation: {
            country: "US",
            location: "",
            region: "",
          },
          options: {
            isGeolocationEnabled: true,
            geolocationApiUrl: "https://some-geolocation-api.com",
          },
        });
      });

      it("fetches geolocation and experience and renders the banner", () => {
        cy.wait("@getGeolocation");
        cy.wait("@getPrivacyExperience").then((interception) => {
          expect(interception.request.query.region).to.eq("us_ca");
        });
        cy.get("div#fides-banner").should("exist");
        cy.get("div#fides-banner").within(() => {
          cy.contains("button", "Opt in to all").should("exist");
          cy.get(
            "div#fides-banner-description.fides-banner-description",
          ).contains("[banner] We use cookies and similar methods");
        });
      });

      it("renders modal link", () => {
        cy.get("#fides-modal-link").should("be.visible");
      });
    });

    describe("when experience is not provided, and geolocation is not provided, but geolocation is disabled", () => {
      beforeEach(() => {
        stubConfig({
          experience: OVERRIDE.UNDEFINED,
          geolocation: OVERRIDE.UNDEFINED,
          options: {
            isGeolocationEnabled: false,
          },
        });
      });

      it("does not render banner", () => {
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("div#fides-banner").should("not.exist");
        });
      });

      it("does not render modal link", () => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    describe("when experience contains no notices", () => {
      beforeEach(() => {
        stubConfig({
          experience: {
            privacy_notices: [],
          },
        });
      });

      it("does not render banner", () => {
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("div#fides-banner").should("not.exist");
        });
      });

      it("does not render modal link", () => {
        cy.get("#fides-modal-link").should("not.be.visible");
      });
    });

    describe("when all notices have current user preferences set and GPC flag exists", () => {
      beforeEach(() => {
        cy.on("window:before:load", (win) => {
          // eslint-disable-next-line no-param-reassign
          win.navigator.globalPrivacyControl = true;
        });
        // create cookie with matching notice key since we rely on it to determine whether to resurface consent
        const uuid = "4fbb6edf-34f6-4717-a6f1-52o47rybwuafh5";
        const CREATED_DATE = "2022-12-24T12:00:00.000Z";
        const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
        const notices = {
          advertising: true,
        };
        const originalCookie = {
          identity: { fides_user_device_id: uuid },
          fides_meta: {
            version: "0.9.0",
            createdAt: CREATED_DATE,
            updatedAt: UPDATED_DATE,
          },
          consent: notices,
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));
        stubConfig({
          experience: {
            privacy_notices: [
              mockPrivacyNotice({
                title: "Advertising",
                id: "pri_notice-advertising",
                has_gpc_flag: true,
                consent_mechanism: ConsentMechanism.OPT_IN,
                default_preference: UserConsentPreference.OPT_IN,
              }),
            ],
          },
        });
      });

      it("does not render banner", () => {
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("div#fides-banner").should("not.exist");
        });
      });

      it("renders modal link", () => {
        cy.get("#fides-modal-link").should("be.visible");
      });

      it("does not set user consent preference automatically", () => {
        // timeout means API call not made, which is expected
        cy.on("fail", (error) => {
          if (error.message.indexOf("Timed out retrying") !== 0) {
            throw error;
          }
        });
        // check that preferences aren't sent to Fides API
        cy.wait("@patchPrivacyPreference", {
          requestTimeout: 500,
        }).then((xhr) => {
          assert.isNull(xhr?.response?.body);
        });
        // check that Fides consent obj is empty
        cy.window().its("Fides").its("consent").should("eql", {});
        // check that preferences do not exist in cookie
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      });

      it("shows gpc indicators in modal", () => {
        cy.get("#fides-modal-link").click();
        cy.get("div.fides-gpc-banner").contains(
          "Global Privacy Control detected",
        );
        cy.get("span").contains("Advertising");
        cy.get("span").contains("Global Privacy Control Overridden");
      });
    });

    describe("when banner should not be shown but modal link element exists", () => {
      beforeEach(() => {
        cy.fixture("consent/fidesjs_options_banner_modal.json").then(
          (config) => {
            stubConfig({
              experience: {
                experience_config: {
                  ...config.experience.experience_config,
                  ...{ component: ComponentType.MODAL },
                },
              },
            });
          },
        );
      });

      it("does not render banner", () => {
        cy.waitUntilFidesInitialized().then(() => {
          cy.get("div#fides-banner").should("not.exist");
        });
      });

      describe("modal link", () => {
        it("is visible", () => {
          cy.get("#fides-modal-link").should("be.visible");
        });

        it("opens modal when clicked", () => {
          cy.get("#fides-modal-link").should("be.visible").click();
          cy.getByTestId("consent-modal").should("be.visible");
        });

        it(
          "gets binded to the click handler even after a delay in appearing in the DOM",
          { defaultCommandTimeout: 200 },
          () => {
            const delay = 1000;
            cy.on("window:before:load", (win: { render_delay: number }) => {
              // eslint-disable-next-line no-param-reassign
              win.render_delay = delay;
            });
            cy.fixture("consent/fidesjs_options_banner_modal.json").then(
              (config) => {
                stubConfig({
                  experience: {
                    experience_config: {
                      ...config.experience.experience_config,
                      ...{ component: ComponentType.MODAL },
                    },
                  },
                });
              },
            );
            cy.get("#fides-modal-link").should("not.exist");
            // eslint-disable-next-line cypress/no-unnecessary-waiting
            cy.wait(delay); // wait until delay is over
            cy.get("#fides-modal-link").should("be.visible").click();
            cy.getByTestId("consent-modal").should("be.visible");
          },
        );
      });
    });

    describe("when both banner is shown and modal link element exists", () => {
      beforeEach(() => {
        cy.fixture("consent/fidesjs_options_banner_modal.json").then(
          (config) => {
            stubConfig({ experience: config.experience });
          },
        );
      });

      it("closes banner and opens modal when modal link is clicked", () => {
        cy.get("div#fides-banner").should("be.visible");
        cy.get("div#fides-banner").within(() => {
          cy.contains("button", "Opt in to all").should("exist");
        });

        cy.get("#fides-modal-link").click();
        cy.get("div#fides-banner").should("not.be.visible");
        cy.getByTestId("consent-modal").should("be.visible");
      });

      it("opens modal even after modal has been previously opened and closed", () => {
        cy.contains("button", "Manage preferences").click();

        // Save new preferences
        cy.getByTestId("toggle-Advertising").click();
        cy.getByTestId("toggle-Essential").click();
        cy.getByTestId("Save-btn").click();

        cy.get("#fides-modal-link").click();
        cy.getByTestId("consent-modal").should("be.visible");
      });
    });

    describe("when resurfacing consent banner", () => {
      it("shows consent banner when no saved consent exists", () => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubConfig({
          options: {
            isOverlayEnabled: true,
          },
        });
        cy.get("div#fides-banner").should("be.visible");
      });

      it("does not resurface consent banner when saved consent exists for all notices", () => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        stubConfig({
          options: {
            isOverlayEnabled: true,
          },
        });
        cy.get("div#fides-banner").should("be.visible");
        cy.get("#fides-banner .fides-accept-all-button").click();

        // Reload the page, except this time with our saved consent cookie
        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME);
        stubConfig({
          options: {
            isOverlayEnabled: true,
          },
        });
        cy.get("div#fides-banner").should("not.exist");
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [PRIVACY_NOTICE_KEY_1]: true,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });
      });

      it("resurfaces consent banner when saved consent is missing for a notice", () => {
        // Save a consent cookie with preferences for only the "advertising" test notice
        const cookie = {
          identity: {
            fides_user_device_id: "4fbb6edf-34f6-4717-a6f1-541fd1e5d585",
          },
          fides_meta: {
            version: "0.9.0",
            createdAt: "2022-12-24T12:00:00.000Z",
            updatedAt: "2022-12-25T12:00:00.000Z",
          },
          consent: {
            advertising: false,
          },
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(cookie));

        // Load the page with all three test notices (advertising, essential,
        // analytics_opt_out). Since saved consent should only exist for
        // "advertising", expect the banner to resurface
        stubConfig({
          options: {
            isOverlayEnabled: true,
          },
        });
        cy.get("div#fides-banner").should("be.visible");
      });
    });

    describe("Automatically set preferences", () => {
      describe("Reject all", () => {
        const validateRejectAll = (interception: any) => {
          const { body } = interception.request;
          const expectedPreferences = [
            {
              preference: "opt_out",
              privacy_notice_history_id:
                "pri_notice-history-advertising-en-000",
            },
            {
              preference: "opt_out",
              privacy_notice_history_id: "pri_notice-history-analytics-en-000",
            },
            {
              preference: "acknowledge",
              privacy_notice_history_id: "pri_notice-history-essential-en-000",
            },
          ];
          cy.wrap(body.preferences).should(
            "deep.include.members",
            expectedPreferences,
          );
          cy.wrap(expectedPreferences).should(
            "deep.include.members",
            body.preferences,
          );
          expect(body.method).to.eql(ConsentMethod.SCRIPT);
        };
        it("rejects all notices automatically when set", () => {
          stubConfig({
            options: {
              fidesConsentOverride: ConsentMethod.REJECT,
            },
          });
          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateRejectAll(interception);
            });
          });
        });

        it("rejects all notices automatically when set via cookie", () => {
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
          cy.getCookie("fides_consent_override").should("not.exist");
          cy.setCookie("fides_consent_override", ConsentMethod.REJECT);
          stubConfig({});

          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateRejectAll(interception);
            });
          });
        });

        it("rejects all notices automatically when set via query param", () => {
          cy.getCookie("fides_string").should("not.exist");
          stubConfig({}, null, null, {
            fides_consent_override: ConsentMethod.REJECT,
          });

          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateRejectAll(interception);
            });
          });
        });

        it("rejects all notices automatically when set via window obj", () => {
          cy.getCookie("fides_string").should("not.exist");
          stubConfig({}, null, null, null, {
            fides_consent_override: ConsentMethod.REJECT,
          });

          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateRejectAll(interception);
            });
          });
        });
      });

      describe("Accept all", () => {
        const validateAcceptAll = (interception: any) => {
          const { body } = interception.request;
          const expectedPreferences = [
            {
              preference: "opt_in",
              privacy_notice_history_id:
                "pri_notice-history-advertising-en-000",
            },
            {
              preference: "opt_in",
              privacy_notice_history_id: "pri_notice-history-analytics-en-000",
            },
            {
              preference: "acknowledge",
              privacy_notice_history_id: "pri_notice-history-essential-en-000",
            },
          ];
          cy.wrap(body.preferences).should(
            "deep.include.members",
            expectedPreferences,
          );
          cy.wrap(expectedPreferences).should(
            "deep.include.members",
            body.preferences,
          );
          expect(body.method).to.eql(ConsentMethod.SCRIPT);
        };
        it("accepts all notices automatically when set", () => {
          stubConfig({
            options: {
              fidesConsentOverride: ConsentMethod.ACCEPT,
            },
          });
          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateAcceptAll(interception);
            });
          });
        });

        it("accepts all notices automatically when set via cookie", () => {
          cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
          cy.getCookie("fides_consent_override").should("not.exist");
          cy.setCookie("fides_consent_override", ConsentMethod.ACCEPT);
          stubConfig({});

          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateAcceptAll(interception);
            });
          });
        });

        it("accepts all notices automatically when set via query param", () => {
          cy.getCookie("fides_string").should("not.exist");
          stubConfig({}, null, null, {
            fides_consent_override: ConsentMethod.ACCEPT,
          });

          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateAcceptAll(interception);
            });
          });
        });

        it("accepts all notices automatically when set via window obj", () => {
          cy.getCookie("fides_string").should("not.exist");
          stubConfig({}, null, null, null, {
            fides_consent_override: ConsentMethod.ACCEPT,
          });

          cy.waitUntilFidesInitialized().then(() => {
            cy.wait("@patchPrivacyPreference").then((interception) => {
              validateAcceptAll(interception);
            });
          });
        });
      });
    });

    it("should display notice-only notices first in the toggle list", () => {
      // Create a mix of notice types with different consent mechanisms
      const notices = [
        mockPrivacyNotice({
          title: "Regular Notice",
          id: "pri_notice-regular",
          notice_key: "regular",
          consent_mechanism: ConsentMechanism.OPT_IN,
        }),
        mockPrivacyNotice({
          title: "Notice Only First",
          id: "pri_notice-only-first",
          notice_key: "notice_only_first",
          consent_mechanism: ConsentMechanism.NOTICE_ONLY,
        }),
        mockPrivacyNotice({
          title: "Another Regular",
          id: "pri_notice-another",
          notice_key: "another",
          consent_mechanism: ConsentMechanism.OPT_OUT,
        }),
        mockPrivacyNotice({
          title: "Notice Only Second",
          id: "pri_notice-only-second",
          notice_key: "notice_only_second",
          consent_mechanism: ConsentMechanism.NOTICE_ONLY,
        }),
      ];

      stubConfig({
        experience: {
          privacy_notices: notices,
        },
      });

      // Open the modal
      cy.contains("button", "Manage preferences").click();

      // Get all notice toggles
      cy.get(".fides-notice-toggle").then(($toggles) => {
        // First two toggles should be notice-only
        cy.wrap($toggles[0]).contains("Notice Only First");
        cy.wrap($toggles[1]).contains("Notice Only Second");
        // Followed by regular notices
        cy.wrap($toggles[2]).contains("Regular Notice");
        cy.wrap($toggles[3]).contains("Another Regular");
      });
    });
  });

  describe("when listening for fides.js events", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
      });
      cy.get("@FidesInitializing").should("have.been.calledOnce");
    });

    // NOTE: See definition of cy.visitConsentDemo in commands.ts for where we
    // register listeners for these window events
    it("emits a FidesReady but not any subsequent events when initialized", () => {
      cy.window()
        .its("Fides")
        .its("consent")
        .should("eql", {
          [PRIVACY_NOTICE_KEY_1]: false,
          [PRIVACY_NOTICE_KEY_2]: true,
          [PRIVACY_NOTICE_KEY_3]: true,
        });
      cy.get("@FidesReady")
        .should("have.been.calledOnce")
        .its("firstCall.args.0.detail.consent")
        .should("deep.equal", {
          [PRIVACY_NOTICE_KEY_1]: false,
          [PRIVACY_NOTICE_KEY_2]: true,
          [PRIVACY_NOTICE_KEY_3]: true,
        });
      cy.get("@FidesUpdating").should("not.have.been.called");
      cy.get("@FidesUpdated").should("not.have.been.called");
      cy.get("@FidesUIShown").should("not.have.been.called");
      cy.get("@FidesUIChanged").should("not.have.been.called");
    });

    describe("when preferences are changed / saved", () => {
      it("emits FidesUpdating -> FidesUpdated events when reject all is clicked", () => {
        cy.get("@FidesReady")
          // First event, before the user rejects all
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });
        cy.get("div#fides-banner").within(() => {
          cy.contains("button", "Opt out of all").click();
        });
        cy.get("@FidesUIChanged").should("not.have.been.called");
        cy.get("@FidesUpdating")
          // Updating event, when the user rejects all
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: false,
          });
        cy.get("@FidesUpdated")
          // Updated event, when the preferences have finished updating
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: false,
          });
        cy.get("@FidesUpdated")
          .its("lastCall.args.0.detail.extraDetails.consentMethod")
          .then((consentMethod) => {
            expect(consentMethod).to.eql(ConsentMethod.REJECT);
          });
      });
      it("emits FidesUpdating -> FidesUpdated events when accept all is clicked", () => {
        cy.get("@FidesReady")
          // First event, before the user accepts all
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });
        cy.get("div#fides-banner").within(() => {
          cy.contains("button", "Opt in to all").should("be.visible").click();
        });
        cy.get("@FidesUIChanged").should("not.have.been.called");
        cy.get("@FidesUpdating")
          // Updating event, when the user accepts all
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: true,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });
        cy.get("@FidesUpdated")
          // Updated event, when the preferences have finished updating
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: true,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });
        cy.get("@FidesUpdated")
          .its("lastCall.args.0.detail.extraDetails.consentMethod")
          .then((consentMethod) => {
            expect(consentMethod).to.eql(ConsentMethod.ACCEPT);
          });
      });

      it("emits a FidesUIChanged event when preferences are changed and FidesUpdating -> FidesUpdated events when preferences are saved", () => {
        cy.contains("button", "Manage preferences")
          .should("be.visible")
          .click();
        cy.get("@FidesReady")
          // First event, before the user saved preferences
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });

        // Toggle the notice, but don't save yet
        cy.getByTestId("toggle-Advertising").click();
        cy.get("@FidesUIChanged").its("callCount").should("equal", 1);
        cy.get("@FidesUIChanged")
          .its("firstCall.args.0")
          .then((event: CustomEvent) => {
            // Check that the extraDetails includes context about what changed
            expect(event.type).to.equal("FidesUIChanged");
            expect(event.detail.extraDetails).to.have.property("trigger");
            expect(event.detail.extraDetails.trigger).to.deep.include({
              label: "Advertising",
              checked: true,
            });
            expect(event.detail.extraDetails.preference).to.deep.include({
              key: "advertising",
              type: "notice",
            });
          });
        cy.get("@FidesUpdating").should("not.have.been.called");
        cy.get("@FidesUpdated").should("not.have.been.called");

        // Save the changes
        cy.getByTestId("consent-modal").contains("Save").click();
        cy.get("@FidesUIChanged").should("have.been.calledOnce"); // still only once
        cy.get("@FidesUpdating")
          // Updating event, when the user saved preferences and opted-in to the first notice
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: true,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });
        cy.get("@FidesUpdated")
          // Updated event, when the preferences have finished updating
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: true,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });
        cy.get("@FidesUpdated")
          .its("lastCall.args.0.detail.extraDetails.consentMethod")
          .then((consentMethod) => {
            expect(consentMethod).to.eql(ConsentMethod.SAVE);
          });
      });
    });
  });

  describe("when listening for fides.js events with existing cookie", () => {
    describe("when overlay is enabled and legacy notices exist", () => {
      it("reflects client-side experiences consent in the UI", () => {
        const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
        const CREATED_DATE = "2022-12-24T12:00:00.000Z";
        const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
        const legacyNotices = {
          data_sales: false,
          tracking: false,
          analytics: true,
        };
        const originalCookie = {
          identity: { fides_user_device_id: uuid },
          fides_meta: {
            version: "0.9.0",
            createdAt: CREATED_DATE,
            updatedAt: UPDATED_DATE,
          },
          consent: legacyNotices,
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));

        // we need to visit the page after the cookie exists, so the Fides.consent obj is initialized with the original
        // cookie values
        stubConfig({
          experience: OVERRIDE.UNDEFINED,
          geolocation: {
            country: "US",
            location: "US-CA",
            region: "CA",
          },
        });
        cy.getCookie(CONSENT_COOKIE_NAME).should("exist");
        cy.contains("button", "Manage preferences").click();
        // Default preference opt-out
        cy.getByTestId("toggle-Advertising").within(() => {
          cy.get("input").should("not.be.checked");
        });
        // Default preference opt-in
        cy.getByTestId("toggle-Analytics").within(() => {
          cy.get("input").should("be.checked");
        });
      });

      // NOTE: See definition of cy.visitConsentDemo in commands.ts for where we
      // register listeners for these window events
      it("first event reflects legacy consent from cookie, second event reflects new experiences consent", () => {
        const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
        const CREATED_DATE = "2022-12-24T12:00:00.000Z";
        const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
        const legacyNotices = {
          data_sales: false,
          tracking: false,
          analytics: true,
        };
        const originalCookie = {
          identity: { fides_user_device_id: uuid },
          fides_meta: {
            version: "0.9.0",
            createdAt: CREATED_DATE,
            updatedAt: UPDATED_DATE,
          },
          consent: legacyNotices,
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));

        // we need to visit the page after the cookie exists, so the Fides.consent obj is initialized with the original
        // cookie values
        stubConfig({
          options: {
            isOverlayEnabled: true,
          },
        });
        // There is a brief period of time when Fides.consent is set to the legacy values, but this
        // test asserts the new values have been set
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });
        cy.get("@FidesConsentLoaded")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            data_sales: false,
            tracking: false,
            analytics: true,
          });
        cy.get("@FidesReady")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });
      });
    });

    describe("when overlay is enabled and legacy notices do not exist", () => {
      beforeEach(() => {
        const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
        const CREATED_DATE = "2022-12-24T12:00:00.000Z";
        const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
        const legacyNotices = {
          data_sales: false,
          tracking: false,
          analytics: true,
        };
        const originalCookie = {
          identity: { fides_user_device_id: uuid },
          fides_meta: {
            version: "0.9.0",
            createdAt: CREATED_DATE,
            updatedAt: UPDATED_DATE,
          },
          consent: legacyNotices,
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));

        stubConfig({
          options: {
            isOverlayEnabled: true,
          },
          consent: { options: [] },
        });
      });

      it("first event reflects legacy consent options, second event reflects new experiences consent", () => {
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });
        cy.get("@FidesConsentLoaded")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            data_sales: false,
            tracking: false,
            analytics: true,
          });
        cy.get("@FidesReady")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });
      });
    });

    describe("when overlay is disabled and legacy notices do not exist", () => {
      beforeEach(() => {
        const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
        const CREATED_DATE = "2022-12-24T12:00:00.000Z";
        const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
        const legacyNotices = {
          data_sales: false,
          tracking: false,
          analytics: true,
        };
        const originalCookie = {
          identity: { fides_user_device_id: uuid },
          fides_meta: {
            version: "0.9.0",
            createdAt: CREATED_DATE,
            updatedAt: UPDATED_DATE,
          },
          consent: legacyNotices,
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));

        stubConfig({
          options: {
            isOverlayEnabled: false,
          },
          consent: { options: [] },
        });
      });

      // NOTE: See definition of cy.visitConsentDemo in commands.ts for where we
      // register listeners for these window events
      it("all events should reflect existing legacy cookie values", () => {
        cy.window().its("Fides").its("consent").should("eql", {
          data_sales: false,
          tracking: false,
          analytics: true,
        });
        cy.get("@FidesConsentLoaded")
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            data_sales: false,
            tracking: false,
            analytics: true,
          });
      });
    });

    describe("when overlay is disabled and legacy notices exist", () => {
      beforeEach(() => {
        const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
        const CREATED_DATE = "2022-12-24T12:00:00.000Z";
        const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
        const legacyNotices = {
          data_sales: false,
          tracking: false,
          analytics: true,
        };
        const originalCookie = {
          identity: { fides_user_device_id: uuid },
          fides_meta: {
            version: "0.9.0",
            createdAt: CREATED_DATE,
            updatedAt: UPDATED_DATE,
          },
          consent: legacyNotices,
        };
        cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));

        stubConfig({
          options: {
            isOverlayEnabled: false,
          },
        });
      });

      // NOTE: See definition of cy.visitConsentDemo in commands.ts for where we
      // register listeners for these window events
      it("all events should reflect legacy consent from cookie", () => {
        cy.window().its("Fides").its("consent").should("eql", {
          data_sales: false,
          tracking: false,
          analytics: true,
        });
        cy.get("@FidesConsentLoaded")
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .should("deep.equal", {
            data_sales: false,
            tracking: false,
            analytics: true,
          });
      });
    });
  });

  describe("gpc indicators in the modal", () => {
    beforeEach(() => {
      cy.on("window:before:load", (win) => {
        // eslint-disable-next-line no-param-reassign
        win.navigator.globalPrivacyControl = true;
      });
    });

    it("renders the proper gpc indicator", () => {
      // Create an existing cookie with preferences, to test that these will
      // override GPC defaults if present
      const uuid = "4fbb6edf-34f6-4717-a6f1-52o47rybwuafh5";
      const CREATED_DATE = "2022-12-24T12:00:00.000Z";
      const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
      const notices = {
        // we skip setting the "applied" notice key since we wish to replicate no user pref here
        notice_only: true,
        overridden: true, // this pref should override GPC setting
      };
      const originalCookie = {
        identity: { fides_user_device_id: uuid },
        fides_meta: {
          version: "0.9.0",
          createdAt: CREATED_DATE,
          updatedAt: UPDATED_DATE,
        },
        consent: notices,
      };
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));
      stubConfig({
        experience: {
          privacy_notices: [
            mockPrivacyNotice({
              title: "Applied",
              id: "pri_notice-applied",
              notice_key: "applied",
              has_gpc_flag: true,
              consent_mechanism: ConsentMechanism.OPT_IN,
              default_preference: UserConsentPreference.OPT_OUT,
            }),
            mockPrivacyNotice({
              title: "Notice only",
              notice_key: "notice_only",
              id: "pri_notice-only",
              // notice-only should never have has_gpc_flag true, but just in case,
              // make sure the expected behavior still holds if it is somehow true
              has_gpc_flag: true,
              consent_mechanism: ConsentMechanism.NOTICE_ONLY,
              default_preference: UserConsentPreference.ACKNOWLEDGE,
            }),
            mockPrivacyNotice({
              title: "Overridden",
              notice_key: "overridden",
              id: "pri_notice-overridden",
              has_gpc_flag: true,
              consent_mechanism: ConsentMechanism.OPT_OUT,
              default_preference: UserConsentPreference.OPT_IN,
            }),
          ],
        },
      });
      cy.get("#fides-modal-link").click();
      cy.get(".fides-notice-toggle")
        .contains("Applied")
        .parents(".fides-notice-toggle-title")
        .within(() => {
          cy.get(".fides-gpc-label").contains("Applied");
        });
      cy.get(".fides-notice-toggle")
        .contains("Notice only")
        .parents(".fides-notice-toggle-title")
        .within(() => {
          cy.get(".fides-gpc-label").should("not.exist");
        });
      cy.get(".fides-notice-toggle")
        .contains("Overridden")
        .parents(".fides-notice-toggle-title")
        .within(() => {
          cy.get(".fides-gpc-label").contains("Overridden");
        });
    });
  });

  describe("consent reporting APIs (notices-served, privacy-preferences)", () => {
    const historyId1 = "pri_mock_history_id_1";
    const historyId2 = "pri_mock_history_id_2";
    const buildMockNotices = (): PrivacyNotice[] => [
      mockPrivacyNotice(
        {
          title: "Data Sales and Sharing",
          id: "pri_notice-data-sales",
          notice_key: "data_sales_and_sharing",
        },
        [
          mockPrivacyNoticeTranslation({
            title: "Data Sales and Sharing",
            privacy_notice_history_id: historyId1,
          }),
        ],
      ),
      mockPrivacyNotice(
        {
          title: "Essential",
          notice_key: "essential",
          id: "pri_notice-essential",
        },
        [
          mockPrivacyNoticeTranslation({
            title: "Essential",
            privacy_notice_history_id: historyId2,
          }),
        ],
      ),
    ];

    it("can go through consent reporting flow", () => {
      stubConfig({
        experience: {
          privacy_notices: buildMockNotices(),
        },
      });
      cy.get("#fides-modal-link").click();
      cy.get("@FidesUIShown").should("have.been.calledTwice");
      cy.wait("@patchNoticesServed").then((noticesServedInterception) => {
        const { browser_identity: identity, ...body } =
          noticesServedInterception.request.body;
        expect(identity.fides_user_device_id).to.be.a("string");
        expect(body).to.eql({
          privacy_experience_config_history_id:
            "pri_exp-history-banner-modal-en-000",
          user_geography: "us_ca",
          acknowledge_mode: false,
          serving_component: "modal",
          privacy_notice_history_ids: [historyId1, historyId2],
          served_notice_history_id: body.served_notice_history_id,
        });
        expect(body.served_notice_history_id).to.be.a("string");
        const servedNoticeHistoryId = body.served_notice_history_id;

        // Now opt out of the notices
        cy.getByTestId("consent-modal").within(() => {
          cy.get("button").contains("Opt out of all").click();
        });
        // The patch should include the served notice ID (generated in the client and used in the notices-served request already)
        cy.wait("@patchPrivacyPreference").then((preferenceInterception) => {
          // eslint-disable-next-line @typescript-eslint/naming-convention
          const { served_notice_history_id } =
            preferenceInterception.request.body;
          expect(served_notice_history_id).to.eql(servedNoticeHistoryId);
          expect(preferenceInterception.request.body.method).to.eql(
            ConsentMethod.REJECT,
          );
        });
      });
    });

    it("uses consistent served_notice_history_id between manual and automated consent flows", () => {
      // Test both manual consent (via UI) and automated consent (via GPC)
      // to ensure they use the same session-level served_notice_history_id
      cy.on("window:before:load", (win) => {
        // eslint-disable-next-line no-param-reassign
        win.navigator.globalPrivacyControl = true;
      });

      stubConfig({
        experience: {
          privacy_notices: [
            mockPrivacyNotice({
              title: "Advertising with GPC enabled",
              id: "pri_notice-advertising",
              notice_key: "advertising_gpc",
              has_gpc_flag: true,
              consent_mechanism: ConsentMechanism.OPT_OUT,
            }),
            ...buildMockNotices(),
          ],
        },
      });

      let automatedServedNoticeHistoryId: string;
      let manualServedNoticeHistoryId: string;

      // First, automated consent should be applied via GPC
      cy.wait("@patchPrivacyPreference").then((gpcInterception) => {
        const { served_notice_history_id } = gpcInterception.request.body;
        expect(served_notice_history_id).to.be.a("string");
        automatedServedNoticeHistoryId = served_notice_history_id;
        expect(gpcInterception.request.body.method).to.eql(ConsentMethod.GPC);
      });

      // Then, open the modal to trigger notices-served
      cy.get("#fides-modal-link").click();
      cy.wait("@patchNoticesServed").then((noticesServedInterception) => {
        const { served_notice_history_id } =
          noticesServedInterception.request.body;
        expect(served_notice_history_id).to.be.a("string");
        manualServedNoticeHistoryId = served_notice_history_id;

        // The served_notice_history_id should be the same as the automated consent
        expect(manualServedNoticeHistoryId).to.eql(
          automatedServedNoticeHistoryId,
        );
      });

      // Finally, make manual changes and save to trigger privacy-preferences
      cy.getByTestId("consent-modal").within(() => {
        // Toggle one of the non-GPC notices to trigger a manual save
        cy.getByTestId("toggle-Data Sales and Sharing").click();
        cy.get("button").contains("Save").click();
      });

      cy.wait("@patchPrivacyPreference").then((manualInterception) => {
        const { served_notice_history_id } = manualInterception.request.body;
        expect(served_notice_history_id).to.be.a("string");
        expect(manualInterception.request.body.method).to.eql(
          ConsentMethod.SAVE,
        );

        // The served_notice_history_id should be consistent across all flows
        expect(served_notice_history_id).to.eql(automatedServedNoticeHistoryId);
        expect(served_notice_history_id).to.eql(manualServedNoticeHistoryId);
      });
    });

    it("can be sent from the banner if show_layer1_notices is true", () => {
      const noticeOnlyNotices = buildMockNotices().map((notice) => ({
        ...notice,
        ...{ consent_mechanism: ConsentMechanism.NOTICE_ONLY },
      }));
      cy.fixture("consent/fidesjs_options_banner_modal.json").then((config) => {
        stubConfig({
          experience: {
            privacy_notices: noticeOnlyNotices,
            experience_config: {
              ...config.experience.experience_config,
              show_layer1_notices: true,
            },
          },
        });
      });
      cy.get("@FidesUIShown").should("have.been.calledOnce");
      cy.wait("@patchNoticesServed").then((interception) => {
        expect(interception.request.body.serving_component).to.eql("banner");
      });
    });

    it("can set acknowledge mode to true", () => {
      const noticeOnlyNotices = buildMockNotices().map((notice) => ({
        ...notice,
        ...{ consent_mechanism: ConsentMechanism.NOTICE_ONLY },
      }));
      stubConfig({
        experience: {
          privacy_notices: noticeOnlyNotices,
        },
      });
      cy.get("@FidesUIShown").should("have.been.calledOnce");
      cy.get("#fides-modal-link").click();
      cy.wait("@patchNoticesServed").then((interception) => {
        expect(interception.request.body.acknowledge_mode).to.eql(true);
      });
    });

    it("can call custom notices served fn instead of Fides API", () => {
      /* eslint-disable @typescript-eslint/no-unused-vars */
      const apiOptions = {
        patchNoticesServedFn: async (request: RecordConsentServedRequest) =>
          null,
      };
      /* eslint-enable @typescript-eslint/no-unused-vars */
      const spyObject = cy.spy(apiOptions, "patchNoticesServedFn");
      stubConfig({
        experience: {
          privacy_notices: buildMockNotices(),
        },
        options: {
          apiOptions,
        },
      });
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").should("not.have.been.called");
        cy.get("#fides-modal-link").click();
        cy.get("@FidesUIShown").then(() => {
          // eslint-disable-next-line @typescript-eslint/no-unused-expressions
          expect(spyObject).to.be.called;
          const spy = spyObject.getCalls();
          const { args } = spy[0];
          expect(args[0]).to.contains({
            serving_component: "modal",
          });
          // timeout means API call not made, which is expected
          cy.on("fail", (error) => {
            if (error.message.indexOf("Timed out retrying") !== 0) {
              throw error;
            }
          });
          // check that notices aren't patched to Fides API
          cy.wait("@patchNoticesServed", {
            requestTimeout: 100,
          }).then((xhr) => {
            assert.isNull(xhr?.response?.body);
          });
        });
      });
    });

    it("when fides_disable_save_api option is set, disables notices-served & privacy-preferences APIs", () => {
      stubConfig({
        experience: {
          privacy_notices: buildMockNotices(),
        },
        options: {
          fidesDisableSaveApi: true,
        },
      });
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").should("not.have.been.called");
        cy.get("#fides-modal-link").click();

        // Check that notices-served API is not called when the modal is shown
        cy.get("@FidesUIShown").then(() => {
          cy.on("fail", (error) => {
            if (error.message.indexOf("Timed out retrying") !== 0) {
              throw error;
            }
          });
          cy.wait("@patchNoticesServed", {
            requestTimeout: 100,
          }).then((xhr) => {
            assert.isNull(xhr?.response?.body);
          });
        });

        // Also, check that privacy-preferences API is not called after saving
        cy.getByTestId("Save-btn").click();
        cy.get("@FidesUpdated").then(() => {
          cy.on("fail", (error) => {
            if (error.message.indexOf("Timed out retrying") !== 0) {
              throw error;
            }
          });
          cy.wait("@patchPrivacyPreference", {
            requestTimeout: 100,
          }).then((xhr) => {
            assert.isNull(xhr?.response?.body);
          });
        });
      });
    });

    it("when fides_disable_notices_served_api option is set, only disables notices-served API", () => {
      stubConfig({
        experience: {
          privacy_notices: buildMockNotices(),
        },
        options: {
          fidesDisableNoticesServedApi: true,
        },
      });
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesUIShown").should("not.have.been.called");
        cy.get("#fides-modal-link").click();

        // Check that notices-served API is not called when the modal is shown
        cy.get("@FidesUIShown").then(() => {
          cy.on("fail", (error) => {
            if (error.message.indexOf("Timed out retrying") !== 0) {
              throw error;
            }
          });
          cy.wait("@patchNoticesServed", {
            requestTimeout: 100,
          }).then((xhr) => {
            assert.isNull(xhr?.response?.body);
          });
        });

        // Also, check that privacy-preferences API is called after saving
        cy.getByTestId("Save-btn").click();
        cy.get("@FidesUpdated").then(() => {
          cy.wait("@patchPrivacyPreference", {
            requestTimeout: 100,
          }).then((xhr) => {
            assert.isNotNull(xhr?.response?.body);
          });
        });
      });
    });
  });

  describe("consent overlay buttons", () => {
    it("only shows the save button when a single privacy notice is configured", () => {
      stubConfig({
        experience: {
          privacy_notices: [
            mockPrivacyNotice({
              title: "Marketing",
              id: "pri_notice-marketing",
              has_gpc_flag: true,
            }),
          ],
        },
      });
      cy.get("button").contains("Manage preferences").click();
      cy.get(".fides-modal-primary-actions")
        .find("button")
        .should("have.length", 1);
    });
    it("shows all buttons when multiple privacy notices are configured", () => {
      stubConfig({
        experience: {
          privacy_notices: [
            mockPrivacyNotice({
              title: "Marketing",
              id: "pri_notice-marketing",
              has_gpc_flag: true,
            }),
            mockPrivacyNotice({
              title: "Functional",
              id: "pri_notice-functional",
              has_gpc_flag: true,
            }),
          ],
        },
      });
      cy.get("button").contains("Manage preferences").click();
      cy.get(".fides-modal-primary-actions")
        .find("button")
        .should("have.length", 3);
    });
  });

  describe("fides overrides", () => {
    describe("when set via window obj", () => {
      it("applies primary color override", () => {
        const overrides = {
          fides_primary_color: "#999000",
        };
        cy.fixture("consent/experience_banner_modal.json").then(
          (experience) => {
            stubConfig(
              {
                options: {
                  customOptionsPath: TEST_OVERRIDE_WINDOW_PATH,
                },
                experience: experience.items[0],
              },
              null,
              null,
              undefined,
              { ...overrides },
            );
          },
        );
        cy.get("div#fides-banner .fides-accept-all-button").should(
          "have.css",
          "background-color",
          "rgb(153, 144, 0)",
        );
      });
      it("applies fides_disabled_notices override", () => {
        // Disable the analytics notice which is opted in by default
        let overrides = {
          fides_disabled_notices: "analytics_opt_out",
        };
        cy.fixture("consent/experience_banner_modal.json").then(() => {
          stubConfig(
            {
              options: {
                customOptionsPath: TEST_OVERRIDE_WINDOW_PATH,
              },
            },
            null,
            null,
            { ...overrides },
          );
        });
        cy.get("button").contains("Manage preferences").click();
        cy.getByTestId("toggle-Analytics").find("input").should("be.disabled"); // disabled by override
        cy.getByTestId("toggle-Analytics").find("input").should("be.checked"); // opted in by default
        cy.getByTestId("toggle-Advertising")
          .find("input")
          .should("not.be.disabled"); // unaffected by override
        cy.getByTestId("toggle-Advertising")
          .find("input")
          .should("not.be.checked"); // opted out by default

        // Opt out of all has no effect
        cy.getByTestId("fides-modal-content")
          .contains("button", "Opt out of all")
          .should("be.visible")
          .click();
        cy.getByTestId("toggle-Analytics").find("input").should("be.checked"); // still opted in
      });
    });
  });

  describe("when using Fides.reinitialize() SDK function", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
      });
    });

    it("reinitializes FidesJS and loads any changed options", () => {
      // First, it should initialize normally and show the banner
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesReady").should("have.callCount", 1);
        cy.get("#fides-overlay .fides-banner").should("exist");
        cy.get("#fides-overlay .fides-banner").should(
          "have.class",
          "fides-banner-hidden",
        );
        cy.get("#fides-overlay .fides-banner").should(
          "not.have.class",
          "fides-banner-hidden",
        );
        cy.get("#fides-embed-container .fides-banner").should("not.exist");
        cy.get("#fides-embed-container .fides-modal-body").should("not.exist");
      });

      // Call reinitialize() without making any changes
      cy.window().then((win) => {
        win.Fides.init();
      });

      // FidesJS should re-initialize and re-show the banner
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesReady").should("have.callCount", 2);
        cy.get("#fides-overlay .fides-banner").should("exist");
        cy.get("#fides-embed-container .fides-banner").should("not.exist");
        cy.get("#fides-embed-container .fides-modal-body").should("not.exist");

        // Ensure the .fides-banner-hidden class is added & removed again (foranimation)
        cy.get("#fides-overlay .fides-banner").should(
          "have.class",
          "fides-banner-hidden",
        );
        cy.get("#fides-overlay .fides-banner").should(
          "not.have.class",
          "fides-banner-hidden",
        );
      });

      // Next, change some Fides options to enable embed and reinitialize()
      cy.window().then((win) => {
        // @ts-ignore
        // eslint-disable-next-line no-param-reassign
        win.fides_overrides = {
          fides_embed: true,
          fides_disable_banner: false,
        };
        win.Fides.init();
      });

      // FidesJS should initialize again, in embedded mode this time
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesReady").should("have.callCount", 3);
        cy.get("#fides-overlay .fides-banner").should("not.exist");
        cy.get("#fides-embed-container .fides-banner").should("exist");
        cy.get("#fides-embed-container .fides-modal-body").should("not.exist");
      });

      // Change the options  and reinitialize() again
      cy.window().then((win) => {
        // @ts-ignore
        // eslint-disable-next-line no-param-reassign
        win.fides_overrides = {
          fides_embed: true,
          fides_disable_banner: true,
        };
        win.Fides.init();
      });

      // FidesJS should initialize once again, without any banners
      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesReady").should("have.callCount", 4);
        cy.get("#fides-overlay .fides-banner").should("not.exist");
        cy.get("#fides-embed-container .fides-banner").should("not.exist");
        cy.get("#fides-embed-container .fides-modal-body").should("exist");
      });
    });
  });

  describe("when initialization has been disabled by the developer", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      cy.visit({
        url: "/fides-js-demo.html",
        qs: { initialize: "false" },
      });
      cy.window().then((win) => {
        win.addEventListener("FidesReady", cy.stub().as("FidesReady"));
      });
    });
    it("does not trigger any side-effects (like banners displaying, events firing, etc.)", () => {
      cy.window().then((win) => {
        assert.isTrue(!!win.Fides.config);
        assert.isFalse(win.Fides.initialized);
      });
      cy.get("@FidesReady").should("not.have.been.called");
      cy.get("#fides-overlay .fides-banner").should("not.exist");
    });
    it("can still be initialized manually by the developer after adjusting settings", () => {
      cy.window().then((win) => {
        win.Fides.init().then(() => {
          assert.isTrue(win.Fides.initialized);
        });
      });
    });
  });

  describe("when using overrides for consent mechanism flags and non-applicable notices", () => {
    describe("when using consent mechanism flags and OMIT mode for non-applicable notices", () => {
      beforeEach(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        const nonApplicableNotices = ["functional", "personalization"];

        // Create experience with non-applicable notices
        cy.fixture("consent/experience_banner_modal.json").then((data) => {
          const experience = data.items[0];
          experience.non_applicable_privacy_notices = nonApplicableNotices;

          stubConfig({
            experience,
            options: {
              isOverlayEnabled: true,
              fidesConsentFlagType: ConsentFlagType.CONSENT_MECHANISM,
              // Default is OMIT, so we don't need to specify fidesConsentNonApplicableFlagMode
            },
          });
        });
      });

      it("initializes the options correctly", () => {
        cy.window().then((win) => {
          expect(win.Fides.options).to.have.property(
            "fidesConsentFlagType",
            ConsentFlagType.CONSENT_MECHANISM,
          );
        });
      });

      it("initializes with the correct consent values", () => {
        cy.window().then((win) => {
          win.Fides.init().then(() => {
            expect(win.Fides.consent).to.have.property(
              PRIVACY_NOTICE_KEY_1,
              "opt_out",
            );
            expect(win.Fides.consent).to.have.property(
              PRIVACY_NOTICE_KEY_2,
              "acknowledge",
            );
            expect(win.Fides.consent).to.have.property(
              PRIVACY_NOTICE_KEY_3,
              "opt_in",
            );
            expect(win.Fides.consent).to.not.have.property("functional");
            expect(win.Fides.consent).to.not.have.property("personalization");
          });
        });
      });

      it("formats FidesReady events with consent mechanism strings and omits non-applicable notices", () => {
        cy.get("@FidesReady")
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .then((consent) => {
            // Check that values are formatted as strings
            expect(
              Object.values(consent).every(
                (value) => typeof value === "string",
              ),
            ).to.be.true;

            // Default values should be formatted as consent mechanism strings
            expect(consent).to.have.property(PRIVACY_NOTICE_KEY_1, "opt_out");
            expect(consent).to.have.property(
              PRIVACY_NOTICE_KEY_2,
              "acknowledge",
            );
            expect(consent).to.have.property(PRIVACY_NOTICE_KEY_3, "opt_in");

            // Non-applicable notices should NOT be included
            expect(consent).to.not.have.property("functional");
            expect(consent).to.not.have.property("personalization");
          });
      });

      // Rest of the test cases remain the same, just update assertions
      it("omits non-applicable notices in the cookie", () => {
        // Accept all preferences
        cy.get("div#fides-banner").within(() => {
          cy.contains("button", "Opt in to all").click();
        });

        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );

            // Cookie values should be strings not booleans
            expect(
              typeof cookieKeyConsent.consent[PRIVACY_NOTICE_KEY_1],
            ).to.equal("string");
            expect(
              typeof cookieKeyConsent.consent[PRIVACY_NOTICE_KEY_2],
            ).to.equal("string");
            expect(
              typeof cookieKeyConsent.consent[PRIVACY_NOTICE_KEY_3],
            ).to.equal("string");

            // Non-applicable notices should NOT exist in the cookie
            expect(cookieKeyConsent.consent).to.not.have.property("functional");
            expect(cookieKeyConsent.consent).to.not.have.property(
              "personalization",
            );
          });
        });
      });
    });

    describe("when using consent mechanism flags and non-applicable notices", () => {
      beforeEach(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        const nonApplicableNotices = ["functional", "personalization"];

        // Create experience with non-applicable notices
        cy.fixture("consent/experience_banner_modal.json").then((data) => {
          const experience = data.items[0];
          experience.non_applicable_privacy_notices = nonApplicableNotices;

          stubConfig({
            experience,
            options: {
              isOverlayEnabled: true,
              fidesConsentFlagType: ConsentFlagType.CONSENT_MECHANISM,
              fidesConsentNonApplicableFlagMode:
                ConsentNonApplicableFlagMode.INCLUDE,
            },
          });
        });
      });

      it("initializes the options correctly", () => {
        cy.window().then((win) => {
          expect(win.Fides.options).to.have.property(
            "fidesConsentFlagType",
            ConsentFlagType.CONSENT_MECHANISM,
          );
          expect(win.Fides.options).to.have.property(
            "fidesConsentNonApplicableFlagMode",
            ConsentNonApplicableFlagMode.INCLUDE,
          );
        });
      });

      it("initializes with the correct consent values", () => {
        cy.window().then((win) => {
          win.Fides.init().then(() => {
            expect(win.Fides.consent).to.have.property(
              PRIVACY_NOTICE_KEY_1,
              "opt_out",
            );
            expect(win.Fides.consent).to.have.property(
              PRIVACY_NOTICE_KEY_2,
              "acknowledge",
            );
            expect(win.Fides.consent).to.have.property(
              PRIVACY_NOTICE_KEY_3,
              "opt_in",
            );
            expect(win.Fides.consent).to.have.property(
              "functional",
              "not_applicable",
            );
            expect(win.Fides.consent).to.have.property(
              "personalization",
              "not_applicable",
            );
          });
        });
      });

      it("formats FidesReady events with consent mechanism strings", () => {
        cy.get("@FidesReady")
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .then((consent) => {
            // Check that values are formatted as strings
            expect(
              Object.values(consent).every(
                (value) => typeof value === "string",
              ),
            ).to.be.true;

            // Default values should be formatted as consent mechanism strings
            expect(consent).to.have.property(PRIVACY_NOTICE_KEY_1, "opt_out");
            expect(consent).to.have.property(
              PRIVACY_NOTICE_KEY_2,
              "acknowledge",
            );
            expect(consent).to.have.property(PRIVACY_NOTICE_KEY_3, "opt_in");

            // Non-applicable notices should be included with "not_applicable" value
            expect(consent).to.have.property("functional", "not_applicable");
            expect(consent).to.have.property(
              "personalization",
              "not_applicable",
            );
          });
      });

      // Update remaining cases with "functional" instead of "essential"
      it("formats FidesUpdated events with consent mechanism strings when changing preferences", () => {
        // Accept all preferences
        cy.get("div#fides-banner").within(() => {
          cy.contains("button", "Opt in to all").click();
        });

        cy.get("@FidesUpdated")
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .then((consent) => {
            // Check that all values are formatted as strings
            expect(
              Object.values(consent).every(
                (value) => typeof value === "string",
              ),
            ).to.be.true;

            // All applicable notices should be opt_in
            expect(consent).to.have.property(PRIVACY_NOTICE_KEY_1, "opt_in");
            expect(consent).to.have.property(
              PRIVACY_NOTICE_KEY_2,
              "acknowledge",
            );
            expect(consent).to.have.property(PRIVACY_NOTICE_KEY_3, "opt_in");

            // Non-applicable notices should be included with "not_applicable" value
            expect(consent).to.have.property("functional", "not_applicable");
            expect(consent).to.have.property(
              "personalization",
              "not_applicable",
            );
          });
      });

      it("stores consent values in the cookie with consent mechanism format", () => {
        // Accept all preferences
        cy.get("div#fides-banner").within(() => {
          cy.contains("button", "Opt in to all").click();
        });

        cy.waitUntilCookieExists(CONSENT_COOKIE_NAME).then(() => {
          cy.getCookie(CONSENT_COOKIE_NAME).then((cookie) => {
            const cookieKeyConsent: FidesCookie = JSON.parse(
              decodeURIComponent(cookie!.value),
            );

            // Cookie values should be strings not booleans
            expect(
              typeof cookieKeyConsent.consent[PRIVACY_NOTICE_KEY_1],
            ).to.equal("string");
            expect(
              typeof cookieKeyConsent.consent[PRIVACY_NOTICE_KEY_2],
            ).to.equal("string");
            expect(
              typeof cookieKeyConsent.consent[PRIVACY_NOTICE_KEY_3],
            ).to.equal("string");

            // Values should match consent mechanism strings
            expect(cookieKeyConsent.consent[PRIVACY_NOTICE_KEY_1]).to.equal(
              "opt_in",
            );
            expect(cookieKeyConsent.consent[PRIVACY_NOTICE_KEY_2]).to.equal(
              "acknowledge",
            );
            expect(cookieKeyConsent.consent[PRIVACY_NOTICE_KEY_3]).to.equal(
              "opt_in",
            );

            // Non-applicable notices should exist in the cookie
            expect(cookieKeyConsent.consent).to.have.property(
              "functional",
              "not_applicable",
            );
            expect(cookieKeyConsent.consent).to.have.property(
              "personalization",
              "not_applicable",
            );
          });
        });
      });

      // Replace all instances of checking for 'essential' toggle
      it("represents consent values correctly in the UI", () => {
        cy.contains("button", "Manage preferences").click();

        // UI should still show toggles in correct states regardless of consent value format
        cy.getByTestId("toggle-Advertising").within(() => {
          cy.get("input").should("not.be.checked");
        });
        cy.getByTestId("toggle-Essential").within(() => {
          cy.get("input").should("be.checked");
        });
        cy.getByTestId("toggle-Analytics").within(() => {
          cy.get("input").should("be.checked");
        });

        // No toggles should exist for non-applicable notices
        cy.getByTestId("toggle-functional").should("not.exist");
        cy.getByTestId("toggle-personalization").should("not.exist");
      });
    });

    describe("when using boolean flags (default) with non-applicable notices", () => {
      beforeEach(() => {
        cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
        const nonApplicableNotices = ["functional", "personalization"];

        // Create experience with non-applicable notices
        cy.fixture("consent/experience_banner_modal.json").then((data) => {
          const experience = data.items[0];
          experience.non_applicable_privacy_notices = nonApplicableNotices;

          stubConfig({
            experience,
            options: {
              isOverlayEnabled: true,
              // Not setting fidesConsentFlagType defaults to BOOLEAN
              fidesConsentNonApplicableFlagMode:
                ConsentNonApplicableFlagMode.INCLUDE,
            },
          });
        });
      });

      it("formats FidesReady events with boolean values and includes non-applicable notices", () => {
        cy.get("@FidesReady")
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .then((consent) => {
            // Check that values are formatted as booleans
            expect(
              Object.values(consent).every(
                (value) => typeof value === "boolean",
              ),
            ).to.be.true;

            // Default values should be formatted as booleans
            expect(consent).to.have.property(PRIVACY_NOTICE_KEY_1, false);
            expect(consent).to.have.property(PRIVACY_NOTICE_KEY_2, true);
            expect(consent).to.have.property(PRIVACY_NOTICE_KEY_3, true);

            // Non-applicable notices should be included with null values represented as true
            expect(consent).to.have.property("functional", true);
            expect(consent).to.have.property("personalization", true);
          });
      });

      it("formats FidesUpdated events with boolean values when changing preferences", () => {
        // Accept all preferences
        cy.get("div#fides-banner").within(() => {
          cy.contains("button", "Opt in to all").click();
        });

        cy.get("@FidesUpdated")
          .should("have.been.calledOnce")
          .its("firstCall.args.0.detail.consent")
          .then((consent) => {
            // Check that all values are formatted as booleans
            expect(
              Object.values(consent).every(
                (value) => typeof value === "boolean",
              ),
            ).to.be.true;

            // All applicable notices should be true
            expect(consent).to.have.property(PRIVACY_NOTICE_KEY_1, true);
            expect(consent).to.have.property(PRIVACY_NOTICE_KEY_2, true);
            expect(consent).to.have.property(PRIVACY_NOTICE_KEY_3, true);

            // Non-applicable notices should be included with null values represented as true
            expect(consent).to.have.property("functional", true);
            expect(consent).to.have.property("personalization", true);
          });
      });
    });
  });

  describe("when updating consent using window.Fides.updateConsent", () => {
    beforeEach(() => {
      cy.getCookie(CONSENT_COOKIE_NAME).should("not.exist");
      cy.fixture("consent/fidesjs_options_banner_modal.json").then((config) => {
        stubConfig({
          experience: {
            experience_config: {
              ...config.experience.experience_config,
              ...{ component: ComponentType.HEADLESS },
            },
          },
        });
      });
    });

    it("should update the consent cookie using consent object", () => {
      cy.window().then((win) => {
        // Initial consent
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });

        // Update consent
        win.Fides.updateConsent({
          consent: {
            [PRIVACY_NOTICE_KEY_1]: true,
            [PRIVACY_NOTICE_KEY_2]: UserConsentPreference.ACKNOWLEDGE,
            [PRIVACY_NOTICE_KEY_3]: UserConsentPreference.OPT_OUT,
          },
        });

        // Verify consent was updated
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [PRIVACY_NOTICE_KEY_1]: true,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: false,
          });
      });
    });

    it("should update the consent cookie using fidesString", () => {
      cy.window().then((win) => {
        // Initial consent
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });

        // Update consent
        win.Fides.updateConsent({
          fidesString:
            ",,,eyJhZHZlcnRpc2luZyI6dHJ1ZSwiZXNzZW50aWFsIjp0cnVlLCJhbmFseXRpY3Nfb3B0X291dCI6ZmFsc2V9",
        });

        // Verify consent was updated
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [PRIVACY_NOTICE_KEY_1]: true,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: false,
          });
      });
    });

    it("should update the consent cookie using fidesString when both are provided", () => {
      cy.window().then((win) => {
        // Initial consent
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: true,
          });

        // Update consent
        win.Fides.updateConsent({
          consent: {
            [PRIVACY_NOTICE_KEY_1]: false,
            [PRIVACY_NOTICE_KEY_2]: UserConsentPreference.ACKNOWLEDGE,
            [PRIVACY_NOTICE_KEY_3]: false,
          },
          fidesString:
            ",,,eyJhZHZlcnRpc2luZyI6dHJ1ZSwiZXNzZW50aWFsIjp0cnVlLCJhbmFseXRpY3Nfb3B0X291dCI6ZmFsc2V9",
        });

        // Verify consent was updated from the fidesString and not the consent object
        cy.window()
          .its("Fides")
          .its("consent")
          .should("eql", {
            [PRIVACY_NOTICE_KEY_1]: true,
            [PRIVACY_NOTICE_KEY_2]: true,
            [PRIVACY_NOTICE_KEY_3]: false,
          });
      });
    });
  });

  describe("FidesInitialized event support", () => {
    beforeEach(() => {
      const originalCookie = {
        identity: { fides_user_device_id: "test-user-device-id" },
        fides_meta: {
          version: "0.9.0",
          createdAt: "2022-12-24T12:00:00.000Z",
          updatedAt: "2022-12-25T12:00:00.000Z",
        },
        consent: {
          [PRIVACY_NOTICE_KEY_1]: false,
          [PRIVACY_NOTICE_KEY_2]: true,
          [PRIVACY_NOTICE_KEY_3]: true,
        },
      };
      cy.setCookie(CONSENT_COOKIE_NAME, JSON.stringify(originalCookie));
    });

    it("dispatches FidesInitialized twice when fidesInitializedEventMode is 'multiple'", () => {
      stubConfig({
        options: {
          isOverlayEnabled: true,
          fidesInitializedEventMode: "multiple",
        },
      });

      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesConsentLoaded").should("have.been.calledOnce");
        cy.get("@FidesReady").should("have.been.calledOnce");
        cy.get("@FidesInitialized").should("have.been.calledTwice");
      });
    });

    it("dispatches FidesInitialized once when fidesInitializedEventMode is default", () => {
      stubConfig({
        options: {
          isOverlayEnabled: true,
        },
      });

      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesConsentLoaded").should("have.been.calledOnce");
        cy.get("@FidesReady").should("have.been.calledOnce");
        cy.get("@FidesInitialized").should("have.been.calledOnce");
      });
    });

    it("does not dispatch FidesInitialized when fidesInitializedEventMode is 'disable'", () => {
      stubConfig({
        options: {
          isOverlayEnabled: true,
          fidesInitializedEventMode: "disable",
        },
      });

      cy.waitUntilFidesInitialized().then(() => {
        cy.get("@FidesConsentLoaded").should("have.been.calledOnce");
        cy.get("@FidesReady").should("have.been.calledOnce");
        cy.get("@FidesInitialized").should("not.have.been.called");
      });
    });
  });

  describe("when handling multiple script loading", () => {
    const waitForScriptToRun = () => {
      // wait for script to run before finishing the test
      // without this, the test will end without waiting for the thrown error to be caught resulting in a false positive!!
      // eslint-disable-next-line cypress/no-unnecessary-waiting
      cy.wait(50);
    };

    it("prevents execution when script is loaded multiple times on the same page", () => {
      cy.expectFidesAlreadyLoadedException();
      stubConfig({});

      // Wait for initial Fides to load
      cy.window().should("have.property", "Fides");

      // Spy on console.error to capture the warning message
      cy.window().then((win) => {
        // Inject a second script tag to simulate multiple loading
        const script = win.document.createElement("script");
        script.setAttribute("data-testid", "fides-js-test-script");
        script.src = "/fides.js";
        win.document.head.appendChild(script);
        waitForScriptToRun();
      });
    });

    it("allows reloading when fides_unsupported_repeated_script_loading is enabled", () => {
      stubConfig({
        options: {
          fidesUnsupportedRepeatedScriptLoading:
            "enabled_acknowledge_not_supported",
        },
      });

      // Wait for initial Fides to load
      cy.window().should("have.property", "Fides");

      cy.window().then((win) => {
        cy.spy(win.console, "error").as("consoleError");

        // Inject a second script tag
        const script = win.document.createElement("script");
        script.src =
          "/fides.js?fides_unsupported_repeated_script_loading=enabled_acknowledge_not_supported";
        win.document.head.appendChild(script);
        waitForScriptToRun();
        // an exception will automatically fail the test here because we didn't include cy.expectFidesAlreadyLoadedException()
        // If nothing happens, the test will pass. no further action is needed.
      });
    });

    it("handles script removal and re-addition scenario", () => {
      cy.expectFidesAlreadyLoadedException();
      stubConfig({});

      // Wait for initial Fides to load
      cy.window().should("have.property", "Fides");

      cy.window().then((win) => {
        // Store reference to original Fides
        const originalFides = win.Fides;

        // Find and remove the existing fides script tag
        const existingScript = win.document.querySelector(
          'script[src*="/fides.js"]',
        );
        if (existingScript) {
          existingScript.remove();
        }

        cy.spy(win.console, "error").as("consoleError");

        // Add a new script tag (simulating customer removing and re-adding)
        const newScript = win.document.createElement("script");
        newScript.src = "/fides.js";
        win.document.head.appendChild(newScript);

        waitForScriptToRun();

        // Verify that the original Fides object is still intact
        expect(win.Fides).to.equal(originalFides);
      });
    });

    it("handles multiple script tags present from page load", () => {
      cy.expectFidesAlreadyLoadedException();
      stubConfig({});
      // Create a custom test page with multiple script tags
      cy.window().then((win) => {
        // Clear the page and add multiple script tags
        win.document.body.innerHTML = `
            <div>
              <h1>Multiple Scripts Test</h1>
              <script src="/fides.js"></script>
              <script src="/fides.js"></script>
            </div>
          `;

        waitForScriptToRun();

        // Force execution of the scripts by creating new ones
        const script1 = win.document.createElement("script");
        script1.src = "/fides.js";
        const script2 = win.document.createElement("script");
        script2.src = "/fides.js";

        waitForScriptToRun();
        win.document.head.appendChild(script1);

        waitForScriptToRun();
        win.document.head.appendChild(script2);

        waitForScriptToRun();
      });
    });
  });
});
