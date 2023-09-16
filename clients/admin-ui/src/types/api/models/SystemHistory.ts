export type SystemHistory = {
  edited_by: string;
  system_id: string;
  before: Record<string, any>;
  after: Record<string, any>;
  created_at: string;
};
