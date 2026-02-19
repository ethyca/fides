/* eslint-disable import/no-extraneous-dependencies */
import { random } from "lodash";
import { rest } from "msw";

import { CONNECTION_ROUTE, PLUS_CONNECTION_API_ROUTE } from "~/constants";

import {
  getAllConnectionKeys,
  getAllMockConnections,
  getLinksForConnection,
  getMockConnection,
  getSystemName,
  linkExists,
  removeLink,
  setLink,
  SystemConnectionLinkType,
} from "./data";

/**
 * MSW handlers for system link endpoints
 */
export const systemLinksHandlers = () => {
  const apiBase = "/api/v1";

  return [
    // PUT /api/v1/plus/connection/{connection_key}/system-links
    // Set system links for an integration
    rest.put<{
      links: Array<{
        system_fides_key: string;
        link_type: SystemConnectionLinkType;
      }>;
    }>(
      `${apiBase}${PLUS_CONNECTION_API_ROUTE}/:connection_key/system-links`,
      async (req, res, ctx) => {
        const { connection_key: connectionKey } = req.params;
        const body = await req.json();

        if (!body.links || !Array.isArray(body.links)) {
          return res(
            ctx.status(400),
            ctx.json({
              detail: "Invalid request body: 'links' must be an array",
            }),
          );
        }

        // Validate all links first
        const invalidLink = body.links.find(
          (link: {
            system_fides_key?: string;
            link_type?: SystemConnectionLinkType;
          }) => !link.system_fides_key || !link.link_type,
        );

        if (invalidLink) {
          return res(
            ctx.status(400),
            ctx.json({
              detail: "Invalid link: missing system_fides_key or link_type",
            }),
          );
        }

        // Set each link
        const responseLinks = body.links.map(
          (link: {
            system_fides_key: string;
            link_type: SystemConnectionLinkType;
          }) => {
            const systemName = getSystemName(link.system_fides_key);
            const createdLink = setLink(
              connectionKey as string,
              link.system_fides_key,
              link.link_type,
              systemName,
            );

            return createdLink;
          },
        );

        return res(
          ctx.status(200),
          ctx.json({
            links: responseLinks,
          }),
        );
      },
    ),

    // DELETE /api/v1/plus/connection/{connection_key}/system-links/{system_fides_key}
    // Remove a system link
    rest.delete(
      `${apiBase}${PLUS_CONNECTION_API_ROUTE}/:connection_key/system-links/:system_fides_key`,
      async (req, res, ctx) => {
        const {
          connection_key: connectionKey,
          system_fides_key: systemFidesKey,
        } = req.params;
        const linkType = req.url.searchParams.get(
          "link_type",
        ) as SystemConnectionLinkType | null;

        const exists = linkExists(
          connectionKey as string,
          systemFidesKey as string,
          linkType || undefined,
        );

        if (!exists) {
          return res(ctx.status(404), ctx.json({ detail: "Link not found" }));
        }

        removeLink(
          connectionKey as string,
          systemFidesKey as string,
          linkType || undefined,
        );

        return res(ctx.status(204));
      },
    ),

    // GET /api/v1/plus/connection/{connection_key}/system-links
    // List system links for an integration
    rest.get(
      `${apiBase}${PLUS_CONNECTION_API_ROUTE}/:connection_key/system-links`,
      (req, res, ctx) => {
        const { connection_key: connectionKey } = req.params;
        const links = getLinksForConnection(connectionKey as string);

        return res(
          ctx.status(200),
          ctx.json({
            links,
          }),
        );
      },
    ),

    // GET /api/v1/connection/{connection_key}
    // Extended response with linked_systems field
    rest.get(
      `${apiBase}${CONNECTION_ROUTE}/:connection_key`,
      (req, res, ctx) => {
        const { connection_key: connectionKey } = req.params;
        const links = getLinksForConnection(connectionKey as string);

        // Get system_key from dsr link for backward compatibility
        const dsrLink = links.find((link) => link.link_type === "dsr");
        const systemKey = dsrLink?.system_fides_key || null;

        // Transform links to linked_systems format
        // If no links exist, use deterministic sample links
        let linkedSystems = links.map((link) => ({
          system_fides_key: link.system_fides_key,
          system_name: link.system_name,
          link_type: link.link_type,
        }));

        // Use deterministic sample links if no actual links exist
        if (linkedSystems.length === 0) {
          linkedSystems = [
            {
              system_fides_key: "test_system_1",
              system_name: "Test System 1",
              link_type: "dsr" as SystemConnectionLinkType,
            },
            {
              system_fides_key: "some_new_system",
              system_name: "Some New System",
              link_type: "monitoring" as SystemConnectionLinkType,
            },
          ];
        }

        // Update system_key from dsr link (either from actual links or deterministic sample)
        const finalSystemKey =
          systemKey ||
          linkedSystems.find((link) => link.link_type === "dsr")
            ?.system_fides_key ||
          null;

        // Try to get mock connection data, otherwise return minimal response
        const mockConnection = getMockConnection(connectionKey as string);
        if (mockConnection) {
          return res(
            ctx.status(200),
            ctx.json({
              ...mockConnection,
              system_key: finalSystemKey,
              linked_systems: linkedSystems,
            }),
          );
        }

        // Fallback to minimal response if no mock data exists
        return res(
          ctx.status(200),
          ctx.json({
            key: connectionKey,
            name: `Connection ${connectionKey}`,
            connection_type: "postgres",
            system_key: finalSystemKey,
            linked_systems: linkedSystems,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            access: "read",
          }),
        );
      },
    ),

    // GET /api/v1/connection
    // Extended list response with linked_systems field for each connection
    rest.get(`${apiBase}${CONNECTION_ROUTE}`, (req, res, ctx) => {
      // Get all mock connections and connection keys that have links
      const mockConnections = getAllMockConnections();
      const linkedConnectionKeys = new Set(getAllConnectionKeys());

      // Build a map of all connections (mock + linked)
      type ConnectionWithLinks = (typeof mockConnections)[0] & {
        system_key: string | null;
        linked_systems: Array<{
          system_fides_key: string;
          system_name: string | null;
          link_type: SystemConnectionLinkType;
        }>;
      };
      const connectionMap = new Map<string, ConnectionWithLinks>();

      // Add all mock connections with empty linked_systems
      mockConnections.forEach((mockConn) => {
        connectionMap.set(mockConn.key, {
          ...mockConn,
          system_key: null,
          linked_systems:
            random(0, 1) > 0.5
              ? [
                  {
                    system_fides_key: "test_system_1",
                    system_name: "Test System 1",
                    link_type: "dsr",
                  },
                  {
                    system_fides_key: "some_new_system",
                    system_name: "Some New System",
                    link_type: "monitoring",
                  },
                ]
              : [],
        });
      });

      // Update connections that have links
      linkedConnectionKeys.forEach((connectionKey) => {
        const links = getLinksForConnection(connectionKey);
        const dsrLink = links.find((link) => link.link_type === "dsr");
        const systemKey = dsrLink?.system_fides_key || null;

        const linkedSystems = links.map((link) => ({
          system_fides_key: link.system_fides_key,
          system_name: link.system_name,
          link_type: link.link_type,
        }));

        const existingConnection = connectionMap.get(connectionKey);
        if (existingConnection) {
          // Update existing mock connection with links
          existingConnection.system_key = systemKey;
          existingConnection.linked_systems = linkedSystems;
        } else {
          // Create new connection entry for linked-only connections
          connectionMap.set(connectionKey, {
            key: connectionKey,
            name: `Connection ${connectionKey}`,
            connection_type: "postgres",
            description: null,
            access: "read",
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            disabled: false,
            last_test_timestamp: null,
            last_test_succeeded: null,
            authorized: null,
            enabled_actions: null,
            secrets: null,
            saas_config: null,
            system_key: systemKey,
            linked_systems: linkedSystems,
          });
        }
      });

      // Convert map to array
      const connections = Array.from(connectionMap.values());

      // Return paginated response format
      const page = parseInt(req.url.searchParams.get("page") ?? "1", 10);
      const size = parseInt(req.url.searchParams.get("size") ?? "50", 10);
      const start = (page - 1) * size;
      const end = start + size;
      const paginatedItems = connections.slice(start, end);

      return res(
        ctx.status(200),
        ctx.json({
          items: paginatedItems,
          total: connections.length,
          page,
          size,
          pages: Math.ceil(connections.length / size),
        }),
      );
    }),
  ];
};
