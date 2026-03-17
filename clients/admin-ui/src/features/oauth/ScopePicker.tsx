import { Checkbox } from "fidesui";
import { useFormikContext } from "formik";
import { useMemo, useState } from "react";

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
  /** Formik field name that holds the selected scopes array */
  name: string;
}

/**
 * A filterable grouped checkbox tree for selecting Fides API scopes.
 *
 * Scopes are grouped by resource (e.g. all `client:*` under "Client").
 * A search input filters both group labels and individual scope actions.
 * Checking a group header toggles all scopes in that group at once.
 */
const ScopePicker = ({ name }: ScopePickerProps) => {
  const { values, setFieldValue } =
    useFormikContext<Record<string, string[]>>();

  const selected: string[] = values[name] ?? [];
  const [search, setSearch] = useState("");

  const visibleResources = useMemo(() => {
    if (!search) return SORTED_RESOURCES;
    const q = search.toLowerCase();
    return SORTED_RESOURCES.filter(
      (resource) =>
        formatResourceLabel(resource).toLowerCase().includes(q) ||
        GROUPED[resource].some((scope) => scope.toLowerCase().includes(q)),
    );
  }, [search]);

  const visibleScopesForResource = (resource: string): string[] => {
    if (!search) return GROUPED[resource];
    const q = search.toLowerCase();
    // If the group label matches, show all scopes in the group
    if (formatResourceLabel(resource).toLowerCase().includes(q)) {
      return GROUPED[resource];
    }
    return GROUPED[resource].filter((scope) => scope.toLowerCase().includes(q));
  };

  const handleGroupToggle = (resource: string, checked: boolean) => {
    const groupScopes = GROUPED[resource];
    if (checked) {
      setFieldValue(name, Array.from(new Set([...selected, ...groupScopes])));
    } else {
      setFieldValue(
        name,
        selected.filter((s) => !groupScopes.includes(s)),
      );
    }
  };

  const handleScopeToggle = (scope: string, checked: boolean) => {
    if (checked) {
      setFieldValue(name, [...selected, scope]);
    } else {
      setFieldValue(
        name,
        selected.filter((s) => s !== scope),
      );
    }
  };

  const allSelected = ALL_SCOPES.every((s) => selected.includes(s));
  const someSelected = selected.length > 0 && !allSelected;

  const handleSelectAll = (checked: boolean) => {
    setFieldValue(name, checked ? ALL_SCOPES : []);
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
        className="max-h-[400px] overflow-y-auto border rounded-md p-3"
        data-testid="scope-picker-list"
      >
        {visibleResources.length === 0 ? (
          <span className="text-sm text-gray-500">
            No scopes match &ldquo;{search}&rdquo;.
          </span>
        ) : (
          <div className="flex flex-col gap-3">
            {visibleResources.map((resource) => {
              const scopesInGroup = visibleScopesForResource(resource);
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
            })}
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
};

export default ScopePicker;
