import {
  AntButton as Button,
  AntInput as Input,
  AntInputProps as InputProps,
  AntSpace as Space,
  SearchLineIcon,
} from "fidesui";

export interface SearchInputProps extends Omit<InputProps, "onChange"> {
  onChange: (value: string) => void;
  withIcon?: boolean;
  onClear?: () => void;
}

const SearchInput = ({
  onChange,
  withIcon,
  onClear,
  placeholder,
  ...props
}: SearchInputProps) => {
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    onChange(event.target.value);

  return (
    <Space.Compact className="w-96" data-testid="search-bar">
      <Input
        autoComplete="off"
        onChange={handleSearchChange}
        placeholder={placeholder || "Search..."}
        prefix={withIcon ? <SearchLineIcon boxSize={4} /> : undefined}
        {...props}
      />
      {onClear ? <Button onClick={onClear}>Clear</Button> : null}
    </Space.Compact>
  );
};

export default SearchInput;
