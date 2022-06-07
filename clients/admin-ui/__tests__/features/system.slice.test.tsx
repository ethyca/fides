import { AnyAction } from "@reduxjs/toolkit";

import { reducer, setSystems } from "~/features/system";
import { mockSystems } from "~/mocks/data";

const initialState = {
  systems: [],
};

describe("System slice", () => {
  it("should return the initial state", () => {
    expect(reducer(undefined, {} as AnyAction)).toEqual(initialState);
  });

  it("should handle a dataset being added", () => {
    const systems = mockSystems(1);
    expect(reducer(initialState, setSystems(systems))).toEqual({ systems });
  });
});
