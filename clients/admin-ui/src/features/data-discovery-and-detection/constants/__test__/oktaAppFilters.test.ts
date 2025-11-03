import { MOCK_OKTA_APPS } from "~/mocks/data";
import { OKTA_APP_FILTER_TABS } from "../oktaAppFilters";

// Test to verify filter counts match expected values
describe("Okta App Filters", () => {
  it("should have correct filter counts", () => {
    // All Apps: Should show all 10 items
    const allAppsCount = MOCK_OKTA_APPS.length;
    expect(allAppsCount).toBe(10);

    // New Apps: Should show items with diff_status === "addition"
    const newAppsCount = MOCK_OKTA_APPS.filter(app => app.diff_status === "addition").length;
    expect(newAppsCount).toBe(8); // Salesforce, Google Workspace, Microsoft Office 365, Zoom, Custom Internal App, Deprecated Project Tool, Internal HR Portal, Legacy Finance Tool

    // Active: Should show items with status === "ACTIVE"
    const activeCount = MOCK_OKTA_APPS.filter(app => app.metadata?.status === "ACTIVE").length;
    expect(activeCount).toBe(7); // Salesforce, Google Workspace, Slack, Zoom, Custom Internal App, Deprecated Project Tool, Internal HR Portal

    // Inactive: Should show items with status === "INACTIVE"
    const inactiveCount = MOCK_OKTA_APPS.filter(app => app.metadata?.status === "INACTIVE").length;
    expect(inactiveCount).toBe(3); // Microsoft Office 365, Legacy System, Legacy Finance Tool

    // Known Vendors: Should show items with vendor_id
    const knownVendorsCount = MOCK_OKTA_APPS.filter(app => !!app.vendor_id).length;
    expect(knownVendorsCount).toBe(7); // Salesforce, Google Workspace, Slack, Microsoft Office 365, Zoom, Legacy System, Deprecated Project Tool

    // Unknown Vendors: Should show items without vendor_id
    const unknownVendorsCount = MOCK_OKTA_APPS.filter(app => !app.vendor_id).length;
    expect(unknownVendorsCount).toBe(3); // Custom Internal App, Internal HR Portal, Legacy Finance Tool

    // Removed: Should show items with diff_status === "removal"
    const removedCount = MOCK_OKTA_APPS.filter(app => app.diff_status === "removal").length;
    expect(removedCount).toBe(1); // Legacy System
  });

  it("should filter correctly for each scenario", () => {
    // Test New Apps filter
    const newApps = MOCK_OKTA_APPS.filter(app => app.diff_status === "addition");
    expect(newApps).toHaveLength(8);
    expect(newApps.map(app => app.name)).toEqual([
      "Salesforce",
      "Google Workspace", 
      "Microsoft Office 365",
      "Zoom",
      "Custom Internal App",
      "Deprecated Project Tool",
      "Internal HR Portal",
      "Legacy Finance Tool"
    ]);

    // Test Active filter
    const activeApps = MOCK_OKTA_APPS.filter(app => app.metadata?.status === "ACTIVE");
    expect(activeApps).toHaveLength(7);
    expect(activeApps.map(app => app.name)).toEqual([
      "Salesforce",
      "Google Workspace",
      "Slack", 
      "Zoom",
      "Custom Internal App",
      "Deprecated Project Tool",
      "Internal HR Portal"
    ]);

    // Test Inactive filter
    const inactiveApps = MOCK_OKTA_APPS.filter(app => app.metadata?.status === "INACTIVE");
    expect(inactiveApps).toHaveLength(3);
    expect(inactiveApps.map(app => app.name)).toEqual([
      "Microsoft Office 365",
      "Legacy System",
      "Legacy Finance Tool"
    ]);

    // Test Known Vendors filter
    const knownVendors = MOCK_OKTA_APPS.filter(app => !!app.vendor_id);
    expect(knownVendors).toHaveLength(7);
    expect(knownVendors.map(app => app.name)).toEqual([
      "Salesforce",
      "Google Workspace",
      "Slack",
      "Microsoft Office 365", 
      "Zoom",
      "Legacy System",
      "Deprecated Project Tool"
    ]);

    // Test Unknown Vendors filter
    const unknownVendors = MOCK_OKTA_APPS.filter(app => !app.vendor_id);
    expect(unknownVendors).toHaveLength(3);
    expect(unknownVendors.map(app => app.name)).toEqual([
      "Custom Internal App",
      "Internal HR Portal", 
      "Legacy Finance Tool"
    ]);

    // Test Removed filter
    const removedApps = MOCK_OKTA_APPS.filter(app => app.diff_status === "removal");
    expect(removedApps).toHaveLength(1);
    expect(removedApps[0].name).toBe("Legacy System");
  });

  it("should display correct tab counts", () => {
    // Test that tab counts match expected values
    const expectedCounts = {
      all: 10,
      new: 8,
      active: 7,
      inactive: 3,
      known: 7,
      unknown: 3,
      removed: 1,
    };

    // Verify each filter returns the expected count
    Object.entries(expectedCounts).forEach(([filterValue, expectedCount]) => {
      const filter = OKTA_APP_FILTER_TABS.find(tab => tab.value === filterValue);
      expect(filter).toBeDefined();
      
      const actualCount = MOCK_OKTA_APPS.filter((item) => {
        const resource = item as any;
        return filter?.filter(resource) ?? true;
      }).length;
      
      expect(actualCount).toBe(expectedCount);
    });
  });
});
