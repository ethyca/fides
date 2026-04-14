import { Avatar, Flex, Input, Modal, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useMemo, useState } from "react";

import { getBrandIconUrl } from "~/features/common/utils";

import { MOCK_SYSTEMS } from "../../mock-data";

interface RelationshipPickerModalProps {
  open: boolean;
  onClose: () => void;
  role: "producer" | "consumer";
  systemFidesKey: string;
  existingKeys: Set<string>;
}

const RelationshipPickerModal = ({
  open,
  onClose,
  role,
  systemFidesKey,
  existingKeys,
}: RelationshipPickerModalProps) => {
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const available = useMemo(
    () =>
      MOCK_SYSTEMS.filter(
        (s) => s.fides_key !== systemFidesKey && !existingKeys.has(s.fides_key),
      ),
    [systemFidesKey, existingKeys],
  );

  const filtered = useMemo(() => {
    if (!search) {
      return available;
    }
    const q = search.toLowerCase();
    return available.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.system_type.toLowerCase().includes(q),
    );
  }, [available, search]);

  const toggleSystem = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const resetAndClose = () => {
    setSearch("");
    setSelected(new Set());
    onClose();
  };

  const handleOk = () => {
    // In production this would call an RTK mutation to persist the relationships.
    // For now we just close — the mock data is static.
    resetAndClose();
  };

  const roleLabel = role === "producer" ? "producer" : "consumer";

  return (
    <Modal
      title={`Add ${roleLabel}`}
      open={open}
      onCancel={resetAndClose}
      onOk={handleOk}
      okText={`Add ${selected.size || ""} ${roleLabel}${selected.size !== 1 ? "s" : ""}`}
      okButtonProps={{ disabled: selected.size === 0 }}
      width={560}
    >
      <Text type="secondary" className="mb-3 block text-xs">
        Select systems that{" "}
        {role === "producer" ? "produce data into" : "consume data from"} this
        system.
      </Text>
      <Input
        placeholder="Search systems..."
        value={search}
        onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
          setSearch(e.target.value)
        }
        allowClear
        size="small"
        className="mb-3"
      />
      <div className="max-h-[350px] overflow-y-auto">
        <Flex
          className="border-b border-solid px-3 py-1.5"
          style={{
            borderColor: palette.FIDESUI_NEUTRAL_100,
            backgroundColor: palette.FIDESUI_NEUTRAL_75,
          }}
        >
          <Text strong className="w-2/5 text-[10px] uppercase tracking-wider">
            System
          </Text>
          <Text strong className="w-[30%] text-[10px] uppercase tracking-wider">
            Type
          </Text>
          <Text
            strong
            className="w-[30%] text-right text-[10px] uppercase tracking-wider"
          >
            Department
          </Text>
        </Flex>
        {filtered.map((sys) => {
          const isSelected = selected.has(sys.fides_key);
          return (
            <Flex
              key={sys.fides_key}
              align="center"
              className="cursor-pointer border-b border-solid px-3 py-2"
              style={{
                borderColor: palette.FIDESUI_NEUTRAL_75,
                backgroundColor: isSelected
                  ? palette.FIDESUI_BG_DEFAULT
                  : undefined,
              }}
              onClick={() => toggleSystem(sys.fides_key)}
            >
              <Flex className="w-2/5" align="center" gap={8}>
                <Avatar
                  size={20}
                  shape="square"
                  src={
                    sys.logoDomain
                      ? getBrandIconUrl(sys.logoDomain, 40)
                      : undefined
                  }
                  style={
                    !sys.logoDomain
                      ? {
                          backgroundColor: palette.FIDESUI_NEUTRAL_100,
                          color: palette.FIDESUI_NEUTRAL_800,
                          fontSize: 8,
                        }
                      : undefined
                  }
                >
                  {!sys.logoDomain ? sys.name.slice(0, 2).toUpperCase() : null}
                </Avatar>
                <Text strong={isSelected} className="text-xs">
                  {sys.name}
                </Text>
              </Flex>
              <Text type="secondary" className="w-[30%] text-xs">
                {sys.system_type}
              </Text>
              <Flex className="w-[30%]" justify="flex-end" align="center">
                <Text type="secondary" className="text-xs">
                  {sys.department}
                </Text>
              </Flex>
            </Flex>
          );
        })}
        {filtered.length === 0 && (
          <Flex justify="center" className="py-6">
            <Text type="secondary" className="text-xs">
              No systems available
            </Text>
          </Flex>
        )}
      </div>
    </Modal>
  );
};

export default RelationshipPickerModal;
