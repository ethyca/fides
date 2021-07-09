package devtools.domain

import devtools.App
import devtools.Generators.DataCategoryGen
import devtools.util.FidesYamlProtocols
import faker._

class DataCategoryTest
  extends devtools.domain.DomainObjectTestBase[DataCategory, Long](
    App.dataCategoryService,
    DataCategoryGen,
    FidesYamlProtocols.DataCategoryFormat
  ) {

  override def editValue(t: DataCategory): DataCategory = t.copy(name = Some(Name.name))

}
