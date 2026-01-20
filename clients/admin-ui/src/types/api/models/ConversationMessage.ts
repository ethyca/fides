/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * A single message in a conversation.
 */
export type ConversationMessage = {
  /**
   * The role of the message sender: 'user' or 'assistant'
   */
  role: string;
  /**
   * The message content
   */
  content: string;
};
