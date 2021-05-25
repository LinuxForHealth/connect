## Contributing In General
Our project gladly welcomes external contributions. To contribute code or documentation, please submit a [pull request](https://github.com/LinuxForHealth/connect/pulls).

A good way to familiarize yourself with the codebase and contribution process is
to look for and tackle low-hanging fruit in the [issue tracker](https://github.com/LinuxForHealth/connect/issues).
Before embarking on a more ambitious contribution, please quickly [get in touch](#communication) with us.
Also, be sure to take a look at the [ZenHub](https://app.zenhub.com/workspaces/linux-for-health-5ee2d7cecec5920ec43ae1cb/board?repos=337464130,366144163) to get the full view of the issues and roadmap.

**Note: We appreciate your effort, and want to avoid a situation where a contribution
requires extensive rework (by you or by us), sits in backlog for a long time, or
cannot be accepted at all!**

### Proposing new features

If you would like to implement a new feature, please [raise an issue](https://github.com/LinuxForHealth/connect/issues)
before sending a pull request so the feature can be discussed. This is to avoid
you wasting your valuable time working on a feature that the project developers
are not interested in accepting into the code base.

### Fixing bugs

If you would like to fix a bug, please [raise an issue](https://github.com/LinuxForHealth/connect/issues) before sending a
pull request so it can be tracked.

### Merge approval

A pull request requires approval from at lesat two of the maintainers.

For a list of the maintainers, see the [MAINTAINERS.md](MAINTAINERS.md) page.

## Legal

Each source file must include a license header for the Apache
Software License 2.0. Using the SPDX format is the simplest approach.
e.g.

```
/*
 * (C) Copyright <holder> <year of first update>[, <year of last update>]
 *
 * SPDX-License-Identifier: Apache-2.0
 */
```

## Communication
To connect with us, please open an [issue](https://github.com/LinuxForHealth/connect/issues) or contact one of the maintainers via email. 
See the [MAINTAINERS.md](MAINTAINERS.md) page.

## Setup
LinuxForHealth is requires Java 1.8 or higher and Gradle 6.x.  

LinuxForHealth is currently built on:

    Apache Camel for integration, supported by one of the most active development communities.

    Kafka and NATS for world-class data streaming and messaging.

    Standard data formats, including HL7 FHIR R4, HL7 MLLP and EDI, with easy extensiblity to support any format.


Instructions for developer setup can be found [here](https://linuxforhealth.github.io/docs/developer-setup.html).


## Testing
To ensure a working build, please run the full build from the root of the project before submitting your pull request.

## Coding style guidelines
Formatting has not been strictly enforced, but we'd like to improve it over time, so please consider the following points as you change the code:

1. Write tests. Pull Requests should include necessary updates to unit tests (src/test/java of the corresponding project) and integration tests (in the fhir-server-test project)

2. Use comments. Preferably javadoc.

3. Keep the [documentation](https://github.com/LinuxForHealth/docs) up-to-date. Documentation updates require a pull request.

4. Use spaces (not tabs) in java source. For this we have a checkstyle rule which will fail the build if you're using tabs. We also prefer spaces over tabs in JSON and XML, but its not strictly enforced.

5. Use spaces after control flow keywords (they're not function calls!); if/for/while blocks should always have { }

Leave the code better than you found it.



LinuxForHealth is sublicensed by the Linux Foundation with Sublicense ID: 20200615-0008
