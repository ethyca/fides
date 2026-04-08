# System Inventory — Backend Dependencies

All API endpoints needed to make the system inventory feature production-ready. Grouped by: existing endpoints (already built), endpoints needing enhancement, and net-new endpoints.

---

## Existing endpoints (no BE work needed)

These endpoints already exist and can be consumed as-is.

### System CRUD
| Method | Endpoint | Used for |
|--------|----------|----------|
| `GET /system` | List all systems with filtering, pagination, sorting | Inventory card grid |
| `GET /system/{fides_key}` | Get single system | Detail page |
| `PUT /system` | Update system | About edit modal, Advanced tab save |
| `DELETE /system/{key}` | Delete system | Delete confirmation modal |
| `POST /system/assign-steward` | Bulk assign stewards | Steward picker modal |

### System Assets
| Method | Endpoint | Used for |
|--------|----------|----------|
| `GET /plus/system-assets/{fides_key}` | List assets (cookies, pixels, tags) | Assets tab |
| `POST /plus/system-assets/{key}/assets` | Add asset | Add asset modal |
| `PUT /plus/system-assets/{key}/assets/` | Update assets | Edit asset modal |
| `DELETE /plus/system-assets/{key}/assets` | Delete assets | Delete asset button |

### Datasets
| Method | Endpoint | Used for |
|--------|----------|----------|
| `GET /dataset` | List all datasets | Dataset picker modal |
| `GET /dataset/{key}` | Get single dataset | YAML viewer |

### System History
| Method | Endpoint | Used for |
|--------|----------|----------|
| `GET /plus/system/{key}/history` | Paginated history | History tab |

### Connections
| Method | Endpoint | Used for |
|--------|----------|----------|
| `GET /system/{key}/connection` | Get connection configs | Integrations table |
| `PATCH /system/{key}/connection` | Update connection | Integration edit modal |
| `PATCH /system/{key}/connection/secrets` | Update secrets | Keyfile creds editor |
| `DELETE /system/{key}/connection` | Delete connection | Remove integration |

### Data Categories
| Method | Endpoint | Used for |
|--------|----------|----------|
| `GET /data_category` | List all categories | Data category tags, classification |

### Dashboard
| Method | Endpoint | Used for |
|--------|----------|----------|
| `GET /plus/dashboard/posture` | Governance posture | Could feed inventory health if adapted |
| `GET /plus/dashboard/system-coverage` | System coverage stats | Inventory breakdown |
| `GET /plus/dashboard/activity-feed` | Activity feed | Recent activity panel |

---

## Endpoints needing enhancement

These exist but need modifications to support system inventory features.

### 1. System list — add governance score fields
**Endpoint**: `GET /system`
**Current**: Returns `BasicSystemResponseExtended` which includes most fields.
**Needed**: Add computed fields to the response:
- `governance_score: number` — average of 4 pillars
- `annotation_percent: number` — already exists
- `issue_count: number` — count of governance issues
- `has_steward: boolean` — whether stewards are assigned
- `has_purposes: boolean` — whether purposes are defined
- `capabilities: string[]` — derived from active connections (DSR, monitoring, consent)

**Why**: The card grid needs these for sorting, filtering, and display without making N+1 requests per system.

### 2. System history — add classification-level detail
**Endpoint**: `GET /plus/system/{key}/history`
**Current**: Returns `SystemHistoryResponse` with basic fields.
**Needed**: Extend response with optional classification fields:
```python
class SystemHistoryResponse(BaseModel):
    timestamp: datetime
    action: str
    category: str          # "classification", "steward", "integration", "purpose", "system"
    user: str
    detail: str
    field_name: Optional[str] = None    # NEW: e.g. "user.email"
    old_value: Optional[str] = None     # NEW: previous label
    new_value: Optional[str] = None     # NEW: new label
    reason: Optional[str] = None        # NEW: why the change was made
```

**Why**: The History tab needs field-level classification audit trail (who approved what field, what label was changed, why).

### 3. System history — add category filter
**Endpoint**: `GET /plus/system/{key}/history`
**Current**: Pagination only (`page`, `size`).
**Needed**: Add query params:
- `category: Optional[str]` — filter by "classification", "steward", etc.
- `user: Optional[str]` — filter by actor
- `search: Optional[str]` — full-text search on detail/action

**Why**: The History tab has filter dropdowns that need server-side filtering for large audit logs.

### 4. Dataset response — add data categories and DSR scope
**Endpoint**: `GET /dataset` and `GET /dataset/{key}`
**Current**: Returns collections and fields but not aggregated data categories.
**Needed**: Add to response:
- `data_categories: list[str]` — aggregated from all fields
- `dsr_scope: list[str]` — which DSR actions this dataset supports ("access", "erasure")
- `status: str` — approval status ("approved", "pending", "draft")

**Why**: The Datasets tab shows data categories and DSR scope per dataset.

---

## Net-new endpoints

These don't exist yet and need to be built.

### 1. System inventory health aggregate
```
GET /plus/system-inventory/health
```
**Response**:
```json
{
  "score": 75,
  "dimensions": [
    { "label": "Annotation", "score": 58 },
    { "label": "Compliance", "score": 92 },
    { "label": "Purpose", "score": 84 },
    { "label": "Ownership", "score": 66 }
  ],
  "total_systems": 29,
  "total_issues": 31,
  "health_breakdown": { "healthy": 20, "issues": 9 },
  "systems_with_stewards": 17,
  "systems_with_purposes": 20
}
```
**Why**: Powers the inventory health donut, key, and metadata. Currently hardcoded in `computeGovernanceDimensions()`.

### 2. System inventory health trend
```
GET /plus/system-inventory/health/trend?period=6m
```
**Response**:
```json
{
  "data": [
    { "month": "2025-10", "annotation": 5.5, "compliance": 12, "purpose": 8.75, "ownership": 7.5 },
    ...
    { "month": "2026-03", "annotation": 14.5, "compliance": 23, "purpose": 21, "ownership": 16.5 }
  ]
}
```
**Why**: Powers the stacked area chart. Each pillar contributes `score/4` so they stack to the overall score. Requires storing monthly governance snapshots.

**BE work**: Create a scheduled job or trigger that snapshots the 4 pillar scores monthly. Store in a time-series table (`system_inventory_health_snapshot`).

### 3. System governance score (per-system)
```
GET /plus/system/{fides_key}/governance-score
```
**Response**:
```json
{
  "score": 96,
  "dimensions": [
    { "label": "Annotation", "score": 85 },
    { "label": "Compliance", "score": 100 },
    { "label": "Purpose", "score": 100 },
    { "label": "Ownership", "score": 100 }
  ]
}
```
**Why**: Powers the detail page donut. Currently computed client-side in `computeSystemDimensions()`. Server-side computation ensures consistency and allows the score to incorporate more signals (classification approval rate, DSR health, etc.).

### 4. System capabilities (derived)
```
GET /plus/system/{fides_key}/capabilities
```
**Response**:
```json
{
  "capabilities": ["DSARs", "Monitoring", "Consent", "Integrations", "Classification"]
}
```
**Why**: Currently derived client-side from integration/monitor/classification data. Server-side derivation is more reliable and can factor in connection status.

**Alternative**: Add `capabilities` to the existing `GET /system/{fides_key}` response instead of a separate endpoint.

### 5. AI briefing for system
```
GET /plus/system/{fides_key}/briefing
```
**Response**:
```json
{
  "briefing": "BigQuery is a data warehouse operated by the Engineering team...",
  "issues": [
    { "label": "1,024 fields need review", "action": "Review fields", "href": "/system-inventory/auth0#assets", "severity": "warning" }
  ]
}
```
**Why**: Currently generated client-side by `buildRichBriefing()` and `getIssues()`. Server-side generation allows LLM-powered summaries (via Astralis) and consistent issue detection.

**Alternative**: Keep client-side generation for V1, migrate to server-side when Astralis integration is ready.

---

## Data model changes

### New table: `system_inventory_health_snapshot`
```sql
CREATE TABLE system_inventory_health_snapshot (
    id UUID PRIMARY KEY,
    snapshot_date DATE NOT NULL,
    annotation_score FLOAT NOT NULL,
    compliance_score FLOAT NOT NULL,
    purpose_score FLOAT NOT NULL,
    ownership_score FLOAT NOT NULL,
    overall_score FLOAT NOT NULL,
    total_systems INT NOT NULL,
    total_issues INT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```
**Purpose**: Store monthly governance health snapshots for the trend chart.
**Population**: Scheduled job runs monthly (or on-demand) computing pillar scores across all systems.

### Extend `SystemHistory` model
Add optional fields:
```python
field_name: Optional[str] = None
old_value: Optional[str] = None
new_value: Optional[str] = None
reason: Optional[str] = None
category: str = "system"  # classification, steward, integration, purpose, system
```

---

## Priority order for BE work

| Priority | Endpoint | Effort | Blocks |
|----------|----------|--------|--------|
| **P0** | Enhance `GET /system` with governance fields | Medium | Card grid sorting/filtering |
| **P0** | Enhance `GET /plus/system/{key}/history` with classification fields + filters | Medium | History tab |
| **P1** | New `GET /plus/system-inventory/health` | Medium | Inventory donut (currently hardcoded) |
| **P1** | Enhance `GET /dataset` with data categories + DSR scope | Low | Datasets tab |
| **P2** | New `GET /plus/system-inventory/health/trend` + snapshot job | High | Trend chart (currently hardcoded mock) |
| **P2** | New `GET /plus/system/{key}/governance-score` | Low | Detail donut (currently client-computed) |
| **P3** | New `GET /plus/system/{key}/briefing` | Medium | AI banner (currently client-generated) |
| **P3** | New `GET /plus/system/{key}/capabilities` | Low | Capabilities card (currently client-derived) |

---

## What can ship without BE changes

The following features work with existing endpoints today:
- System list page (using `GET /system`)
- System detail page structure (using `GET /system/{fides_key}`)
- Assets tab (using existing `/plus/system-assets/` endpoints)
- Integration management (using existing `/system/{key}/connection` endpoints)
- Advanced tab form (using `PUT /system`)
- Basic history (using existing `/plus/system/{key}/history`)
- Delete system (using `DELETE /system/{key}`)

The governance health dashboard, trend chart, and enriched history are the main features that need new BE work.
