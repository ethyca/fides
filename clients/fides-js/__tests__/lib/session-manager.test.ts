import { sessionManager } from "../../src/lib/session-manager";

describe("SessionManager", () => {
  beforeEach(() => {
    // Reset the session manager before each test to ensure clean state
    sessionManager.reset();
  });

  describe("getServedNoticeHistoryId", () => {
    it("should generate a UUID on first call", () => {
      const id = sessionManager.getServedNoticeHistoryId();

      expect(id).toBeDefined();
      expect(typeof id).toBe("string");
      expect(id).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
      );
    });

    it("should return the same UUID on subsequent calls", () => {
      const firstId = sessionManager.getServedNoticeHistoryId();
      const secondId = sessionManager.getServedNoticeHistoryId();
      const thirdId = sessionManager.getServedNoticeHistoryId();

      expect(firstId).toBe(secondId);
      expect(secondId).toBe(thirdId);
    });

    it("should return different UUIDs for different sessions", () => {
      const firstSessionId = sessionManager.getServedNoticeHistoryId();

      // Reset to simulate a new session
      sessionManager.reset();

      const secondSessionId = sessionManager.getServedNoticeHistoryId();

      expect(firstSessionId).not.toBe(secondSessionId);
      expect(firstSessionId).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
      );
      expect(secondSessionId).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
      );
    });

    it("should maintain consistency across multiple rapid calls", () => {
      const ids = [];

      // Make 10 rapid calls
      for (let i = 0; i < 10; i += 1) {
        ids.push(sessionManager.getServedNoticeHistoryId());
      }

      // All IDs should be identical
      const uniqueIds = [...new Set(ids)];
      expect(uniqueIds).toHaveLength(1);
      expect(ids).toHaveLength(10);
    });
  });

  describe("hasSessionId", () => {
    it("should return false when no session ID has been generated", () => {
      expect(sessionManager.hasSessionId()).toBe(false);
    });

    it("should return true after a session ID has been generated", () => {
      sessionManager.getServedNoticeHistoryId();
      expect(sessionManager.hasSessionId()).toBe(true);
    });

    it("should return false after reset", () => {
      sessionManager.getServedNoticeHistoryId();
      expect(sessionManager.hasSessionId()).toBe(true);

      sessionManager.reset();
      expect(sessionManager.hasSessionId()).toBe(false);
    });
  });

  describe("reset", () => {
    it("should clear the session ID", () => {
      const originalId = sessionManager.getServedNoticeHistoryId();
      expect(sessionManager.hasSessionId()).toBe(true);

      sessionManager.reset();
      expect(sessionManager.hasSessionId()).toBe(false);

      // Should generate a new ID after reset
      const newId = sessionManager.getServedNoticeHistoryId();
      expect(newId).not.toBe(originalId);
    });

    it("should be safe to call multiple times", () => {
      sessionManager.getServedNoticeHistoryId();

      sessionManager.reset();
      sessionManager.reset();
      sessionManager.reset();

      expect(sessionManager.hasSessionId()).toBe(false);

      // Should still work after multiple resets
      const id = sessionManager.getServedNoticeHistoryId();
      expect(id).toBeDefined();
      expect(sessionManager.hasSessionId()).toBe(true);
    });

    it("should be safe to call when no session ID exists", () => {
      expect(sessionManager.hasSessionId()).toBe(false);

      sessionManager.reset();
      expect(sessionManager.hasSessionId()).toBe(false);

      // Should still work after reset with no existing ID
      const id = sessionManager.getServedNoticeHistoryId();
      expect(id).toBeDefined();
    });
  });

  describe("singleton behavior", () => {
    it("should maintain state across different imports", async () => {
      // This simulates how the session manager would be used across different modules
      const firstId = sessionManager.getServedNoticeHistoryId();

      // Re-import would happen in a real scenario, but we can test the singleton behavior
      const { sessionManager: reimportedSessionManager } = await import(
        "../../src/lib/session-manager"
      );
      const secondId = reimportedSessionManager.getServedNoticeHistoryId();

      expect(firstId).toBe(secondId);
    });
  });

  describe("session lifecycle simulation", () => {
    it("should simulate a typical FidesJS session flow", () => {
      // Initial state - no session ID
      expect(sessionManager.hasSessionId()).toBe(false);

      // First interaction (e.g., UI shown) - generates session ID
      const sessionId = sessionManager.getServedNoticeHistoryId();
      expect(sessionManager.hasSessionId()).toBe(true);

      // Multiple consent interactions use the same session ID
      const noticesServedId = sessionManager.getServedNoticeHistoryId();
      const preferencesId = sessionManager.getServedNoticeHistoryId();
      const automatedConsentId = sessionManager.getServedNoticeHistoryId();

      expect(noticesServedId).toBe(sessionId);
      expect(preferencesId).toBe(sessionId);
      expect(automatedConsentId).toBe(sessionId);

      // Session ends (page reload, etc.) - new session starts
      sessionManager.reset();
      expect(sessionManager.hasSessionId()).toBe(false);

      // New session gets different ID
      const newSessionId = sessionManager.getServedNoticeHistoryId();
      expect(newSessionId).not.toBe(sessionId);
    });
  });
});
