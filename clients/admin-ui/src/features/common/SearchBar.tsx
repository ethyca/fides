import {
  AntButton as Button,
  AntInput as Input,
  AntInputProps as InputProps,
  AntSpace as Space,
  SearchLineIcon,
} from "fidesui";

interface Props extends Omit<InputProps, "onChange"> {
  search?: string;
  onChange: (value: string) => void;
  withIcon?: boolean;
  onClear?: () => void;
}
const SearchBar = ({
  search,
  onChange,
  withIcon,
  onClear,
  placeholder,
  ...props
}: Props) => {
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    onChange(event.target.value);

  return (
    <Space.Compact className="w-96">
      <Input
        autoComplete="off"
        value={search}
        onChange={handleSearchChange}
        placeholder={placeholder || "Search..."}
        prefix={withIcon ? <SearchLineIcon boxSize={4} /> : undefined}
        className="border-[#e6e6e8]"
        {...props}
      />
      {onClear ? (
        <Button
          onClick={onClear}
          className="border-[#e6e6e8] bg-[#f5f5f5] hover:!border-[#e6e6e8] hover:!bg-[#e6e6e8]"
        >
          Clear
        </Button>
      ) : null}
    </Space.Compact>
  );
};

export default SearchBar;
