import { Button, Flex, Input, Modal, Select, Tag, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useState } from "react";

import type { MockAsset, MockSystem } from "../../types";

interface AssetsTabProps {
  system: MockSystem;
}

const ASSET_TYPE_OPTIONS = [
  "Cookie",
  "Browser Request",
  "iFrame",
  "Javascript tag",
  "Image",
].map((t) => ({ label: t, value: t }));

const ASSET_TYPE_COLORS: Record<string, string> = {
  Cookie: "sandstone",
  "Browser Request": "olive",
  iFrame: "nectar",
  "Javascript tag": "minos",
  Image: "default",
};

const AssetsTab = ({ system }: AssetsTabProps) => {
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingAsset, setEditingAsset] = useState<MockAsset | null>(null);

  const filtered = system.assets.filter((asset) => {
    if (search) {
      const q = search.toLowerCase();
      if (
        !asset.name.toLowerCase().includes(q) &&
        !asset.domain.toLowerCase().includes(q) &&
        !asset.description?.toLowerCase().includes(q)
      ) {
        return false;
      }
    }
    if (typeFilter && asset.assetType !== typeFilter) {
      return false;
    }
    return true;
  });

  return (
    <Flex vertical gap={12}>
      {/* Toolbar */}
      <Flex justify="space-between" align="center">
        <Input
          placeholder="Search assets..."
          value={search}
          onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
            setSearch(e.target.value)
          }
          allowClear
          size="small"
          style={{ width: 260 }}
        />
        <Flex gap={12} align="center">
          <Select
            aria-label="Filter by asset type"
            placeholder="All types"
            value={typeFilter}
            onChange={setTypeFilter}
            allowClear
            size="small"
            className="w-[160px]"
            options={ASSET_TYPE_OPTIONS}
          />
          <Text type="secondary" className="text-xs">
            {filtered.length} assets
          </Text>
          <Button
            type="primary"
            size="small"
            onClick={() => {
              setEditingAsset(null);
              setModalOpen(true);
            }}
          >
            + Add asset
          </Button>
        </Flex>
      </Flex>

      {/* Table */}
      <Flex vertical gap={0}>
        {/* Header */}
        <Flex
          className="border-b border-solid border-[#f0f0f0] px-3 py-2"
          style={{ backgroundColor: palette.FIDESUI_CORINTH }}
        >
          <Text strong className="w-[18%] text-[10px] uppercase tracking-wider">
            Name
          </Text>
          <Text strong className="w-[10%] text-[10px] uppercase tracking-wider">
            Type
          </Text>
          <Text strong className="w-[14%] text-[10px] uppercase tracking-wider">
            Domain
          </Text>
          <Text strong className="w-[16%] text-[10px] uppercase tracking-wider">
            Categories of Consent
          </Text>
          <Text strong className="w-[8%] text-[10px] uppercase tracking-wider">
            Duration
          </Text>
          <Text strong className="w-1/5 text-[10px] uppercase tracking-wider">
            Detected On
          </Text>
          <Text
            strong
            className="w-[14%] text-right text-[10px] uppercase tracking-wider"
          >
            Actions
          </Text>
        </Flex>

        {/* Rows */}
        {filtered.map((asset) => (
          <Flex
            key={asset.id}
            align="center"
            className="border-b border-solid border-[#f5f5f5] px-3 py-2"
          >
            <Text className="w-[18%] text-xs">{asset.name}</Text>
            <div className="w-[10%]">
              <Tag
                color={
                  (ASSET_TYPE_COLORS[asset.assetType] ?? "default") as
                    | "sandstone"
                    | "olive"
                    | "nectar"
                    | "minos"
                    | "default"
                }
                bordered={false}
                className="!text-[9px]"
              >
                {asset.assetType}
              </Tag>
            </div>
            <Text type="secondary" className="w-[14%] truncate text-xs">
              {asset.domain}
            </Text>
            <div className="w-[16%]">
              <Flex gap={3} wrap>
                {asset.dataUses.map((use) => (
                  <Tag
                    key={use}
                    bordered={false}
                    style={{ backgroundColor: palette.FIDESUI_NEUTRAL_100 }}
                    className="!text-[9px]"
                  >
                    {use}
                  </Tag>
                ))}
              </Flex>
            </div>
            <Text type="secondary" className="w-[8%] text-xs">
              {asset.duration ?? "—"}
            </Text>
            <div className="w-1/5">
              {asset.detectedOn && asset.detectedOn.length > 0 ? (
                <Text
                  type="secondary"
                  className="truncate text-[10px]"
                  title={asset.detectedOn.join(", ")}
                >
                  {asset.detectedOn.join(", ")}
                </Text>
              ) : (
                <Text type="secondary" className="text-[10px]">
                  —
                </Text>
              )}
            </div>
            <Flex className="w-[14%]" justify="flex-end" gap={6}>
              <Button
                size="small"
                type="default"
                className="!text-[10px]"
                onClick={() => {
                  setEditingAsset(asset);
                  setModalOpen(true);
                }}
              >
                Edit
              </Button>
              <Button
                size="small"
                type="default"
                danger
                className="!text-[10px]"
              >
                Delete
              </Button>
            </Flex>
          </Flex>
        ))}

        {filtered.length === 0 && (
          <Flex justify="center" className="py-8">
            <Text type="secondary" className="text-xs">
              No assets match the current filters
            </Text>
          </Flex>
        )}
      </Flex>

      {/* Add/Edit Modal */}
      <Modal
        title={editingAsset ? `Edit ${editingAsset.name}` : "Add asset"}
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={() => setModalOpen(false)}
        okText={editingAsset ? "Save" : "Add"}
        width={520}
      >
        <Flex vertical gap={16} className="mt-4">
          <div>
            <Text type="secondary" className="mb-1 block text-xs">
              Name
            </Text>
            <Input
              defaultValue={editingAsset?.name ?? ""}
              disabled={!!editingAsset}
            />
          </div>
          <div>
            <Text type="secondary" className="mb-1 block text-xs">
              Asset type
            </Text>
            <Select
              aria-label="Asset type"
              defaultValue={editingAsset?.assetType}
              className="w-full"
              options={ASSET_TYPE_OPTIONS}
              disabled={!!editingAsset}
            />
          </div>
          <div>
            <Text type="secondary" className="mb-1 block text-xs">
              Domain
            </Text>
            <Input
              defaultValue={editingAsset?.domain ?? ""}
              disabled={!!editingAsset}
            />
          </div>
          <div>
            <Text type="secondary" className="mb-1 block text-xs">
              Data uses
            </Text>
            <Select
              aria-label="Data uses"
              mode="multiple"
              defaultValue={editingAsset?.dataUses ?? []}
              className="w-full"
              options={[
                { label: "Functional", value: "functional" },
                { label: "Essential", value: "essential" },
                { label: "Analytics", value: "analytics" },
                { label: "Marketing", value: "marketing" },
                { label: "Third party sharing", value: "third_party_sharing" },
              ]}
            />
          </div>
          <div>
            <Text type="secondary" className="mb-1 block text-xs">
              Description
            </Text>
            <Input.TextArea
              rows={2}
              defaultValue={editingAsset?.description ?? ""}
            />
          </div>
          <div>
            <Text type="secondary" className="mb-1 block text-xs">
              Duration (cookies only)
            </Text>
            <Input
              defaultValue={editingAsset?.duration ?? ""}
              placeholder="e.g. 1 day, 30 minutes, 1 year"
            />
          </div>
          <div>
            <Text type="secondary" className="mb-1 block text-xs">
              Base URL (non-cookie assets)
            </Text>
            <Input
              defaultValue={editingAsset?.baseUrl ?? ""}
              placeholder="https://..."
            />
          </div>
        </Flex>
      </Modal>
    </Flex>
  );
};

export default AssetsTab;
