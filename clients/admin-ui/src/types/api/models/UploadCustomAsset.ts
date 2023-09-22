import { CustomAssetType } from "./CustomAssetType";

export type UploadCustomAsset = {
  assetType: CustomAssetType;
  file: File;
};
