import {
  AntButton as Button,
  Input,
  InputGroup,
  InputLeftElement,
  InputProps,
  InputRightElement,
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
    <InputGroup size="sm" minWidth="308px">
      {withIcon ? (
        <InputLeftElement pointerEvents="none">
          <SearchLineIcon color="gray.300" w="17px" h="17px" />
        </InputLeftElement>
      ) : null}
      <Input
        autoComplete="off"
        type="search"
        minWidth={200}
        size="sm"
        borderRadius="md"
        value={search}
        name="search"
        onChange={handleSearchChange}
        placeholder={placeholder || ""}
        {...props}
      />
      {onClear ? (
        <InputRightElement>
          <Button onClick={onClear} className="right-4 shrink-0 rounded-s-none">
            Clear
          </Button>
        </InputRightElement>
      ) : null}
    </InputGroup>
  );
};

export default SearchBar;
