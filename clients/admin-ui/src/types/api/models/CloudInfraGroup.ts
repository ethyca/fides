export type CloudInfraGroupSummary = {
  id: string;
  name?: string | null;
  system_key?: string | null;
  system_name?: string | null;
  assignment_promoted: boolean;
};

export type CloudInfraGroupResponse = {
  id: string;
  monitor_config_id: string;
  name?: string | null;
  system_key?: string | null;
  system_name?: string | null;
  resource_count: number;
  promoted_resource_count: number;
  created_at: string;
  updated_at: string;
};

export type CloudInfraGroupRequest = {
  name?: string | null;
  system_key?: string | null;
};

export type CloudInfraAssignmentActionResponse = {
  processed: number;
  skipped: number;
};
