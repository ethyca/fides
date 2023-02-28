import { produce } from "immer";

import { configIsValid } from "~/scripts/validate-config";
import minimalJson from "~/config/examples/minimal.json";
import fullJson from "~/config/examples/full.json";

describe("configIsValid", () => {
  const testCases = [
    {
      name: "no consent options",
      config: minimalJson,
      expected: {
        isValid: true,
      },
    },
    {
      name: "valid consent options",
      config: fullJson,
      expected: {
        isValid: true,
      },
    },
    {
      name: "multiple executable consent options",
      config: produce(fullJson, (draftConfig) => {
        draftConfig.consent.consentOptions[0].executable = true;
        draftConfig.consent.consentOptions[1].executable = true;
      }),
      expected: {
        isValid: false,
        message: "Cannot have more than one consent option be executable",
      },
    },
  ];

  testCases.forEach((tc) => {
    test(tc.name, () => {
      expect(configIsValid(tc.config)).toMatchObject(tc.expected);
    });
  });
});
