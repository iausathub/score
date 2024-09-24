# Guide to contributing to SCORE

Welcome to the SCORE contributing guide! SCORE is the satellite brightness/position observation repository developed by the IAU Centre for the Protection of the Dark and Quiet Sky from Satellite Constellation Interference (IAU CPS) SatHub group. Observation data submitted here can be used to study the effects of satellite constellations on astronomical observations.

Bug report/fixes, feature requests, and other contributions are welcome, and all issues and pull requests will be reviewed by a repo maintainer to ensure consistency with the project's scope and other guidelines.

For any questions not answered here please email sathub@cps.iau.org or open an issue. We are in the process of creating additional issues for the GitHub repo based off of known issues and changes to make, so that section is a work in progress.

## Getting Started
1. Fork and clone the repository ([instructions](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo))
2. Follow the local environment setup instructions in the README (https://github.com/iausathub/score)
3. Review the issues or propose a new feature.
4. Open a pull request when you're done - if this was for a new feature, only features approved by a project maintainer will be considered for merging into the project.

## Code Quality
* The project has Ruff and Black set up to run as part of pull requests and commits to branches in this repository, and info on the rules used for those can be found in the README [here](https://github.com/iausathub/score).

* Pytest is used for testing.

* Use Google-style docstrings -- example:
```
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together.

    Args:
        a (int): The first number.
        b (int): The second number.

    Returns:
        int: The sum of the two numbers.

    Raises:
        ValueError: If either `a` or `b` is not an integer.
    """
```

## Pull request guidelines
* Create a new pull request for each feature or bug fix.
* Add a clear title and description of the changes.
* Don't forget to include relevant tests or examples to demonstrate the changes, and make sure all existing tests still pass.
* Include a link to any relevant issues or discussions.


#### License Info
All code that is part of SCORE is currently released under the [BSD-3-Clause](https://opensource.org/licenses/BSD-3-Clause) license.
