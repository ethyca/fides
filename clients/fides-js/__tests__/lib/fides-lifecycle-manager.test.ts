import { fidesLifecycleManager } from "../../src/lib/fides-lifecycle-manager";

describe("FidesLifecycleManager", () => {
  beforeEach(() => {
    // Reset the lifecycle manager before each test to ensure clean state
    fidesLifecycleManager.reset();
  });

  describe("getServedNoticeHistoryId", () => {
    it("should generate a UUID on first call", () => {
      const id = fidesLifecycleManager.getServedNoticeHistoryId();

      expect(id).toBeDefined();
      expect(typeof id).toBe("string");
      expect(id).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
      );
    });

    it("should return the same UUID on subsequent calls", () => {
      const firstId = fidesLifecycleManager.getServedNoticeHistoryId();
      const secondId = fidesLifecycleManager.getServedNoticeHistoryId();
      const thirdId = fidesLifecycleManager.getServedNoticeHistoryId();

      expect(firstId).toBe(secondId);
      expect(secondId).toBe(thirdId);
    });

    it("should return different UUIDs for different lifecycles", () => {
      const firstLifecycleId = fidesLifecycleManager.getServedNoticeHistoryId();

      // Reset to simulate a new lifecycle
      fidesLifecycleManager.reset();

      const secondLifecycleId =
        fidesLifecycleManager.getServedNoticeHistoryId();

      expect(firstLifecycleId).not.toBe(secondLifecycleId);
      expect(firstLifecycleId).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
      );
      expect(secondLifecycleId).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
      );
    });

    it("should maintain consistency across multiple rapid calls", () => {
      const ids = [];

      // Make 10 rapid calls
      for (let i = 0; i < 10; i += 1) {
        ids.push(fidesLifecycleManager.getServedNoticeHistoryId());
      }

      // All IDs should be identical
      const uniqueIds = [...new Set(ids)];
      expect(uniqueIds).toHaveLength(1);
      expect(ids).toHaveLength(10);
    });
  });

  describe("hasLifecycleId", () => {
    it("should return false when no lifecycle ID has been generated", () => {
      expect(fidesLifecycleManager.hasLifecycleId()).toBe(false);
    });

    it("should return true after a lifecycle ID has been generated", () => {
      fidesLifecycleManager.getServedNoticeHistoryId();
      expect(fidesLifecycleManager.hasLifecycleId()).toBe(true);
    });

    it("should return false after reset", () => {
      fidesLifecycleManager.getServedNoticeHistoryId();
      expect(fidesLifecycleManager.hasLifecycleId()).toBe(true);

      fidesLifecycleManager.reset();
      expect(fidesLifecycleManager.hasLifecycleId()).toBe(false);
    });
  });

  describe("reset", () => {
    it("should clear the lifecycle ID", () => {
      const originalId = fidesLifecycleManager.getServedNoticeHistoryId();
      expect(fidesLifecycleManager.hasLifecycleId()).toBe(true);

      fidesLifecycleManager.reset();
      expect(fidesLifecycleManager.hasLifecycleId()).toBe(false);

      // Should generate a new ID after reset
      const newId = fidesLifecycleManager.getServedNoticeHistoryId();
      expect(newId).not.toBe(originalId);
    });

    it("should be safe to call multiple times", () => {
      fidesLifecycleManager.getServedNoticeHistoryId();

      fidesLifecycleManager.reset();
      fidesLifecycleManager.reset();
      fidesLifecycleManager.reset();

      expect(fidesLifecycleManager.hasLifecycleId()).toBe(false);

      // Should still work after multiple resets
      const id = fidesLifecycleManager.getServedNoticeHistoryId();
      expect(id).toBeDefined();
      expect(fidesLifecycleManager.hasLifecycleId()).toBe(true);
    });

    it("should be safe to call when no lifecycle ID exists", () => {
      expect(fidesLifecycleManager.hasLifecycleId()).toBe(false);

      fidesLifecycleManager.reset();
      expect(fidesLifecycleManager.hasLifecycleId()).toBe(false);

      // Should still work after reset with no existing ID
      const id = fidesLifecycleManager.getServedNoticeHistoryId();
      expect(id).toBeDefined();
    });
  });

  describe("singleton behavior", () => {
    it("should maintain state across different imports", async () => {
      // This simulates how the lifecycle manager would be used across different modules
      const firstId = fidesLifecycleManager.getServedNoticeHistoryId();

      // Re-import would happen in a real scenario, but we can test the singleton behavior
      const { fidesLifecycleManager: reimportedLifecycleManager } =
        await import("../../src/lib/fides-lifecycle-manager");
      const secondId = reimportedLifecycleManager.getServedNoticeHistoryId();

      expect(firstId).toBe(secondId);
    });
  });

  describe("FidesJS lifecycle simulation", () => {
    it("should simulate a typical FidesJS lifecycle flow", () => {
      // Initial state - no lifecycle ID
      expect(fidesLifecycleManager.hasLifecycleId()).toBe(false);

      // First interaction (e.g., UI shown) - generates lifecycle ID
      const lifecycleId = fidesLifecycleManager.getServedNoticeHistoryId();
      expect(fidesLifecycleManager.hasLifecycleId()).toBe(true);

      // Multiple consent interactions use the same lifecycle ID
      const noticesServedId = fidesLifecycleManager.getServedNoticeHistoryId();
      const preferencesId = fidesLifecycleManager.getServedNoticeHistoryId();
      const automatedConsentId =
        fidesLifecycleManager.getServedNoticeHistoryId();

      expect(noticesServedId).toBe(lifecycleId);
      expect(preferencesId).toBe(lifecycleId);
      expect(automatedConsentId).toBe(lifecycleId);

      // Lifecycle ends (page reload, etc.) - new lifecycle starts
      fidesLifecycleManager.reset();
      expect(fidesLifecycleManager.hasLifecycleId()).toBe(false);

      // New lifecycle gets different ID
      const newLifecycleId = fidesLifecycleManager.getServedNoticeHistoryId();
      expect(newLifecycleId).not.toBe(lifecycleId);
    });
  });
});
