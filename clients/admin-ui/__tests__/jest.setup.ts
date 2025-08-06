import "@testing-library/jest-dom";
import "whatwg-fetch";

// eslint-disable-next-line global-require
jest.mock("iso-3166", () => require("./utils/iso-3166-mock").iso3166Mock);
