import { Alert, Button, Flex, Icons, Input } from "fidesui";

interface Props {
  value?: string[];
  onChange?: (next: string[]) => void;
}

export const PathsEditor = ({ value = [], onChange }: Props) => {
  const update = (index: number, val: string) => {
    const next = [...value];
    next[index] = val;
    onChange?.(next);
  };

  const remove = (index: number) =>
    onChange?.(value.filter((_, i) => i !== index));

  const add = () => onChange?.([...value, ""]);

  return (
    <Flex vertical gap={12}>
      {value.map((path, index) => (
        // eslint-disable-next-line react/no-array-index-key
        <Flex key={index} vertical gap={8}>
          {path === "/" && (
            <Alert
              type="warning"
              showIcon
              message={
                <>
                  <code>FIDES_PRIVACY_CENTER__USE_API_CONFIG</code> must be set
                  to <code>true</code> when serving the Privacy Center at the
                  root path (<code>/</code>). Update this variable to continue.
                </>
              }
            />
          )}
          <Flex gap={12} align="flex-end">
            <Input
              value={path}
              onChange={(e) => update(index, e.target.value)}
              placeholder="/path"
              data-testid={`path-input-${index}`}
            />
            <Button
              aria-label="Remove path"
              icon={<Icons.TrashCan />}
              onClick={() => remove(index)}
              data-testid={`remove-path-${index}`}
            />
          </Flex>
        </Flex>
      ))}
      <Button icon={<Icons.Add />} onClick={add} data-testid="add-path-button">
        Add path
      </Button>
    </Flex>
  );
};
