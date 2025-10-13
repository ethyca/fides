/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Types of digest conditions - each can have their own tree.
 *
 * Types:
 * - RECEIVER: Conditions that determine who gets the digest
 * - CONTENT: Conditions that determine what gets included in the digest
 * - PRIORITY: Conditions that determine what is considered high priority for the digest
 * - This could be used to determine sending the digest at a different time or how
 * often it should be sent. It could also be used to format content.
 * - Example:
 * - DSRs that are due within the next week
 * - Privacy requests that are due within the next week
 * - Privacy requests for certain geographic regions
 */
export enum DigestConditionType {
  RECEIVER = "receiver",
  CONTENT = "content",
  PRIORITY = "priority",
}
