import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { useHasPermission } from "~/features/common/Restrict";
import type { DigestConfigResponse } from "~/types/api";
import { DigestType, ScopeRegistryEnum } from "~/types/api";

import {
  useDeleteDigestConfigMutation,
  useListDigestConfigsQuery,
} from "../digest-config.slice";

export const useDigestConfigList = () => {
  const router = useRouter();
  const [searchQuery, setSearchQuery] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);

  // Only support manual tasks for now
  const digestType = DigestType.MANUAL_TASKS;

  // Permissions
  const canUpdate = useHasPermission([
    ScopeRegistryEnum.DIGEST_CONFIG_CREATE,
    ScopeRegistryEnum.DIGEST_CONFIG_UPDATE,
  ]);
  const canDelete = useHasPermission([ScopeRegistryEnum.DIGEST_CONFIG_DELETE]);

  // API calls
  const { data, isLoading, refetch } = useListDigestConfigsQuery({
    digest_config_type: digestType,
    page,
    size: pageSize,
  });

  const [deleteDigestConfig, { isLoading: isDeleting }] =
    useDeleteDigestConfigMutation();

  // Delete modal state
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [configToDelete, setConfigToDelete] =
    useState<DigestConfigResponse | null>(null);

  // Filter data by search query
  const filteredData = useMemo(() => {
    if (!data?.items) {
      return [];
    }
    if (!searchQuery) {
      return data.items;
    }

    const query = searchQuery.toLowerCase();
    return data.items.filter(
      (config) =>
        config.name.toLowerCase().includes(query) ||
        config.description?.toLowerCase().includes(query),
    );
  }, [data?.items, searchQuery]);

  // Handlers
  const handleEdit = (config: DigestConfigResponse) => {
    router.push(`/settings/digests/${config.id}`);
  };

  const handleDeleteClick = (config: DigestConfigResponse) => {
    setConfigToDelete(config);
    setDeleteModalOpen(true);
  };

  const confirmDelete = async () => {
    if (!configToDelete) {
      return;
    }

    await deleteDigestConfig({
      config_id: configToDelete.id,
      digest_config_type: digestType,
    });

    setDeleteModalOpen(false);
    setConfigToDelete(null);
    refetch();
  };

  const cancelDelete = () => {
    setDeleteModalOpen(false);
    setConfigToDelete(null);
  };

  return {
    // Data
    data: filteredData,
    total: data?.total ?? 0,
    isLoading,

    // List state
    page,
    pageSize,
    searchQuery,

    // Handlers
    setPage,
    setPageSize,
    setSearchQuery,
    refetch,
    handleEdit,
    handleDeleteClick,

    // Delete modal
    deleteModalOpen,
    configToDelete,
    confirmDelete,
    cancelDelete,
    isDeleting,

    // Permissions
    canUpdate,
    canDelete,
  };
};
