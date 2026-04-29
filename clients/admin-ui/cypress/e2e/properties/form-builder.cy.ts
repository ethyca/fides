import { stubPlus, stubProperties } from "cypress/support/stubs";

// ─── Helpers ─────────────────────────────────────────────────────────────────

const PROPERTY_ID = "FDS-CEA9EV";
const POLICY_KEY = "default_access_policy";

// Minimal property fixture that satisfies FormBuilderPage's shape:
// it needs privacy_center_config.actions with at least one entry whose
// policy_key matches the route param.
const buildPropertyFixture = () => ({
  id: PROPERTY_ID,
  name: "Property A",
  type: "Website",
  paths: [],
  experiences: [],
  privacy_center_config: {
    actions: [
      {
        policy_key: POLICY_KEY,
        title: "Access Request",
        description: "Request a copy of your data",
        identity_inputs: { email: "required" },
        custom_privacy_request_fields: null,
        _form_builder_spec: null,
      },
    ],
  },
});

// Build a JsonRenderSpec — the shape the SSE "done" event carries.
const buildSpec = (extraElements: Record<string, unknown> = {}) => ({
  root: "form",
  elements: {
    form: {
      type: "Form",
      props: {},
      children: ["f_email", ...Object.keys(extraElements)],
    },
    f_email: {
      type: "Text",
      props: { name: "email", label: "Email", required: true },
      children: [],
    },
    ...extraElements,
  },
});

// Encode a spec into a well-formed SSE body that the streaming parser accepts.
// The body is delivered as one chunk; the parser accumulates until \n\n.
const buildSseBody = (spec: object): string =>
  [
    `event: chunk\ndata: ${JSON.stringify(spec)}\n\n`,
    `event: done\ndata: ${JSON.stringify({ raw: JSON.stringify(spec) })}\n\n`,
  ].join("");

// ─── Tests ───────────────────────────────────────────────────────────────────

describe("Privacy center form builder", () => {
  beforeEach(() => {
    cy.login();
    stubPlus(true);
    stubProperties();

    // Stub the single-property GET so the route can hydrate before rendering.
    cy.intercept("GET", `/api/v1/plus/property/${PROPERTY_ID}`, {
      statusCode: 200,
      body: buildPropertyFixture(),
    }).as("getProperty");
  });

  // ── Test 1: happy path ──────────────────────────────────────────────────────
  it("happy path: chat → preview → save", () => {
    const spec = buildSpec();

    cy.intercept(
      "POST",
      `/api/v1/plus/property/${PROPERTY_ID}/form-builder/chat`,
      {
        statusCode: 200,
        headers: { "content-type": "text/event-stream" },
        body: buildSseBody(spec),
      },
    ).as("chatTurn");

    cy.intercept("PUT", `/api/v1/plus/property/${PROPERTY_ID}`, {
      statusCode: 200,
      body: buildPropertyFixture(),
    }).as("savePut");

    cy.visit(`/properties/${PROPERTY_ID}/forms/${POLICY_KEY}`);
    cy.wait("@getProperty");

    // The ChatPane renders a textarea with this placeholder
    cy.findByPlaceholderText(/tell the builder/i).type("Add an email field");

    // Send the message — after streaming the spec should appear in the preview
    cy.findByRole("button", { name: /^send$/i }).click();
    cy.wait("@chatTurn");

    // The registry renders a Form.Item whose label is the field's label prop
    cy.findByText("Email").should("be.visible");

    // Save the form — should PUT to property endpoint and show success toast
    cy.findByRole("button", { name: /^save$/i }).click();
    cy.wait("@savePut");
    // Scope to the Ant Design message container to avoid false positives from
    // other text on the page that contains "saved".
    cy.get(".ant-message").findByText(/^saved$/i).should("be.visible");
  });

  // ── Test 2: dropped-features acknowledgement ────────────────────────────────
  it("warns and gates save when conditional logic is present", () => {
    const spec = buildSpec({
      f_state: {
        type: "Text",
        props: { name: "state", label: "State", required: false },
        children: [],
        // `visible` is a dropped feature — the mapper will flag it
        visible: [{ $state: "/form/country", eq: "US" }],
      },
    });

    cy.intercept(
      "POST",
      `/api/v1/plus/property/${PROPERTY_ID}/form-builder/chat`,
      {
        statusCode: 200,
        headers: { "content-type": "text/event-stream" },
        body: buildSseBody(spec),
      },
    ).as("chatTurn");

    cy.intercept("PUT", `/api/v1/plus/property/${PROPERTY_ID}`, {
      statusCode: 200,
      body: buildPropertyFixture(),
    }).as("savePut");

    cy.visit(`/properties/${PROPERTY_ID}/forms/${POLICY_KEY}`);
    cy.wait("@getProperty");

    cy.findByPlaceholderText(/tell the builder/i).type(
      "Add state field visible only when country is US",
    );
    cy.findByRole("button", { name: /^send$/i }).click();
    cy.wait("@chatTurn");

    // The email field always renders (no visibility condition).
    // NOTE: "State" has a `visible` conditional that evaluates to false in the
    // preview (no country value exists), so the @json-render renderer hides it.
    // We only assert the field the renderer definitely shows.
    cy.findByText("Email").should("be.visible");

    // Clicking Save should open the dropped-features modal instead of saving
    cy.findByRole("button", { name: /^save$/i }).click();

    // The modal title is "Some features won't be saved"
    cy.findByText(/won.?t be saved/i).should("be.visible");

    // Confirm save despite dropped features
    cy.findByRole("button", { name: /save anyway/i }).click();
    cy.wait("@savePut");
    cy.get(".ant-message").findByText(/^saved$/i).should("be.visible");
  });
});
