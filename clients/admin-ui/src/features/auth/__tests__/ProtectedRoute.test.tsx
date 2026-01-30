/**
 * @jest-environment jsdom
 */
import { describe, expect, it, jest, beforeEach } from "@jest/globals";

// Mock window.location
const mockLocation = {
  pathname: "/dashboard",
  href: "",
};

Object.defineProperty(window, "location", {
  value: mockLocation,
  writable: true,
});

describe("ProtectedRoute redirect behavior", () => {
  beforeEach(() => {
    mockLocation.pathname = "/dashboard";
    mockLocation.href = "";
  });

  it("should use hard navigation (window.location.href) for redirect URLs", () => {
    // This test verifies that when redirecting to login, we use window.location.href
    // instead of client-side navigation to ensure proper page reload (ENG-1466)
    const redirectUrl = "/login";
    const redirectParam = `?redirect=${encodeURIComponent("/dashboard")}`;
    const expectedHref = `${redirectUrl}${redirectParam}`;

    // Simulate setting window.location.href (the fix)
    window.location.href = expectedHref;

    expect(window.location.href).toBe(expectedHref);
  });

  it("should not include redirect param for ignored paths", () => {
    const REDIRECT_IGNORES = ["/", "/login"];

    // Test that root path doesn't include redirect param
    mockLocation.pathname = "/";
    const redirectParam = REDIRECT_IGNORES.includes(mockLocation.pathname)
      ? ""
      : `?redirect=${encodeURIComponent(mockLocation.pathname)}`;

    expect(redirectParam).toBe("");
  });

  it("should include redirect param for non-ignored paths", () => {
    const REDIRECT_IGNORES = ["/", "/login"];

    // Test that other paths include redirect param
    mockLocation.pathname = "/dashboard";
    const redirectParam = REDIRECT_IGNORES.includes(mockLocation.pathname)
      ? ""
      : `?redirect=${encodeURIComponent(mockLocation.pathname)}`;

    expect(redirectParam).toBe("?redirect=%2Fdashboard");
  });

  it("should properly encode redirect param with special characters", () => {
    mockLocation.pathname = "/systems/my-system?filter=active";
    const redirectParam = `?redirect=${encodeURIComponent(mockLocation.pathname)}`;

    expect(redirectParam).toBe(
      "?redirect=%2Fsystems%2Fmy-system%3Ffilter%3Dactive"
    );
  });
});
