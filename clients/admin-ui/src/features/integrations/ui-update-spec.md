
### 6.2 Integration Detail Page -- System Link Management Panel

**Location:** New section on the integration detail page, below connection configuration.

**Wireframe:**

```
+---------------------------------------------------------+
| Linked systems                                          |
+---------------------------------------------------------+
| My System       (monitoring)               [Unlink]     |
| My System       (dsr)                      [Unlink]     |
|                                                         |
| [+ Link system]                                         |
+---------------------------------------------------------+
```

- **System list:** Each row shows the system name (clickable link to system page), link type badge, and an "Unlink" button.
- **"Link system" action:** Opens an Ant Design Select/AutoComplete dropdown that searches systems via the existing `GET /api/v1/system` API. On selection, calls `PUT /connection/{key}/system-links` with the chosen system and link type.
- **Link type selection:** When linking, a secondary selector or default for `link_type`. For the short-term, default to `monitoring` since that is the primary use case; DSR links are managed through the existing system-side flow.

### 6.3 Scope-Gated Rendering

```tsx
// Unlink button -- only shown if user has the delete scope
<Restrict scopes={[ScopeRegistryEnum.SYSTEM_INTEGRATION_LINK_DELETE]}>
  <Button onClick={handleUnlink}>Unlink</Button>
</Restrict>

// Link system action -- only shown if user has the create scope
<Restrict scopes={[ScopeRegistryEnum.SYSTEM_INTEGRATION_LINK_CREATE_OR_UPDATE]}>
  <Button onClick={handleLinkSystem}>+ Link system</Button>
</Restrict>
```

The `Restrict` component (already in the codebase at `clients/admin-ui/src/features/common/Restrict.tsx`) renders children only if the user has ANY of the listed scopes. The `useHasPermission` hook can be used for more fine-grained conditional logic where needed.
