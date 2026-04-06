import { Button, Form } from "fidesui";

interface RenameColumnsButtonsProps {
  columnNameMapOverrides: Record<string, string>;
  setColumnNameMapOverrides: (overrides: Record<string, string>) => void;
  setSavedCustomReportId: (id: string) => void;
  setIsRenamingColumns: (isRenaming: boolean) => void;
}
export const RenameColumnsButtons = ({
  columnNameMapOverrides,
  setColumnNameMapOverrides,
  setSavedCustomReportId,
  setIsRenamingColumns,
}: RenameColumnsButtonsProps) => {
  const form = Form.useFormInstance();
  return (
    <div className="flex gap-2">
      <Button
        size="small"
        data-testid="rename-columns-reset-btn"
        onClick={() => {
          setColumnNameMapOverrides({});
          setSavedCustomReportId("");
          form.resetFields();
          setIsRenamingColumns(false);
        }}
      >
        Reset all
      </Button>
      <Button
        size="small"
        data-testid="rename-columns-cancel-btn"
        onClick={() => {
          form.setFieldsValue(columnNameMapOverrides);
          setIsRenamingColumns(false);
        }}
      >
        Cancel
      </Button>
      <Button
        size="small"
        type="primary"
        data-testid="rename-columns-apply-btn"
        onClick={() => form.submit()}
      >
        Apply
      </Button>
    </div>
  );
};
