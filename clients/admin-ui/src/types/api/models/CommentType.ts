/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Enum for comment types. Indicates comment usage.
 *
 * - notes are internal comments.
 * - reply comments are public and may cause an email or other communciation to be sent
 */
export enum CommentType {
  NOTE = "note",
  REPLY = "reply",
}
