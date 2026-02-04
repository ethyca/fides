/* eslint-disable import/no-extraneous-dependencies */
import { rest } from "msw";

import {
  mockInfrastructureSystems,
  mockOktaApp,
  mockOktaMonitor,
} from "./data";

/**
 * MSW handlers for discovery monitor aggregate results
 */
export const discoveryMonitorHandlers = () => {
  const apiBase = "/api/v1";

  return [
    // GET - return mock Okta monitor
    rest.get(
      `${apiBase}/plus/discovery-monitor/aggregate-results`,
      (_req, res, ctx) =>
        res(
          ctx.status(200),
          ctx.json({
            items: [mockOktaMonitor],
            total: 1,
            page: 1,
            size: 25,
            pages: 1,
          }),
        ),
    ),
    // GET - return mock Okta app assets for system aggregate results
    rest.get(
      `${apiBase}/plus/discovery-monitor/system-aggregate-results`,
      (_req, res, ctx) =>
        res(
          ctx.status(200),
          ctx.json({
            items: [mockOktaApp],
            total: 10,
            page: 1,
            size: 25,
            pages: 1,
          }),
        ),
    ),
    // GET - Identity Provider Monitors (Okta) - list all monitors
    rest.get(`${apiBase}/plus/identity-provider-monitors`, (_req, res, ctx) => {
      const page = parseInt(_req.url.searchParams.get("page") || "1", 10);
      const size = parseInt(_req.url.searchParams.get("size") || "50", 10);

      return res(
        ctx.status(200),
        ctx.json({
          items: [mockOktaMonitor],
          total: 1,
          page,
          size,
          pages: 1,
        }),
      );
    }),
    // GET - Identity Provider Monitor Filters - get available filter options
    rest.get(
      `${apiBase}/plus/filters/idp_monitor_resources`,
      (_req, res, ctx) => {
        // Extract unique values from mock data
        const uniqueStatuses = new Set<string>();
        const uniqueVendorIds = new Set<string>();
        const uniqueDataUses = new Set<string>();

        mockInfrastructureSystems.forEach((item) => {
          if (item.diff_status) {
            uniqueStatuses.add(item.diff_status);
          }
          if (item.vendor_id) {
            uniqueVendorIds.add(item.vendor_id);
          }
          if (item.data_uses && item.data_uses.length > 0) {
            item.data_uses.forEach((du: string) => uniqueDataUses.add(du));
          }
        });

        return res(
          ctx.status(200),
          ctx.json({
            diff_status: Array.from(uniqueStatuses).sort(),
            vendor_id: Array.from(uniqueVendorIds).sort(),
            data_uses: Array.from(uniqueDataUses).sort(),
          }),
        );
      },
    ),
    // GET - Identity Provider Monitor Results (Okta) - get results for a monitor
    rest.get(
      `${apiBase}/plus/identity-provider-monitors/:monitor_config_key/results`,
      (_req, res, ctx) => {
        // const { monitor_config_key } = _req.params;
        const page = parseInt(_req.url.searchParams.get("page") || "1", 10);
        const size = parseInt(_req.url.searchParams.get("size") || "50", 10);
        const search = _req.url.searchParams.get("search");
        const diffStatusParam = _req.url.searchParams.get("diff_status");
        const vendorIdParam = _req.url.searchParams.get("vendor_id");
        const dataUsesParam = _req.url.searchParams.get("data_uses");

        // Start with all mock infrastructure systems
        let filteredItems = [...mockInfrastructureSystems];

        // Apply search filter if provided
        if (search) {
          const searchLower = search.toLowerCase();
          filteredItems = filteredItems.filter(
            (item) =>
              item.name?.toLowerCase().includes(searchLower) ||
              item.vendor_id?.toLowerCase().includes(searchLower) ||
              item.description?.toLowerCase().includes(searchLower),
          );
        }

        // Apply diff_status filter if provided
        if (diffStatusParam) {
          const statuses = Array.isArray(diffStatusParam)
            ? diffStatusParam
            : [diffStatusParam];
          filteredItems = filteredItems.filter((item) =>
            statuses.includes(item.diff_status || ""),
          );
        }

        // Apply vendor_id filter if provided
        if (vendorIdParam) {
          const vendorIds = Array.isArray(vendorIdParam)
            ? vendorIdParam
            : [vendorIdParam];
          filteredItems = filteredItems.filter(
            (item) => item.vendor_id && vendorIds.includes(item.vendor_id),
          );
        }

        // Apply data_uses filter if provided
        if (dataUsesParam) {
          const dataUses = Array.isArray(dataUsesParam)
            ? dataUsesParam
            : [dataUsesParam];
          filteredItems = filteredItems.filter((item) => {
            if (!item.data_uses || item.data_uses.length === 0) {
              return false;
            }
            // Check if any of the item's data_uses match any of the filter data_uses
            return item.data_uses.some((du: string) => dataUses.includes(du));
          });
        }

        // Apply pagination
        const startIndex = (page - 1) * size;
        const endIndex = startIndex + size;
        const paginatedItems = filteredItems.slice(startIndex, endIndex);

        return res(
          ctx.status(200),
          ctx.json({
            items: paginatedItems,
            total: filteredItems.length,
            page,
            size,
            pages: Math.ceil(filteredItems.length / size),
          }),
        );
      },
    ),
    // POST - Create Identity Provider Monitor (Okta)
    rest.post(
      `${apiBase}/plus/identity-provider-monitors`,
      (_req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            ...mockOktaMonitor,
            ...(_req.body as Record<string, unknown>),
          }),
        );
      },
    ),
    // POST - Execute Identity Provider Monitor (Okta)
    rest.post(
      `${apiBase}/plus/identity-provider-monitors/:monitor_config_key/execute`,
      (_req, res, ctx) => {
        return res(
          ctx.status(200),
          ctx.json({
            monitor_execution_id: "550e8400-e29b-41d4-a716-446655440000",
            task_id: null,
          }),
        );
      },
    ),
    // POST - Bulk Promote Identity Provider Monitor Results
    rest.post(
      `${apiBase}/plus/identity-provider-monitors/:monitor_config_key/results/bulk-promote`,
      async (req, res, ctx) => {
        const body = await req.json();
        let count = 0;

        // Handle old format (urns array)
        if (Array.isArray(body)) {
          count = body.length;
        } else if (body.urns && Array.isArray(body.urns)) {
          count = body.urns.length;
        } else if (body.bulkSelection) {
          // Handle new format (bulkSelection with filters)
          const { filters, exclude_urns: excludeUrns } = body.bulkSelection;
          let filteredItems = [...mockInfrastructureSystems];

          // Apply filters
          if (filters) {
            if (filters.search) {
              const searchLower = filters.search.toLowerCase();
              filteredItems = filteredItems.filter(
                (item) =>
                  item.name?.toLowerCase().includes(searchLower) ||
                  item.vendor_id?.toLowerCase().includes(searchLower) ||
                  item.description?.toLowerCase().includes(searchLower),
              );
            }
            if (filters.diff_status) {
              const statuses = Array.isArray(filters.diff_status)
                ? filters.diff_status
                : [filters.diff_status];
              filteredItems = filteredItems.filter((item) =>
                statuses.includes(item.diff_status || ""),
              );
            }
            if (filters.vendor_id) {
              const vendorIds = Array.isArray(filters.vendor_id)
                ? filters.vendor_id
                : [filters.vendor_id];
              filteredItems = filteredItems.filter(
                (item) => item.vendor_id && vendorIds.includes(item.vendor_id),
              );
            }
            if (filters.data_uses) {
              filteredItems = filteredItems.filter((item) => {
                if (!item.data_uses || item.data_uses.length === 0) {
                  return false;
                }
                return item.data_uses.some((du: string) =>
                  filters.data_uses.includes(du),
                );
              });
            }
          }

          // Exclude URNs
          if (excludeUrns && Array.isArray(excludeUrns)) {
            filteredItems = filteredItems.filter(
              (item) => !excludeUrns.includes(item.urn),
            );
          }

          count = filteredItems.length;
        }

        return res(
          ctx.status(200),
          ctx.json({
            summary: {
              successful: count,
              failed: 0,
              total_requested: count,
            },
          }),
        );
      },
    ),
    // POST - Bulk Mute Identity Provider Monitor Results
    rest.post(
      `${apiBase}/plus/identity-provider-monitors/:monitor_config_key/results/bulk-mute`,
      async (req, res, ctx) => {
        const body = await req.json();
        let count = 0;

        // Handle old format (urns array)
        if (Array.isArray(body)) {
          count = body.length;
        } else if (body.urns && Array.isArray(body.urns)) {
          count = body.urns.length;
        } else if (body.bulkSelection) {
          // Handle new format (bulkSelection with filters)
          const { filters, exclude_urns: excludeUrns } = body.bulkSelection;
          let filteredItems = [...mockInfrastructureSystems];

          // Apply filters (same logic as bulk-promote)
          if (filters) {
            if (filters.search) {
              const searchLower = filters.search.toLowerCase();
              filteredItems = filteredItems.filter(
                (item) =>
                  item.name?.toLowerCase().includes(searchLower) ||
                  item.vendor_id?.toLowerCase().includes(searchLower) ||
                  item.description?.toLowerCase().includes(searchLower),
              );
            }
            if (filters.diff_status) {
              const statuses = Array.isArray(filters.diff_status)
                ? filters.diff_status
                : [filters.diff_status];
              filteredItems = filteredItems.filter((item) =>
                statuses.includes(item.diff_status || ""),
              );
            }
            if (filters.vendor_id) {
              const vendorIds = Array.isArray(filters.vendor_id)
                ? filters.vendor_id
                : [filters.vendor_id];
              filteredItems = filteredItems.filter(
                (item) => item.vendor_id && vendorIds.includes(item.vendor_id),
              );
            }
            if (filters.data_uses) {
              filteredItems = filteredItems.filter((item) => {
                if (!item.data_uses || item.data_uses.length === 0) {
                  return false;
                }
                return item.data_uses.some((du: string) =>
                  filters.data_uses.includes(du),
                );
              });
            }
          }

          // Exclude URNs
          if (excludeUrns && Array.isArray(excludeUrns)) {
            filteredItems = filteredItems.filter(
              (item) => !excludeUrns.includes(item.urn),
            );
          }

          count = filteredItems.length;
        }

        return res(
          ctx.status(200),
          ctx.json({
            summary: {
              successful: count,
              failed: 0,
              total_requested: count,
            },
          }),
        );
      },
    ),
    // POST - Bulk Unmute Identity Provider Monitor Results
    rest.post(
      `${apiBase}/plus/identity-provider-monitors/:monitor_config_key/results/bulk-unmute`,
      async (req, res, ctx) => {
        const body = await req.json();
        let count = 0;

        // Handle old format (urns array)
        if (Array.isArray(body)) {
          count = body.length;
        } else if (body.urns && Array.isArray(body.urns)) {
          count = body.urns.length;
        } else if (body.bulkSelection) {
          // Handle new format (bulkSelection with filters)
          const { filters, exclude_urns: excludeUrns } = body.bulkSelection;
          let filteredItems = [...mockInfrastructureSystems];

          // Apply filters (same logic as bulk-promote)
          if (filters) {
            if (filters.search) {
              const searchLower = filters.search.toLowerCase();
              filteredItems = filteredItems.filter(
                (item) =>
                  item.name?.toLowerCase().includes(searchLower) ||
                  item.vendor_id?.toLowerCase().includes(searchLower) ||
                  item.description?.toLowerCase().includes(searchLower),
              );
            }
            if (filters.diff_status) {
              const statuses = Array.isArray(filters.diff_status)
                ? filters.diff_status
                : [filters.diff_status];
              filteredItems = filteredItems.filter((item) =>
                statuses.includes(item.diff_status || ""),
              );
            }
            if (filters.vendor_id) {
              const vendorIds = Array.isArray(filters.vendor_id)
                ? filters.vendor_id
                : [filters.vendor_id];
              filteredItems = filteredItems.filter(
                (item) => item.vendor_id && vendorIds.includes(item.vendor_id),
              );
            }
            if (filters.data_uses) {
              filteredItems = filteredItems.filter((item) => {
                if (!item.data_uses || item.data_uses.length === 0) {
                  return false;
                }
                return item.data_uses.some((du: string) =>
                  filters.data_uses.includes(du),
                );
              });
            }
          }

          // Exclude URNs
          if (excludeUrns && Array.isArray(excludeUrns)) {
            filteredItems = filteredItems.filter(
              (item) => !excludeUrns.includes(item.urn),
            );
          }

          count = filteredItems.length;
        }

        return res(
          ctx.status(200),
          ctx.json({
            summary: {
              successful: count,
              failed: 0,
              total_requested: count,
            },
          }),
        );
      },
    ),
  ];
};
