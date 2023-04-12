import {
  Button,
  Input,
  InputGroup,
  InputLeftElement,
  InputProps,
  InputRightElement,
  SearchLineIcon,
} from "@fidesui/react";

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
        {...props}
      />
      {onClear ? (
        <InputRightElement>
          <Button
            borderLeftRadius={0}
            height="95%"
            right="14px"
            flexShrink={0}
            fontWeight="light"
            size="sm"
            onClick={onClear}
          >
            Clear
          </Button>
        </InputRightElement>
      ) : null}
    </InputGroup>
  );
};

export default SearchBar;
