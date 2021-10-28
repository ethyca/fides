# Understanding the Fides Taxonomy
_In this section, we'll review what the Fides taxonomy is, how it was created, when and how it should be used._

(TODO: link to taxonomy reference)

The Fides taxonomy for data categories is a standard adapted from [ISO 19944](https://www.iso.org/standard/79573.html). This taxonomy provides descriptions of the types of sensitive, personally identifiable, or non-identifiable data that an organization could hold for any data subject. The hierarchical nature of the Fides taxonomy has a few notable benefits:

* Consistency: the taxonomy is used as a shared resource across your Fidesctl deployment(s). Because the taxonomy is derived from an international standard, it enables interoperability inside and outside of your organization.
* Natural inheritance: the hierarchy allows ease of reference to multiple subcategories or uncertain categorizations, simply by using a more superior data category.
* Extensibility: if the taxonomy is missing any data categories specific to your business, you can extend the taxonomy with whatever new values you need.

The Fides Taxonomy is used across the Fides ecosystem of projects, fidesctl and fidesops.

## Why did we create the Fides Taxonomy?
The Fides taxonomy was created because the industry lacks common definitions of personal data and identifiable data, and the notion that anonymized data must be unidentifiable. The taxonomy provides these common classifications, and is a key component of implementing Privacy as Code.

## How to use the Fides Taxonomy
The Fides project includes four taxonomies of privacy attributes:

* Data Categories
* Data Subjects
* Data Uses
* Data Qualifiers

Fidesctl comes loaded with these taxonomies by default, and they can be found [here](https://github.com/ethyca/fides/blob/318f243e576f1a493d36612b249f5c4e7a35286f/fidesctl/src/fideslang/default_taxonomy.py). To extend this taxonomy for your business uses, you might want to add additional data categories to cover all the types of PII your business collects, or additional legal uses for the data. At Best Pizza Co, since we're expanding to new countries, we need to support Province as a part of the user-provided delivery address. We can accomplish this by adding the additional data category directly to `default_taxonomy.py`:

(TODO: update this example to apply a Data Category resource file instead of editing source)

   ```diff
   +   DataCategory(
   +       fides_key="user.provided.identifiable.contact.province",
   +       organization_fides_key="default_organization",
   +       name="User Provided Province",
   +       description="User's province.",
   +       parent_key="user.provided.identifiable.contact",
   +   ),
        DataCategory(
            fides_key="user.provided.identifiable.contact.state",
            organization_fides_key="default_organization",
            name="User Provided State",
            description="User's state level address data.",
            parent_key="user.provided.identifiable.contact",
        ),
   ```

This will add the `user.provided.identifiable.contact.province` as a data category type, and a subcategory of `user.provided.identifiable.contact` for your organization. You can add and remove as many privacy attributes as necessary for your organization. For a more in-depth definition of these privacy attributes, see [the Fides Resources documentation](../language/resources.md).

## Next: Datasets
Let's start using the taxonomy to write some Fides declarations! We'll build up from the data layer, with [Datasets](dataset.md).
