# Getting Acquainted with the Fides Taxonomy 
_In this section, we'll review what the Fides taxonomy is, how it was created, when and how it should be used._

(todo link to taxonomy reference)

The Fides taxonomy for data categories is a standard adapted from [ISO 19944](https://www.iso.org/standard/79573.html). This taxonomy provides descriptions of the types of sensitive, personally identifiable, or non-identifiable data that an organization could hold for any data subject. The hierarchical nature of the Fides taxonomy has a few notable benefits:

* Consistency: the taxonomy is used as a shared resource across your Fidesctl deployment(s). Because the taxonomy is derived from an international standard, it enables interoperability inside and outside of your organization. 
* Natural inheritance: the hierarchy allows ease of reference to multiple subcategories or uncertain categorizations, simply by using a more superior data category.  
* Extensibility: if the taxonomy is missing any data categories specific to your business, you can extend the taxonomy with whatever new values you need. 

The Fides Taxonomy is used across the Fides ecosystem of projects, fidesctl and fidesops. 

## Why did we create the Fides Taxonomy?
The Fides taxonomy was created because the industry is distinctly lacking a common definition of what Personal Data is, what identifiable data is, and how anonymized data has to be to be unidentifiable. The taxonomy provides this common classification and is a key component of implementing Privacy as Code. 

## How to use the Fides Taxonomy
The Fides project comes with 4 taxonomies of privacy attributes by default:

* Data Categories
* Data Subjects
* Data Uses
* Data Qualifiers

Fidesctl comes loaded with these taxonomies by default and they can be found here `fidesctl/src/fideslang/default_taxonomy.py`. To extend this taxonomy for your business uses, you might want to add additional data categories to cover all the types of PII your business collects, or additional legal uses for the data. At Best Pizza Co, since we're expanding to new countries, we need to support Province, for example, as part of the user's provided address for delivery. We could accomplish this by adding the additional data category directly to `default_taxonomy.py`: 

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

This will add the `user.provided.identifiable.contact.province` as a data category type for your organization. You can add and remove any privacy attributes as you see fit for your organization.  For a more in-depth definition of these privacy attributes, please refer to [the Fides Resources documentation](../fides_resources.md). 
