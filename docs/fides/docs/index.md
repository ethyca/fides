# Fides

## Overview




  test("test policy rating") {
    val policy = PolicyGen.sample.get.copy(rules =
      Some(
        Seq(
          policyRuleOf(
            //category
            PolicyValueGrouping(ANY, Set("credentials")),
            //use
            PolicyValueGrouping(ALL, Set("provide")),
            //dataQualifier
            "identified_data",
            PolicyValueGrouping(NONE, Set()),
            REJECT
          )
        )
      )
    )

    val failingSystem = systemOf("_", Declaration(Set("credentials"), "provide", "identified_data", Set()))

    val passingSystem = systemOf("_", Declaration(Set("credentials"), "provide", "anonymized_data", Set()))

    val a: (Approval, Approval) = waitFor(for {
      pass <- systemService.dryRun(passingSystem, requestContext)
      fail <- systemService.dryRun(failingSystem, requestContext)
    } yield (pass, fail))

    val pass: Approval = a._1
    val fail: Approval = a._2

    // TODO approval stamps
//    pass.isSuccess shouldEqual true
//    pass.versionStamp.isDefined shouldEqual true
//    fail.isFailure shouldEqual true
//    fail.versionStamp.isDefined shouldEqual false

  }
