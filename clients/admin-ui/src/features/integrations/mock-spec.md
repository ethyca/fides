2. API Contracts
2.1 Set System Links for an Integration

PUT /api/v1/plus/connection/{connection_key}/system-links

Scope: system_integration_link:create_or_update

Request body:

{
  "links": [
    {
      "system_fides_key": "my_system",
      "link_type": "monitoring"
    }
  ]
}

Response (200):

{
  "links": [
    {
      "system_fides_key": "my_system",
      "system_name": "My System",
      "link_type": "monitoring",
      "created_at": "2026-02-18T12:00:00Z"
    }
  ]
}

Behavior:

    Idempotent replace for the given link_type. If a link with the same (connection_config_id, link_type) already exists pointing to a different system, it is replaced.
    Validates that the system exists and the connection config exists.
    If link_type is dsr, also updates ConnectionConfig.system_id for backward compat.

Schemas:

class SystemLinkRequest(BaseModel):
    system_fides_key: str
    link_type: SystemConnectionLinkType


class SetSystemLinksRequest(BaseModel):
    links: list[SystemLinkRequest]


class SystemLinkResponse(BaseModel):
    system_fides_key: str
    system_name: str | None
    link_type: SystemConnectionLinkType
    created_at: datetime


class SystemLinksResponse(BaseModel):
    links: list[SystemLinkResponse]

2.2 Remove a System Link

DELETE /api/v1/plus/connection/{connection_key}/system-links/{system_fides_key}

Scope: system_integration_link:delete

Query parameter: link_type (optional; if omitted, removes all link types for that system)

Response: 204 No Content

Behavior:

    Removes the link row(s) from the join table.
    If the removed link was link_type=dsr, sets ConnectionConfig.system_id = NULL.
    Returns 404 if the link does not exist.

2.3 List System Links for an Integration

GET /api/v1/plus/connection/{connection_key}/system-links

Scope: system_integration_link:read

Response (200):

{
  "links": [
    {
      "system_fides_key": "my_system",
      "system_name": "My System",
      "link_type": "dsr",
      "created_at": "2026-01-15T08:00:00Z"
    },
    {
      "system_fides_key": "my_system",
      "system_name": "My System",
      "link_type": "monitoring",
      "created_at": "2026-02-18T12:00:00Z"
    }
  ]
}

2.4 Extended GET /connection List Response

The existing GET /api/v1/connection and GET /api/v1/connection/{connection_key} responses gain a new field:

{
  "key": "my_postgres_connection",
  "name": "My Postgres",
  "connection_type": "postgres",
  "system_key": "my_system",
  "linked_systems": [
    {
      "system_fides_key": "my_system",
      "system_name": "My System",
      "link_type": "dsr"
    },
    {
      "system_fides_key": "my_system",
      "system_name": "My System",
      "link_type": "monitoring"
    }
  ]
}

The existing system_key field is preserved (derived from the dsr link) for backward compatibility.