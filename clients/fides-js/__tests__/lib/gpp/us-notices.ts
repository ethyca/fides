/* eslint-disable no-underscore-dangle */

import { CmpApi } from "@iabgpp/cmpapi";
import {
  setGppNoticesProvidedFromExperience,
  setGppOptOutsFromCookie,
} from "../../../src/lib/gpp/us-notices";
import {
  PrivacyExperience,
  PrivacyNotice,
} from "../../../src/lib/consent-types";
import { makeStub } from "../../../src/lib/gpp/stub";
import { FidesCookie } from "../../../src/lib/cookie";

const EMPTY_GPP_STRING = "DBAA";

const mockPrivacyExperience = (override?: Partial<PrivacyExperience>) => {
  const base: PrivacyExperience = {
    id: "id",
    region: "us",
    privacy_notices: [],
    created_at: "2023-12-06T22:03:26.052630+00:00",
    updated_at: "2023-12-07T22:03:26.052630+00:00",
  };

  if (!override) {
    return base;
  }
  return { ...base, ...override };
};

const mockFidesCookie = (override?: Partial<FidesCookie>) => {
  const uuid = "4fbb6edf-34f6-4717-a6f1-541fd1e5d585";
  const CREATED_DATE = "2022-12-24T12:00:00.000Z";
  const UPDATED_DATE = "2022-12-25T12:00:00.000Z";
  const cookie: FidesCookie = {
    identity: { fides_user_device_id: uuid },
    fides_meta: {
      version: "0.9.0",
      createdAt: CREATED_DATE,
      updatedAt: UPDATED_DATE,
    },
    consent: {},
    tcf_consent: {},
  };

  if (!override) {
    return cookie;
  }

  return { ...cookie, ...override };
};

describe("setGppNoticesProvidedFromExperience", () => {
  beforeEach(() => {
    // Make stub so that the library initializes without errors
    makeStub();
  });

  it("does nothing for region outside of US", () => {
    const cmpApi = new CmpApi(1, 1);
    const experience = mockPrivacyExperience({ region: "fr" });
    setGppNoticesProvidedFromExperience({ cmpApi, experience });
    expect(cmpApi.getGppString()).toEqual(EMPTY_GPP_STRING);
    expect(cmpApi.getSection("usnatv1")).toBe(null);
  });

  it("sets all as not provided when there are no notices", () => {
    const cmpApi = new CmpApi(1, 1);
    const experience = mockPrivacyExperience();
    setGppNoticesProvidedFromExperience({ cmpApi, experience });
    const section = cmpApi.getSection("usnatv1");
    // 2 means notice was not provided. All other consent fields should be 0 (N/A)
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 2,
      SaleOptOutNotice: 2,
      SharingOptOutNotice: 2,
      TargetedAdvertisingOptOutNotice: 2,
      SensitiveDataProcessingOptOutNotice: 2,
      SensitiveDataLimitUseNotice: 2,
      SaleOptOut: 0,
      SharingOptOut: 0,
      TargetedAdvertisingOptOut: 0,
      SensitiveDataProcessing: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      KnownChildSensitiveDataConsents: [0, 0],
      PersonalDataConsents: 0,
      MspaCoveredTransaction: 0,
      MspaOptOutOptionMode: 0,
      MspaServiceProviderMode: 0,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BqqAAAAAAAA.QA");
  });

  it("can set all to provided", () => {
    const cmpApi = new CmpApi(1, 1);
    const notices = [
      { notice_key: "data_sales_and_sharing" },
      { notice_key: "targeted_advertising" },
      { notice_key: "sensitive_personal_data_sharing" },
    ] as PrivacyNotice[];
    const experience = mockPrivacyExperience({ privacy_notices: notices });
    setGppNoticesProvidedFromExperience({ cmpApi, experience });
    const section = cmpApi.getSection("usnatv1");
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 1,
      SaleOptOutNotice: 1,
      SharingOptOutNotice: 1,
      TargetedAdvertisingOptOutNotice: 1,
      SensitiveDataProcessingOptOutNotice: 1,
      SensitiveDataLimitUseNotice: 1,
      SaleOptOut: 0,
      SharingOptOut: 0,
      TargetedAdvertisingOptOut: 0,
      SensitiveDataProcessing: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      KnownChildSensitiveDataConsents: [0, 0],
      PersonalDataConsents: 0,
      MspaCoveredTransaction: 0,
      MspaOptOutOptionMode: 0,
      MspaServiceProviderMode: 0,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BVVAAAAAAAA.QA");
  });
});

describe("setGppOptOutsFromCookie", () => {
  beforeEach(() => {
    // Make stub so that the library initializes without errors
    makeStub();
  });

  it("does nothing for region outside of US", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie();
    setGppOptOutsFromCookie({ cmpApi, cookie, region: "fr" });
    expect(cmpApi.getGppString()).toEqual(EMPTY_GPP_STRING);
  });

  it("sets all as 0 when there is no consent object in cookie", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie({ consent: {} });
    setGppOptOutsFromCookie({ cmpApi, cookie, region: "us" });

    const section = cmpApi.getSection("usnatv1");
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 0,
      SaleOptOutNotice: 0,
      SharingOptOutNotice: 0,
      TargetedAdvertisingOptOutNotice: 0,
      SensitiveDataProcessingOptOutNotice: 0,
      SensitiveDataLimitUseNotice: 0,
      SaleOptOut: 0,
      SharingOptOut: 0,
      TargetedAdvertisingOptOut: 0,
      SensitiveDataProcessing: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      KnownChildSensitiveDataConsents: [0, 0],
      PersonalDataConsents: 0,
      MspaCoveredTransaction: 0,
      MspaOptOutOptionMode: 0,
      MspaServiceProviderMode: 0,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BAAAAAAAAAA.QA");
  });

  it("can set fields when there is a partial consent object in cookie", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie({
      consent: { data_sales_and_sharing: true },
    });
    setGppOptOutsFromCookie({ cmpApi, cookie, region: "us" });
    const section = cmpApi.getSection("usnatv1");
    expect(section).toEqual({
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
      SensitiveDataProcessing: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      KnownChildSensitiveDataConsents: [0, 0],
      PersonalDataConsents: 0,
      MspaCoveredTransaction: 0,
      MspaOptOutOptionMode: 0,
      MspaServiceProviderMode: 0,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BAAoAAAAAAA.QA");
  });

  it("can set all fields to not opted out for consent object in cookie", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie({
      consent: {
        data_sales_and_sharing: true,
        targeted_advertising: true,
        sensitive_personal_data_sharing: true,
      },
    });
    setGppOptOutsFromCookie({ cmpApi, cookie, region: "us" });
    const section = cmpApi.getSection("usnatv1");
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 0,
      SaleOptOutNotice: 0,
      SharingOptOutNotice: 0,
      TargetedAdvertisingOptOutNotice: 0,
      SensitiveDataProcessingOptOutNotice: 0,
      SensitiveDataLimitUseNotice: 0,
      SaleOptOut: 2,
      SharingOptOut: 2,
      TargetedAdvertisingOptOut: 2,
      SensitiveDataProcessing: [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
      KnownChildSensitiveDataConsents: [2, 2],
      PersonalDataConsents: 2,
      MspaCoveredTransaction: 0,
      MspaOptOutOptionMode: 0,
      MspaServiceProviderMode: 0,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BAAqqqqqqAA.QA");
  });

  it("can set all fields to opted out for consent object in cookie", () => {
    const cmpApi = new CmpApi(1, 1);
    const cookie = mockFidesCookie({
      consent: {
        data_sales_and_sharing: false,
        targeted_advertising: false,
        sensitive_personal_data_sharing: false,
      },
    });
    setGppOptOutsFromCookie({ cmpApi, cookie, region: "us" });
    const section = cmpApi.getSection("usnatv1");
    expect(section).toEqual({
      Version: 1,
      SharingNotice: 0,
      SaleOptOutNotice: 0,
      SharingOptOutNotice: 0,
      TargetedAdvertisingOptOutNotice: 0,
      SensitiveDataProcessingOptOutNotice: 0,
      SensitiveDataLimitUseNotice: 0,
      SaleOptOut: 1,
      SharingOptOut: 1,
      TargetedAdvertisingOptOut: 1,
      SensitiveDataProcessing: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
      KnownChildSensitiveDataConsents: [1, 1],
      PersonalDataConsents: 1,
      MspaCoveredTransaction: 0,
      MspaOptOutOptionMode: 0,
      MspaServiceProviderMode: 0,
      GpcSegmentType: 1,
      Gpc: false,
    });
    expect(cmpApi.getGppString()).toEqual("DBABLA~BAAVVVVVVAA.QA");
  });
});
