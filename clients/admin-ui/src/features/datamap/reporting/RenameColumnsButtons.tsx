import { AntButton as Button } from "fidesui";
import { useFormikContext } from "formik";

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
  const { submitForm, resetForm } = useFormikContext();
  return (
    <div className="flex gap-2">
      <Button
        size="small"
        data-testid="rename-columns-reset-btn"
        onClick={() => {
          setColumnNameMapOverrides({});
          setSavedCustomReportId("");
          resetForm({ values: {} });
          setIsRenamingColumns(false);
        }}
      >
        Reset all
      </Button>
      <Button
        size="small"
        data-testid="rename-columns-cancel-btn"
        onClick={() => {
          resetForm({ values: columnNameMapOverrides });
          setIsRenamingColumns(false);
        }}
      >
        Cancel
      </Button>
      <Button
        size="small"
        type="primary"
        htmlType="submit"
        data-testid="rename-columns-apply-btn"
        onClick={submitForm}
      >
        Apply
      </Button>
    </div>
  );
};
