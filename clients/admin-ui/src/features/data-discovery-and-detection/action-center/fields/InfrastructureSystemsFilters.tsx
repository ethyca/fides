import { AntTreeDataNode as DataNode, Filter } from "fidesui";
import { uniq } from "lodash";
import { useEffect, useMemo, useState } from "react";

import {
    INFRASTRUCTURE_SYSTEM_FILTER_LABELS,
    INFRASTRUCTURE_SYSTEM_FILTER_SECTION_KEYS,
    INFRASTRUCTURE_SYSTEM_FILTERS,
    InfrastructureSystemFilterLabel,
} from "../constants/InfrastructureSystemsFilters.const";
import { useInfrastructureSystemsFilters } from "./useInfrastructureSystemsFilters";

export const InfrastructureSystemsFilters = ({
    statusFilters,
    setStatusFilters,
    vendorFilters,
    setVendorFilters,
    resetToInitialState,
}: ReturnType<typeof useInfrastructureSystemsFilters>) => {
    // Local state for filter changes (not applied until "Apply" is clicked)
    const [localStatusFilters, setLocalStatusFilters] = useState<
        InfrastructureSystemFilterLabel[] | null
    >(statusFilters);
    const [localVendorFilters, setLocalVendorFilters] = useState<string[] | null>(
        vendorFilters,
    );

    // Initialize with status section expanded by default
    const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([
        INFRASTRUCTURE_SYSTEM_FILTER_SECTION_KEYS.STATUS,
    ]);

    // Sync local state when external state changes
    useEffect(() => {
        setLocalStatusFilters(statusFilters);
    }, [statusFilters]);

    useEffect(() => {
        setLocalVendorFilters(vendorFilters);
    }, [vendorFilters]);

    // Build tree data for filters
    const statusTreeData: DataNode[] = useMemo(
        () =>
            INFRASTRUCTURE_SYSTEM_FILTERS.filter(
                (filter) =>
                    filter !== "all" && filter !== "known" && filter !== "unknown",
            ).map((filter) => ({
                title: INFRASTRUCTURE_SYSTEM_FILTER_LABELS[filter],
                key: filter,
                checkable: true,
                selectable: false,
                isLeaf: true,
            })),
        [],
    );

    const vendorTreeData: DataNode[] = useMemo(
        () =>
            INFRASTRUCTURE_SYSTEM_FILTERS.filter(
                (filter) => filter === "known" || filter === "unknown",
            ).map((filter) => ({
                title: INFRASTRUCTURE_SYSTEM_FILTER_LABELS[filter],
                key: filter,
                checkable: true,
                selectable: false,
                isLeaf: true,
            })),
        [],
    );

    // Combine status and vendor trees
    const treeData: DataNode[] = useMemo(() => {
        const sections: DataNode[] = [];

        if (statusTreeData.length > 0) {
            sections.push({
                title: "Status",
                key: INFRASTRUCTURE_SYSTEM_FILTER_SECTION_KEYS.STATUS,
                checkable: true,
                selectable: false,
                isLeaf: false,
                children: statusTreeData,
            });
        }

        if (vendorTreeData.length > 0) {
            sections.push({
                title: "Vendor",
                key: INFRASTRUCTURE_SYSTEM_FILTER_SECTION_KEYS.VENDOR,
                checkable: true,
                selectable: false,
                isLeaf: false,
                children: vendorTreeData,
            });
        }

        return sections;
    }, [statusTreeData, vendorTreeData]);

    // Get current checked keys from LOCAL state
    const checkedKeys = useMemo(
        () => uniq([...(localStatusFilters ?? []), ...(localVendorFilters ?? [])]),
        [localStatusFilters, localVendorFilters],
    );

    // Calculate active filters count from APPLIED state (not local)
    const activeFiltersCount = useMemo(() => {
        let count = 0;
        if (statusFilters) {
            count += new Set(statusFilters).size;
        }
        if (vendorFilters) {
            count += new Set(vendorFilters).size;
        }
        return count;
    }, [statusFilters, vendorFilters]);

    const handleCheck = (
        checked: React.Key[] | { checked: React.Key[]; halfChecked: React.Key[] },
    ) => {
        const checkedKeysArray = Array.isArray(checked) ? checked : checked.checked;
        // Separate status and vendor selections based on their keys
        const statusKeys: InfrastructureSystemFilterLabel[] = [];
        const vendorKeys: string[] = [];

        // Section keys that should be excluded from filter values
        const sectionKeys = Object.values(
            INFRASTRUCTURE_SYSTEM_FILTER_SECTION_KEYS,
        );

        checkedKeysArray.forEach((key) => {
            const keyStr = key.toString();

            // Skip section keys
            if (sectionKeys.some((sk) => sk === keyStr)) {
                return;
            }

            const statusKey = INFRASTRUCTURE_SYSTEM_FILTERS.find(
                (fs) => fs === keyStr && fs !== "known" && fs !== "unknown",
            );
            if (statusKey) {
                statusKeys.push(statusKey);
            } else {
                const vendorKey = INFRASTRUCTURE_SYSTEM_FILTERS.find(
                    (fs) => fs === keyStr && (fs === "known" || fs === "unknown"),
                );
                if (vendorKey) {
                    vendorKeys.push(vendorKey);
                }
            }
        });

        // Update LOCAL state only (not applied until "Apply" is clicked)
        setLocalStatusFilters(statusKeys.length > 0 ? statusKeys : []);
        setLocalVendorFilters(vendorKeys.length > 0 ? vendorKeys : []);
    };

    const handleReset = () => {
        resetToInitialState();
        setLocalStatusFilters([]);
        setLocalVendorFilters([]);
    };

    const handleClear = () => {
        setLocalStatusFilters([]);
        setLocalVendorFilters([]);
    };

    const handleApply = () => {
        setStatusFilters(
            localStatusFilters && localStatusFilters.length > 0
                ? Array.from(new Set(localStatusFilters))
                : localStatusFilters,
        );
        setVendorFilters(
            localVendorFilters && localVendorFilters.length > 0
                ? Array.from(new Set(localVendorFilters))
                : localVendorFilters,
        );
    };

    const handleExpand = (keys: React.Key[]) => {
        setExpandedKeys(keys);
    };

    const handleOpenChange = (open: boolean) => {
        if (!open) {
            // When popover closes without applying, reset local state to match applied state
            setLocalStatusFilters(statusFilters);
            setLocalVendorFilters(vendorFilters);
        }
    };

    return (
        <Filter
            treeProps={{
                checkable: true,
                checkedKeys,
                onCheck: handleCheck,
                treeData,
                expandedKeys,
                onExpand: handleExpand,
            }}
            onApply={handleApply}
            onReset={handleReset}
            onClear={handleClear}
            onOpenChange={handleOpenChange}
            activeFiltersCount={activeFiltersCount}
        />
    );
};
