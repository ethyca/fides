import { createParser } from "nuqs";
import * as Yup from "yup";

export const parseAsPositiveInteger = createParser({
  parse(queryValue) {
    const parsedValue = parseInt(queryValue, 10);
    try {
      Yup.number().integer().positive().validateSync(parsedValue);
      return parsedValue;
    } catch {
      return null;
    }
  },
  serialize(value) {
    return value.toString();
  },
});
