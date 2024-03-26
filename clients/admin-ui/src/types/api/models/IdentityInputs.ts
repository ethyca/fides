/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * A base template for all other Fides Schemas to inherit from.
 */
export type IdentityInputs = {
  name?: IdentityInputs.name;
  email?: IdentityInputs.email;
  phone?: IdentityInputs.phone;
};

export namespace IdentityInputs {
  export enum name {
    OPTIONAL = "optional",
    REQUIRED = "required",
  }

  export enum email {
    OPTIONAL = "optional",
    REQUIRED = "required",
  }

  export enum phone {
    OPTIONAL = "optional",
    REQUIRED = "required",
  }
}
