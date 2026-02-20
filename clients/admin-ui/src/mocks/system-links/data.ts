/**
 * Mock data types for system links
 */

export enum SystemConnectionLinkType {
  DSR = "dsr",
  MONITORING = "monitoring",
}

export interface SystemLink {
  system_fides_key: string;
  system_name: string | null;
  link_type: SystemConnectionLinkType;
  created_at: string;
}

/**
 * In-memory store for system links by connection key
 * Format: Map<connection_key, Map<system_fides_key, Map<link_type, SystemLink>>>
 */
export const systemLinksStore = new Map<
  string,
  Map<string, Map<SystemConnectionLinkType, SystemLink>>
>();

/**
 * Helper to get all links for a connection
 */
export const getLinksForConnection = (connectionKey: string): SystemLink[] => {
  const connectionLinks = systemLinksStore.get(connectionKey);
  if (!connectionLinks) {
    return [];
  }

  const allLinks: SystemLink[] = [];
  connectionLinks.forEach((linkTypeMap) => {
    linkTypeMap.forEach((link) => {
      allLinks.push(link);
    });
  });
  return allLinks;
};

/**
 * Helper to get all connection keys that have links
 */
export const getAllConnectionKeys = (): string[] => {
  return Array.from(systemLinksStore.keys());
};

/**
 * Helper to add or update a link
 */
export const setLink = (
  connectionKey: string,
  systemFidesKey: string,
  linkType: SystemConnectionLinkType,
  systemName: string | null,
): SystemLink => {
  let connectionLinks = systemLinksStore.get(connectionKey);
  if (!connectionLinks) {
    connectionLinks = new Map();
    systemLinksStore.set(connectionKey, connectionLinks);
  }

  let systemLinks = connectionLinks.get(systemFidesKey);
  if (!systemLinks) {
    systemLinks = new Map();
    connectionLinks.set(systemFidesKey, systemLinks);
  }

  // If a link with the same link_type already exists for a different system, remove it
  // (idempotent replace behavior)
  connectionLinks.forEach((linkTypeMap, existingSystemKey) => {
    if (existingSystemKey !== systemFidesKey && linkTypeMap.has(linkType)) {
      linkTypeMap.delete(linkType);
      if (linkTypeMap.size === 0) {
        connectionLinks!.delete(existingSystemKey);
      }
    }
  });

  const now = new Date().toISOString();
  const link: SystemLink = {
    system_fides_key: systemFidesKey,
    system_name: systemName,
    link_type: linkType,
    created_at: now,
  };

  systemLinks.set(linkType, link);
  return link;
};

/**
 * Helper to remove a link
 */
export const removeLink = (
  connectionKey: string,
  systemFidesKey: string,
  linkType?: SystemConnectionLinkType,
): boolean => {
  const connectionLinks = systemLinksStore.get(connectionKey);
  if (!connectionLinks) {
    return false;
  }

  const systemLinks = connectionLinks.get(systemFidesKey);
  if (!systemLinks) {
    return false;
  }

  if (linkType) {
    // Remove specific link type
    const removed = systemLinks.delete(linkType);
    if (systemLinks.size === 0) {
      connectionLinks.delete(systemFidesKey);
    }
    if (connectionLinks.size === 0) {
      systemLinksStore.delete(connectionKey);
    }
    return removed;
  }
  // Remove all link types for this system
  connectionLinks.delete(systemFidesKey);
  if (connectionLinks.size === 0) {
    systemLinksStore.delete(connectionKey);
  }
  return true;
};

/**
 * Helper to check if a link exists
 */
export const linkExists = (
  connectionKey: string,
  systemFidesKey: string,
  linkType?: SystemConnectionLinkType,
): boolean => {
  const connectionLinks = systemLinksStore.get(connectionKey);
  if (!connectionLinks) {
    return false;
  }

  const systemLinks = connectionLinks.get(systemFidesKey);
  if (!systemLinks) {
    return false;
  }

  if (linkType) {
    return systemLinks.has(linkType);
  }
  return systemLinks.size > 0;
};

/**
 * Mock system names for common system keys
 */
export const mockSystemNames: Record<string, string> = {
  my_system: "My System",
  postgres_system: "Postgres System",
  bigquery_system: "BigQuery System",
  snowflake_system: "Snowflake System",
};

/**
 * Get system name from mock data or return null
 */
export const getSystemName = (systemFidesKey: string): string | null => {
  return mockSystemNames[systemFidesKey] || null;
};

/**
 * Sample connection data for mocking GET /connection responses
 * These connections will be returned with linked_systems merged in when available
 */
export interface MockConnection {
  key: string;
  name: string;
  connection_type: string;
  description?: string | null;
  access: "read" | "write";
  created_at: string;
  updated_at?: string | null;
  disabled?: boolean | null;
  last_test_timestamp?: string | null;
  last_test_succeeded?: boolean | null;
  authorized?: boolean | null;
  enabled_actions?: string[] | null;
  secrets?: null;
  saas_config?: null;
}

export const mockConnections: MockConnection[] = [
  {
    key: "my_postgres_connection",
    name: "My Postgres",
    connection_type: "postgres",
    description: "Production PostgreSQL database",
    access: "read",
    created_at: "2026-01-15T08:00:00Z",
    updated_at: "2026-01-20T10:30:00Z",
    disabled: false,
    last_test_timestamp: "2026-02-18T12:00:00Z",
    last_test_succeeded: true,
    authorized: true,
    enabled_actions: ["access", "erasure"],
    secrets: null,
    saas_config: null,
  },
  {
    key: "bigquery_warehouse",
    name: "BigQuery Warehouse",
    connection_type: "bigquery",
    description: "Analytics data warehouse",
    access: "read",
    created_at: "2026-01-10T09:00:00Z",
    updated_at: "2026-02-15T14:20:00Z",
    disabled: false,
    last_test_timestamp: "2026-02-17T11:00:00Z",
    last_test_succeeded: true,
    authorized: true,
    enabled_actions: ["access"],
    secrets: null,
    saas_config: null,
  },
  {
    key: "snowflake_analytics",
    name: "Snowflake Analytics",
    connection_type: "snowflake",
    description: "Data warehouse for analytics",
    access: "read",
    created_at: "2026-01-12T10:00:00Z",
    updated_at: "2026-02-10T16:45:00Z",
    disabled: false,
    last_test_timestamp: "2026-02-16T09:30:00Z",
    last_test_succeeded: true,
    authorized: true,
    enabled_actions: ["access", "erasure"],
    secrets: null,
    saas_config: null,
  },
  {
    key: "mysql_production",
    name: "MySQL Production",
    connection_type: "mysql",
    description: "Primary MySQL database",
    access: "read",
    created_at: "2026-01-08T07:00:00Z",
    updated_at: "2026-02-12T13:15:00Z",
    disabled: false,
    last_test_timestamp: "2026-02-15T08:00:00Z",
    last_test_succeeded: true,
    authorized: true,
    enabled_actions: ["access", "erasure", "consent"],
    secrets: null,
    saas_config: null,
  },
  {
    key: "mongodb_content",
    name: "MongoDB Content Store",
    connection_type: "mongodb",
    description: "Content management database",
    access: "read",
    created_at: "2026-01-20T11:00:00Z",
    updated_at: "2026-02-18T10:00:00Z",
    disabled: false,
    last_test_timestamp: "2026-02-18T10:00:00Z",
    last_test_succeeded: true,
    authorized: true,
    enabled_actions: ["access"],
    secrets: null,
    saas_config: null,
  },
];

/**
 * Get mock connection by key
 */
export const getMockConnection = (
  connectionKey: string,
): MockConnection | undefined => {
  return mockConnections.find((conn) => conn.key === connectionKey);
};

/**
 * Get all mock connections
 */
export const getAllMockConnections = (): MockConnection[] => {
  return mockConnections;
};
