import { v4 as uuidv4 } from "uuid";

class FidesLifecycleManager {
  private servedNoticeHistoryId: string | null = null;

  /**
   * Get the lifecycle-level served_notice_history_id.
   * Creates a new UUID on first access and reuses it for the entire FidesJS lifecycle.
   */
  getServedNoticeHistoryId(): string {
    if (!this.servedNoticeHistoryId) {
      this.servedNoticeHistoryId = uuidv4();
    }
    return this.servedNoticeHistoryId;
  }

  /**
   * Reset the lifecycle (primarily for testing purposes)
   */
  reset(): void {
    this.servedNoticeHistoryId = null;
  }

  /**
   * Check if a lifecycle ID has been generated
   */
  hasLifecycleId(): boolean {
    return this.servedNoticeHistoryId !== null;
  }
}

// Export a singleton instance
/**
 * FidesJS lifecycle manager for served_notice_history_id to ensure consistency
 * across the entire FidesJS script execution for accurate analytics correlation
 * between notices-served and privacy-preferences endpoints.
 */
export const fidesLifecycleManager = new FidesLifecycleManager();
