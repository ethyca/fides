/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Schema to represent 3rd-party consentable items and privacy notice relationships.
 */
export type ConsentableItem = {
  external_id: string;
  type: string;
  name: string;
  notice_id?: string | null;
  children?: Array<ConsentableItem>;
  unmapped?: boolean | null;
};
