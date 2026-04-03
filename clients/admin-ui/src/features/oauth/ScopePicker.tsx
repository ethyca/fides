import { Checkbox } from "fidesui";
import { memo, useMemo, useState } from "react";

import SearchInput from "~/features/common/SearchInput";
import { ScopeRegistryEnum } from "~/types/api";

import {
  formatResourceLabel,
  groupScopesByResource,
} from "./scope-picker.utils";

const ALL_SCOPES = Object.values(ScopeRegistryEnum);
const GROUPED = groupScopesByResource(ALL_SCOPES);
const SORTED_RESOURCES = Object.keys(GROUPED).sort();

interface ScopePickerProps {
  value: string[];
  onChange: (value: string[]) => void;
}

/**
 * A filterable grouped checkbox tree for selecting Fides API scopes.
 *
 * Scopes are grouped by resource (e.g. all `client:*` under "Client").
 * A search input filters both group labels and individual scope actions.
 * Checking a group header toggles all scopes in that group at once.
 *
 * Wrapped in React.memo so it only re-renders when `value` or `onChange`
 * change — not on every keystroke in sibling form fields.
 */
const ScopePicker = memo(({ value: selected, onChange }: ScopePickerProps) => {
  const [search, setSearch] = useState("");

  /**
   * Map of resource → visible scopes after applying the search filter.
   * A resource is included if its label or any of its scopes match the query.
   * When the label matches, all scopes in the group are shown.
   */
  const visibleByResource = useMemo<Map<string, string[]>>(() => {
    if (!search) {
      return new Map(SORTED_RESOURCES.map((r) => [r, GROUPED[r]]));
    }
    const q = search.toLowerCase();
    return new Map(
      SORTED_RESOURCES.reduce<[string, string[]][]>((acc, resource) => {
        const labelMatch = formatResourceLabel(resource)
          .toLowerCase()
          .includes(q);
        const scopes = labelMatch
          ? GROUPED[resource]
          : GROUPED[resource].filter((scope) =>
              scope.toLowerCase().includes(q),
            );
        if (scopes.length > 0) {
          acc.push([resource, scopes]);
        }
        return acc;
      }, []),
    );
  }, [search]);

  const handleGroupToggle = (resource: string, checked: boolean) => {
    const groupScopes = GROUPED[resource];
    if (checked) {
      onChange(Array.from(new Set([...selected, ...groupScopes])));
    } else {
      onChange(selected.filter((s) => !groupScopes.includes(s)));
    }
  };

  const handleScopeToggle = (scope: string, checked: boolean) => {
    if (checked) {
      onChange([...selected, scope]);
    } else {
      onChange(selected.filter((s) => s !== scope));
    }
  };

  const allSelected = ALL_SCOPES.every((s) => selected.includes(s));
  const someSelected = selected.length > 0 && !allSelected;

  const handleSelectAll = (checked: boolean) => {
    onChange(checked ? ALL_SCOPES : []);
  };

  return (
    <div className="flex flex-col gap-3" data-testid="scope-picker">
      <div className="flex items-center justify-between gap-3">
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Filter scopes..."
          data-testid="scope-search"
        />
        <Checkbox
          checked={allSelected}
          indeterminate={someSelected}
          onChange={(e) => handleSelectAll(e.target.checked)}
          className="shrink-0"
          data-testid="scope-select-all"
        >
          Select all
        </Checkbox>
      </div>
      <div
        className="max-h-[400px] overflow-y-auto rounded-md border p-3"
        data-testid="scope-picker-list"
      >
        {visibleByResource.size === 0 ? (
          <span className="text-sm text-gray-500">
            No scopes match &ldquo;{search}&rdquo;.
          </span>
        ) : (
          <div className="flex flex-col gap-3">
            {Array.from(visibleByResource.entries()).map(
              ([resource, scopesInGroup]) => {
                const allGroupScopes = GROUPED[resource];
                const selectedInGroup = allGroupScopes.filter((s) =>
                  selected.includes(s),
                );
                const allGroupSelected =
                  selectedInGroup.length === allGroupScopes.length;
                const someGroupSelected =
                  selectedInGroup.length > 0 && !allGroupSelected;

                return (
                  <div key={resource} className="flex flex-col gap-1">
                    <Checkbox
                      checked={allGroupSelected}
                      indeterminate={someGroupSelected}
                      onChange={(e) =>
                        handleGroupToggle(resource, e.target.checked)
                      }
                      className="font-semibold"
                      data-testid={`scope-group-${resource}`}
                    >
                      {formatResourceLabel(resource)}
                    </Checkbox>
                    <div className="flex flex-row flex-wrap gap-1 pl-6">
                      {scopesInGroup.map((scope) => {
                        const action = scope.split(":")[1];
                        return (
                          <Checkbox
                            key={scope}
                            checked={selected.includes(scope)}
                            onChange={(e) =>
                              handleScopeToggle(scope, e.target.checked)
                            }
                            data-testid={`scope-checkbox-${scope}`}
                          >
                            {action}
                          </Checkbox>
                        );
                      })}
                    </div>
                  </div>
                );
              },
            )}
          </div>
        )}
      </div>
      <span
        className="text-sm text-gray-500"
        data-testid="scope-selected-count"
      >
        {selected.length} scope{selected.length !== 1 ? "s" : ""} selected
      </span>
    </div>
  );
});

ScopePicker.displayName = "ScopePicker";

export default ScopePicker;
