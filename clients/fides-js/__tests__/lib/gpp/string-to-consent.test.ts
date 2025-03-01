import { CmpApi } from "@iabgpp/cmpapi";

import { CMP_VERSION } from "~/lib/gpp/constants";

import { PrivacyExperience } from "../../../src/lib/consent-types";
import {
  getConsentFromGppCmpApi,
  getTcfPreferencesFromCmpApi,
} from "../../../src/lib/gpp/string-to-consent";
import { GPPUSApproach } from "../../../src/lib/gpp/types";

// Mock window.__gpp
beforeAll(() => {
  Object.defineProperty(window, "__gpp", {
    value: jest.fn(),
    writable: true,
  });
});

describe("GPP String to Consent", () => {
  let cmpApi: CmpApi;

  beforeEach(() => {
    cmpApi = new CmpApi(1, CMP_VERSION);
  });

  describe("getConsentFromGppApi", () => {
    const mockExperience: PrivacyExperience = {
      id: "test-experience",
      created_at: "2024-01-01",
      updated_at: "2024-01-01",
      privacy_notices: [
        {
          notice_key: "sale_opt_out",
          id: "1",
          created_at: "2024-01-01",
          updated_at: "2024-01-01",
          cookies: [],
          translations: [],
          gpp_field_mapping: [
            {
              region: "us",
              mechanism: [
                {
                  field: "SaleOptOut",
                  opt_out: "2",
                  not_opt_out: "1",
                  not_available: "0",
                },
              ],
            },
          ],
        },
        {
          notice_key: "sharing_opt_out",
          id: "2",
          created_at: "2024-01-01",
          updated_at: "2024-01-01",
          cookies: [],
          translations: [],
          gpp_field_mapping: [
            {
              region: "us",
              mechanism: [
                {
                  field: "SharingOptOut",
                  opt_out: "2",
                  not_opt_out: "1",
                  not_available: "0",
                },
              ],
            },
          ],
        },
      ],
      region: "us-national",
      gpp_settings: {
        us_approach: GPPUSApproach.ALL,
      },
    };

    it("should correctly parse US National GPP string", () => {
      const gppString = "DBABLA~BVAoAAAAAABk.QA";
      cmpApi.setGppString(gppString);

      const consent = getConsentFromGppCmpApi({
        cmpApi,
        experience: mockExperience,
      });

      expect(consent).toEqual({
        sale_opt_out: false,
        sharing_opt_out: false,
      });
    });

    it("should correctly parse California GPP string", () => {
      const gppString = "DBABBg~BUoAAABg.Q";
      const caExperience = {
        ...mockExperience,
        region: "us-ca",
        privacy_notices: [
          {
            notice_key: "sale_opt_out",
            id: "1",
            created_at: "2024-01-01",
            updated_at: "2024-01-01",
            cookies: [],
            translations: [],
            gpp_field_mapping: [
              {
                region: "us-ca",
                mechanism: [
                  {
                    field: "SaleOptOut",
                    opt_out: "2",
                    not_opt_out: "1",
                    not_available: "0",
                  },
                ],
              },
            ],
          },
        ],
      };

      cmpApi.setGppString(gppString);

      const consent = getConsentFromGppCmpApi({
        cmpApi,
        experience: caExperience,
      });

      expect(consent).toEqual({
        sale_opt_out: false,
      });
    });

    it("should handle multiple sections in GPP string", () => {
      const gppString = "DBABrw~BVAUAAAAAABk.QA~BAAAAABA.QA";
      cmpApi.setGppString(gppString);

      // Override mocks for this specific test
      cmpApi.getFieldValue = jest.fn((section, field) => {
        if (section === "usnatv1") {
          if (field === "SaleOptOut" || field === "SharingOptOut") {
            return "2";
          }
        }
        return null;
      });

      cmpApi.hasSection = jest.fn((section) => {
        return section === "usnatv1";
      });

      cmpApi.getSection = jest.fn((section) => {
        if (section === "usnatv1") {
          return {
            Version: 1,
            SharingNotice: 0,
            SaleOptOutNotice: 0,
            SharingOptOutNotice: 0,
            TargetedAdvertisingOptOutNotice: 0,
            SensitiveDataProcessingOptOutNotice: 0,
            SensitiveDataLimitUseNotice: 0,
            SaleOptOut: 2,
            SharingOptOut: 2,
            TargetedAdvertisingOptOut: 0,
            SensitiveDataProcessing: [
              0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
            ],
            KnownChildSensitiveDataConsents: [0, 0, 0],
            PersonalDataConsents: 0,
            MspaCoveredTransaction: 1,
            MspaOptOutOptionMode: 1,
            MspaServiceProviderMode: 2,
            GpcSegmentType: 1,
            Gpc: false,
          };
        }
        return null;
      });

      const consent = getConsentFromGppCmpApi({
        cmpApi,
        experience: mockExperience,
      });

      expect(consent).toEqual({
        sale_opt_out: true,
        sharing_opt_out: true,
      });
    });
  });

  describe("getTcfPreferencesFromCmpApi", () => {
    const mockTcfExperience = {
      tcf_special_purposes: [{ id: 1 }, { id: 2 }],
      tcf_features: [{ id: 1 }, { id: 2 }],
    } as PrivacyExperience;

    it("should correctly parse TCF preferences from GPP string", () => {
      const gppString =
        "DBABMA~CQNb38AQNb38AGXABBENBeFgALAAAENAAAAAFyQAQFyAXJABAXIAAAAA";
      cmpApi.setGppString(gppString);

      const preferences = getTcfPreferencesFromCmpApi({
        cmpApi,
        experience: mockTcfExperience,
      });

      expect(preferences).toMatchObject({
        vendorsConsent: expect.any(Array),
        vendorsLegint: expect.any(Array),
        purposesConsent: expect.any(Array),
        purposesLegint: expect.any(Array),
        specialFeatures: expect.any(Array),
        specialPurposes: ["1", "2"],
        features: ["1", "2"],
        customPurposesConsent: [],
      });
    });

    it("should handle missing TCF section", () => {
      const gppString = "DBABBg~BUoAAABg.Q"; // US-only string
      cmpApi.setGppString(gppString);

      // Override getSection to return null for TCF
      cmpApi.getSection = jest.fn(() => null);

      const preferences = getTcfPreferencesFromCmpApi({
        cmpApi,
        experience: mockTcfExperience,
      });

      expect(preferences).toEqual({
        vendorsConsent: [],
        vendorsLegint: [],
        purposesConsent: [],
        purposesLegint: [],
        specialFeatures: [],
        specialPurposes: ["1", "2"],
        features: ["1", "2"],
        customPurposesConsent: [],
      });
    });
  });
});
