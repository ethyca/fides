import { processGpcConditionals } from "../../src/lib/gpc-utils";

describe("processGpcConditionals", () => {
  it("returns text unchanged when no markers present", () => {
    const text = "This is regular text";
    expect(processGpcConditionals(text, true)).toBe(text);
    expect(processGpcConditionals(text, false)).toBe(text);
  });

  it("shows GPC content when GPC is enabled", () => {
    const text = "We value privacy. __GPC_START__Thank you for GPC!__GPC_END__";
    expect(processGpcConditionals(text, true)).toBe(
      "We value privacy. Thank you for GPC!",
    );
  });

  it("hides GPC content when GPC is disabled", () => {
    const text = "We value privacy. __GPC_START__Thank you for GPC!__GPC_END__";
    expect(processGpcConditionals(text, false)).toBe("We value privacy.");
  });

  it("shows NO_GPC content when GPC is disabled", () => {
    const text =
      "We value privacy. __NO_GPC_START__Manage preferences.__NO_GPC_END__";
    expect(processGpcConditionals(text, false)).toBe(
      "We value privacy. Manage preferences.",
    );
  });

  it("hides NO_GPC content when GPC is enabled", () => {
    const text =
      "We value privacy. __NO_GPC_START__Manage preferences.__NO_GPC_END__";
    expect(processGpcConditionals(text, true)).toBe("We value privacy.");
  });

  it("handles both GPC and NO_GPC blocks together", () => {
    const text =
      "Privacy matters. __GPC_START__GPC detected!__GPC_END____NO_GPC_START__No GPC.__NO_GPC_END__";
    expect(processGpcConditionals(text, true)).toBe(
      "Privacy matters. GPC detected!",
    );
    expect(processGpcConditionals(text, false)).toBe(
      "Privacy matters. No GPC.",
    );
  });

  it("handles empty strings", () => {
    expect(processGpcConditionals("", true)).toBe("");
    expect(processGpcConditionals(undefined, true)).toBe("");
  });

  it("cleans up extra whitespace", () => {
    const text = "Text   __GPC_START__with   spaces__GPC_END__   here";
    expect(processGpcConditionals(text, false)).toBe("Text here");
  });

  it("handles multiline text", () => {
    const text = `We value privacy.
__GPC_START__
Thank you for enabling GPC!
Your preferences are respected.
__GPC_END__
__NO_GPC_START__
You can manage preferences below.
__NO_GPC_END__`;

    const resultWithGpc = processGpcConditionals(text, true);
    expect(resultWithGpc).toContain("Thank you for enabling GPC!");
    expect(resultWithGpc).not.toContain("You can manage preferences below");

    const resultWithoutGpc = processGpcConditionals(text, false);
    expect(resultWithoutGpc).toContain("You can manage preferences below");
    expect(resultWithoutGpc).not.toContain("Thank you for enabling GPC!");
  });

  it("handles multiple GPC blocks in the same text", () => {
    const text =
      "__GPC_START__First GPC block.__GPC_END__ Some text. __GPC_START__Second GPC block.__GPC_END__";
    expect(processGpcConditionals(text, true)).toBe(
      "First GPC block. Some text. Second GPC block.",
    );
    expect(processGpcConditionals(text, false)).toBe("Some text.");
  });

  it("handles nested or adjacent blocks gracefully", () => {
    const text =
      "Start __GPC_START__GPC text__GPC_END____NO_GPC_START__No GPC text__NO_GPC_END__ End";
    expect(processGpcConditionals(text, true)).toBe("Start GPC text End");
    expect(processGpcConditionals(text, false)).toBe("Start No GPC text End");
  });

  it("preserves HTML content within conditional blocks", () => {
    const text =
      '__GPC_START__Thank you! <a href="#">Learn more</a>__GPC_END____NO_GPC_START__<strong>Manage</strong> preferences__NO_GPC_END__';
    expect(processGpcConditionals(text, true)).toBe(
      'Thank you! <a href="#">Learn more</a>',
    );
    expect(processGpcConditionals(text, false)).toBe(
      "<strong>Manage</strong> preferences",
    );
  });
});
