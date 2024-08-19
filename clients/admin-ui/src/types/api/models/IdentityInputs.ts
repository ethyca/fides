/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

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