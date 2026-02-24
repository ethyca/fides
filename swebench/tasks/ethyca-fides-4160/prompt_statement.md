I'm working on a consent management platform and need to make TCF (Transparency and Consent Framework) information more accessible to developers consuming our API. Right now, when developers fetch privacy experiences, they have to compute TC strings and mobile data themselves, which is error-prone and adds complexity to their implementations.

I'd like to add a way for the privacy experience endpoint to return pre-computed metadata when requested. This should include things like version hashes for cache validation, plus pre-built TC strings for both "accept all" and "reject all" scenarios. The mobile apps especially need formatted data they can use directly.

When TCF isn't enabled or there's no TCF content, these fields should just be empty so clients know there's nothing to display.

I also need to introduce proper validation for the consent model data. Things like the CMP ID and policy version should be validated as non-negative numbers, the publisher country code needs to be exactly 2 letters and uppercase, and legitimate interest purposes need to be filtered to only include the ones that are actually allowed under TCF rules. Same goes for vendor lists - they need to be filtered based on what the GVL allows.

Additionally, the TCF utility code has gotten unwieldy in a single file and should be reorganized into a proper subpackage structure to keep things maintainable.
