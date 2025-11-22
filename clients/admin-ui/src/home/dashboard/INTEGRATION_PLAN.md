# Dashboard Data Integration Plan

## Overview
This document outlines the plan to replace dummy data with real API data for the dashboard insights feature.

---

## 1. Helios Section - Data Detection and Classification

### 1.1 Discovered Fields Breakdown (Unlabeled, In review, Approved, Confirmed)

**Data Needed:**
- Count of fields by status:
  - Unlabeled (diff_status: `addition`)
  - In review (diff_status: `classification_addition`, `classification_update`)
  - Approved (diff_status: `approved`)
  - Confirmed (diff_status: `monitored`)

**Existing Endpoints:**
- ✅ **Available**: `POST /plus/discovery-monitor/{monitor_config_id}/fields/allowed-actions`
  - Returns `diff_statuses_with_counts` which includes counts by diff_status
  - **Limitation**: Requires a specific monitor_config_id, returns counts for filtered fields only

**New Endpoint Needed:**
- ❌ **Create**: `GET /plus/discovery-monitor/fields/status-summary`
  - Should return aggregate counts across ALL monitors (or optionally filtered)
  - Response format:
    ```json
    {
      "unlabeled": 450,
      "in_review": 320,
      "approved": 280,
      "confirmed": 150,
      "total": 1200
    }
    ```
  - **Alternative**: Could use existing `GET /plus/discovery-monitor/aggregate-results` but would need to aggregate across all monitors

**Implementation Notes:**
- The existing `get_distinct_diff_statuses()` method in `DatastoreMonitorResourcesQueryService` already provides this functionality per monitor
- Need to aggregate across all monitors or create a new service method

---

### 1.2 Classification Activity Over Time

**Data Needed:**
- Time series data showing:
  - `discovered`: New fields discovered per time period
  - `reviewed`: Fields reviewed per time period
  - `approved`: Fields approved per time period
- Grouped by date (monthly or weekly)

**Existing Endpoints:**
- ❌ **Not Available**: No existing endpoint provides time-series classification activity

**New Endpoint Needed:**
- ❌ **Create**: `GET /plus/discovery-monitor/fields/activity-over-time`
  - Query params:
    - `start_date` (optional)
    - `end_date` (optional)
    - `group_by` (optional: "day", "week", "month" - default: "month")
  - Response format:
    ```json
    {
      "data": [
        {
          "date": "2024-01",
          "discovered": 120,
          "reviewed": 80,
          "approved": 60
        },
        ...
      ]
    }
    ```
  - **Implementation**: Query `staged_resources` table with date filters and group by created_at/updated_at

---

### 1.3 Data Categories Treemap

**Data Needed:**
- Count of fields by data category
- Data category name (e.g., "User.contact.email")
- Count/value for each category

**Existing Endpoints:**
- ✅ **Partially Available**:
  - `GET /plus/discovery-monitor/{monitor_config_id}/fields` with `data_category` filter
  - Can query fields and count by data_category
  - **Limitation**: Requires iterating through all fields or using aggregation

**New Endpoint Needed:**
- ❌ **Create**: `GET /plus/discovery-monitor/fields/data-categories-summary`
  - Returns aggregated counts by data category across all monitors
  - Response format:
    ```json
    {
      "data": [
        {
          "name": "User.contact.email",
          "value": 400
        },
        {
          "name": "User.contact.phone",
          "value": 350
        },
        ...
      ]
    }
    ```
  - **Implementation**:
    - Query `staged_resources` table
    - Extract data categories from `classifications` or `user_assigned_data_categories` fields
    - Group by data category and count
    - Consider using PostgreSQL JSONB functions for efficient extraction

---

## 2. Janus Section - Consent

### 2.1 Opt In vs Opt Out Rates Over Time

**Data Needed:**
- Time series data showing:
  - `optIn`: Percentage or count of opt-in consents per time period
  - `optOut`: Percentage or count of opt-out consents per time period
- Grouped by date

**Existing Endpoints:**
- ✅ **Available**:
  - `GET /historical-privacy-preferences` (via `useGetAllHistoricalPrivacyPreferencesQuery`)
  - Returns paginated consent data with `opt_in` field and `request_timestamp`
  - Can filter by date range: `request_timestamp_gt`, `request_timestamp_lt`

**Implementation Approach:**
- ✅ **Can Use Existing**: Query `historical-privacy-preferences` endpoint
  - Fetch data for desired date range
  - Group by date (month/week) and calculate opt-in vs opt-out percentages
  - **Note**: May need to fetch multiple pages if data spans long periods
  - **Optimization**: Could create a dedicated aggregation endpoint

**New Endpoint (Optional Optimization):**
- ⚠️ **Recommended**: `GET /plus/consent-reporting/rates-over-time`
  - Pre-aggregated endpoint for better performance
  - Query params: `start_date`, `end_date`, `group_by`
  - Response format:
    ```json
    {
      "data": [
        {
          "date": "2024-01",
          "optIn": 65,
          "optOut": 35
        },
        ...
      ]
    }
    ```

---

## 3. Lethe Section - Data Subject Requests (DSRs)

### 3.1 Privacy Requests Needing Approval

**Data Needed:**
- Count of privacy requests with status `pending` (awaiting approval)

**Existing Endpoints:**
- ✅ **Available**:
  - `POST /privacy-request/search` (via `useSearchPrivacyRequestsQuery`)
  - Can filter by `status: ["pending"]`
  - Returns paginated results with `total` count

**Implementation Approach:**
- ✅ **Can Use Existing**:
  - Query with `status: ["pending"]` and `size: 1` to get just the count
  - Use the `total` field from paginated response
  - **Note**: This is efficient as we only need the count, not the actual records

---

### 3.2 Pending Manual Tasks

**Data Needed:**
- Count of manual tasks with status `pending` (or not completed)

**Existing Endpoints:**
- ✅ **Available**:
  - `GET /plus/manual-fields` (via `useGetTasksQuery`)
  - Can filter by `status` parameter
  - Returns paginated results with counts

**Implementation Approach:**
- ✅ **Can Use Existing**:
  - Query with `status: ManualFieldStatus.NEW` (status = "new")
  - Use pagination with `size: 1` to get just the count
  - Use the `total` field from paginated response
  - **Note**: ManualFieldStatus enum has: `NEW`, `COMPLETED`, `SKIPPED`

---

## Summary

### Endpoints That Can Be Used As-Is:
1. ✅ **Privacy Requests Needing Approval**: Use `POST /privacy-request/search` with status filter
2. ✅ **Pending Manual Tasks**: Use `GET /plus/manual-fields` with status filter
3. ✅ **Opt In/Out Rates**: Use `GET /historical-privacy-preferences` (may need client-side aggregation)

### Endpoints That Need to Be Created:
1. ❌ **Discovered Fields Status Summary**: Aggregate counts across all monitors
2. ❌ **Classification Activity Over Time**: Time-series aggregation endpoint
3. ❌ **Data Categories Summary**: Aggregate counts by data category
4. ⚠️ **Consent Rates Over Time** (optional): Pre-aggregated endpoint for better performance

### Implementation Priority:
1. **High Priority** (Core functionality):
   - Discovered Fields Status Summary
   - Privacy Requests Needing Approval (use existing)
   - Pending Manual Tasks (use existing)

2. **Medium Priority** (Enhanced insights):
   - Classification Activity Over Time
   - Data Categories Summary

3. **Low Priority** (Optimization):
   - Consent Rates Over Time (can use existing with client-side aggregation initially)

---

## Next Steps

1. **Backend Development**:
   - Create new aggregation endpoints for Helios data
   - Consider creating a dedicated dashboard API route: `/plus/dashboard/insights`

2. **Frontend Integration**:
   - Update `useHeliosData()`, `useJanusData()`, `useLetheData()` hooks
   - Replace dummy data with API calls
   - Add error handling and loading states
   - Add date range selectors for time-series charts

3. **Testing**:
   - Test with real data
   - Handle edge cases (empty data, large datasets)
   - Performance testing for aggregation queries
