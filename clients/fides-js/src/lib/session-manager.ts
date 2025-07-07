import { v4 as uuidv4 } from "uuid";

class SessionManager {
  private servedNoticeHistoryId: string | null = null;

  /**
   * Get the session-level served_notice_history_id.
   * Creates a new UUID on first access and reuses it for the entire session.
   */
  getServedNoticeHistoryId(): string {
    if (!this.servedNoticeHistoryId) {
      this.servedNoticeHistoryId = uuidv4();
    }
    return this.servedNoticeHistoryId;
  }

  /**
   * Reset the session (primarily for testing purposes)
   */
  reset(): void {
    this.servedNoticeHistoryId = null;
  }

  /**
   * Check if a session ID has been generated
   */
  hasSessionId(): boolean {
    return this.servedNoticeHistoryId !== null;
  }
}

// Export a singleton instance
/**
 * Session-level manager for served_notice_history_id to ensure consistency
 * across the entire FidesJS session for accurate analytics correlation
 * between notices-served and privacy-preferences endpoints.
 */
export const sessionManager = new SessionManager();
