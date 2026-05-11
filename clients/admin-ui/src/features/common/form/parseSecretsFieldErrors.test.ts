import { parseSecretsFieldErrors } from "./parseSecretsFieldErrors";

describe("parseSecretsFieldErrors", () => {
  it("returns null when the error is not a structured 422 detail array", () => {
    expect(
      parseSecretsFieldErrors(
        { data: { detail: "boom" } },
        { knownFields: ["foo"] },
      ),
    ).toBeNull();
    expect(
      parseSecretsFieldErrors(undefined, { knownFields: ["foo"] }),
    ).toBeNull();
  });

  it("returns null when no known fields are provided", () => {
    expect(
      parseSecretsFieldErrors(
        {
          data: {
            detail: [
              { type: "value_error", loc: ["foo"], msg: "Value error, x" },
            ],
          },
        },
        { knownFields: [] },
      ),
    ).toBeNull();
  });

  it("maps loc-based errors and strips the 'Value error, ' prefix (BigQuery keyfile_creds case)", () => {
    const result = parseSecretsFieldErrors(
      {
        data: {
          detail: [
            {
              type: "value_error",
              loc: ["keyfile_creds"],
              msg: "Value error, Expecting value: line 1 column 1 (char 0)",
            },
          ],
        },
      },
      { knownFields: ["keyfile_creds", "dataset"] },
    );

    expect(result).toEqual([
      {
        name: ["secrets", "keyfile_creds"],
        errors: ["Expecting value: line 1 column 1 (char 0)"],
      },
    ]);
  });

  it("falls back to extracting the field name from the message and strips the env-var advisory (Zendesk domain case)", () => {
    const result = parseSecretsFieldErrors(
      {
        data: {
          detail: [
            {
              type: "value_error",
              loc: [],
              msg: "Value error, The value 'sfesdfesk.com' for 'domain' is not in the list of allowed values: [*.zendesk.com]. You may change the validation behavior by setting the environment variable FIDES__SECURITY__DOMAIN_VALIDATION_MODE to 'monitor' (log warnings only) or 'disabled' (skip validation).",
            },
          ],
        },
      },
      { knownFields: ["domain", "username", "api_key"] },
    );

    expect(result).toEqual([
      {
        name: ["secrets", "domain"],
        errors: [
          "The value 'sfesdfesk.com' for 'domain' is not in the list of allowed values: [*.zendesk.com].",
        ],
      },
    ]);
  });

  it("ignores detail entries whose field name is not part of the known fields", () => {
    const result = parseSecretsFieldErrors(
      {
        data: {
          detail: [
            {
              type: "value_error",
              loc: ["unknown_field"],
              msg: "Value error, nope",
            },
          ],
        },
      },
      { knownFields: ["domain"] },
    );
    expect(result).toBeNull();
  });

  it("groups multiple errors targeting the same field", () => {
    const result = parseSecretsFieldErrors(
      {
        data: {
          detail: [
            { type: "value_error", loc: ["domain"], msg: "Value error, A" },
            { type: "value_error", loc: ["domain"], msg: "Value error, B" },
          ],
        },
      },
      { knownFields: ["domain"] },
    );
    expect(result).toEqual([
      { name: ["secrets", "domain"], errors: ["A", "B"] },
    ]);
  });

  it("respects an empty namePrefix for forms whose fields are at the top level", () => {
    const result = parseSecretsFieldErrors(
      {
        data: {
          detail: [
            {
              type: "value_error",
              loc: ["project_key"],
              msg: "Value error, Project does not exist",
            },
          ],
        },
      },
      { knownFields: ["project_key", "issue_type"], namePrefix: [] },
    );

    expect(result).toEqual([
      { name: ["project_key"], errors: ["Project does not exist"] },
    ]);
  });
});
