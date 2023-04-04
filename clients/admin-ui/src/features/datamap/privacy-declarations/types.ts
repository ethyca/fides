import { PrivacyDeclaration } from '~/types/api';

/**
 * This is because privacy declarations do not have an ID on the backend.
 * It is very useful for React rendering to have a stable ID. We currently
 * make this the composite of data_use - name, but even better may be to
 * give it a UUID (or to have the backend actually enforce this!)
 */
export interface PrivacyDeclarationWithId extends PrivacyDeclaration {
  id: string;
}
