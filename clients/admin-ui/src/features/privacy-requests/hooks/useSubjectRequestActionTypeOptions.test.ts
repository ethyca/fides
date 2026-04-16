import { renderHook } from "@testing-library/react";

import { ActionType } from "~/types/api";

import { SubjectRequestActionTypeOptions } from "../constants";
import { useSubjectRequestActionTypeOptions } from "./useSubjectRequestActionTypeOptions";

jest.mock("~/app/hooks", () => ({
  useAppSelector: (selector: any) => selector(),
}));

const mockSelectConsentModuleEnabled = jest.fn();
jest.mock("~/features/config-settings/config-settings.slice", () => ({
  selectConsentModuleEnabled: () => mockSelectConsentModuleEnabled(),
}));

describe("useSubjectRequestActionTypeOptions", () => {
  it("includes Consent when consent module is enabled", () => {
    mockSelectConsentModuleEnabled.mockReturnValue(true);
    const { result } = renderHook(() => useSubjectRequestActionTypeOptions());

    expect(result.current).toEqual(SubjectRequestActionTypeOptions);
    expect(result.current.some((o) => o.value === ActionType.CONSENT)).toBe(
      true,
    );
  });

  it("excludes Consent when consent module is disabled", () => {
    mockSelectConsentModuleEnabled.mockReturnValue(false);
    const { result } = renderHook(() => useSubjectRequestActionTypeOptions());

    expect(result.current.some((o) => o.value === ActionType.CONSENT)).toBe(
      false,
    );
    expect(result.current.some((o) => o.value === ActionType.ACCESS)).toBe(
      true,
    );
    expect(result.current.some((o) => o.value === ActionType.ERASURE)).toBe(
      true,
    );
  });
});
