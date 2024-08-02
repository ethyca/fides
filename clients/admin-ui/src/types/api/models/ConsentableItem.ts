/**
 * 3rd-party consentable item and privacy notice relationships
 */
export interface ConsentableItem {
  id: string;
  type: string;
  name: string;
  notice_id?: string | null;
  children?: ConsentableItem[];
  unmapped?: boolean;
}
