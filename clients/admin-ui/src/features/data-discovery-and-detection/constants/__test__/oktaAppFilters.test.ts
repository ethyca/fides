import { MOCK_OKTA_APPS } from "~/mocks/data";
import { OKTA_APP_FILTER_TABS } from "../oktaAppFilters";

// Test to verify filter counts match expected values
describe("Okta App Filters", () => {
  it("should have correct filter counts", () => {
    // All Apps: Should show all items
    const allAppsCount = MOCK_OKTA_APPS.length;
    expect(allAppsCount).toBe(1);

    // New Apps: Should show items with diff_status === "addition"
    const newAppsCount = MOCK_OKTA_APPS.filter(app => app.diff_status === "addition").length;
    expect(newAppsCount).toBe(1); // Salesforce

    // Active: Should show items with status === "ACTIVE"
    const activeCount = MOCK_OKTA_APPS.filter(app => app.metadata?.status === "ACTIVE").length;
    expect(activeCount).toBe(1); // Salesforce

    // Inactive: Should show items with status === "INACTIVE"
    const inactiveCount = MOCK_OKTA_APPS.filter(app => app.metadata?.status === "INACTIVE").length;
    expect(inactiveCount).toBe(0);

    // Known Vendors: Should show items with vendor_id
    const knownVendorsCount = MOCK_OKTA_APPS.filter(app => !!app.vendor_id).length;
    expect(knownVendorsCount).toBe(1); // Salesforce

    // Unknown Vendors: Should show items without vendor_id
    const unknownVendorsCount = MOCK_OKTA_APPS.filter(app => !app.vendor_id).length;
    expect(unknownVendorsCount).toBe(0);

    // Removed: Should show items with diff_status === "removal"
    const removedCount = MOCK_OKTA_APPS.filter(app => app.diff_status === "removal").length;
    expect(removedCount).toBe(0);
  });

  it("should filter correctly for each scenario", () => {
    // Test New Apps filter
    const newApps = MOCK_OKTA_APPS.filter(app => app.diff_status === "addition");
    expect(newApps).toHaveLength(1);
    expect(newApps.map(app => app.name)).toEqual(["Salesforce"]);

    // Test Active filter
    const activeApps = MOCK_OKTA_APPS.filter(app => app.metadata?.status === "ACTIVE");
    expect(activeApps).toHaveLength(1);
    expect(activeApps.map(app => app.name)).toEqual(["Salesforce"]);

    // Test Inactive filter
    const inactiveApps = MOCK_OKTA_APPS.filter(app => app.metadata?.status === "INACTIVE");
    expect(inactiveApps).toHaveLength(0);
    expect(inactiveApps.map(app => app.name)).toEqual([]);

    // Test Known Vendors filter
    const knownVendors = MOCK_OKTA_APPS.filter(app => !!app.vendor_id);
    expect(knownVendors).toHaveLength(1);
    expect(knownVendors.map(app => app.name)).toEqual(["Salesforce"]);

    // Test Unknown Vendors filter
    const unknownVendors = MOCK_OKTA_APPS.filter(app => !app.vendor_id);
    expect(unknownVendors).toHaveLength(0);
    expect(unknownVendors.map(app => app.name)).toEqual([]);

    // Test Removed filter
    const removedApps = MOCK_OKTA_APPS.filter(app => app.diff_status === "removal");
    expect(removedApps).toHaveLength(0);
  });

  it("should display correct tab counts", () => {
    // Test that tab counts match expected values
    const expectedCounts = {
      all: 1,
      new: 1,
      active: 1,
      inactive: 0,
      known: 1,
      unknown: 0,
      removed: 0,
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
