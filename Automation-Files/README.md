# Automation files

The scripts included here are part of the automated administration system used to administer the PLIC.

`PythonAutomation.py` includes the main administration code and functions that communicate with the Qualtrics survey platform, adapted from [Wilcox *et al.*](https://journals.aps.org/prper/abstract/10.1103/PhysRevPhysEducRes.12.010139). `PythonAutomation_v2.py` is a new version of the administration system that builds on version 1 by improving readability, reducing the amount of code, and increasing the efficiency of the system. We are currently testing version 2 and anticipate deploying this version in the near future.

`ReportGen.py` includes functions that leverage `pylatex` to generate summary reports of student performance on the PLIC. These functions are called by `PythonAutomation.py` as part of the administration system, but can be called independently to generate reports for any PLIC dataset.

`ReportGraph.py` includes functions that score students' responses to the PLIC and generate summary box plots of students' scores along various dimensions. These functions are called by `ReportGen_BIOMAPS.py` as part of the administration system, but can be called independently to generate graphs for any PLIC dataset.

`Scoring.py` includes functions to score each of the PLIC questions and sum students' scores to produce an aggregate score. `Scoring.py` also leverages `rpy2` to conduct a confirmatory factor analysis on students' responses and produce factor scores along each of the dimensions the PLIC was designed to measure: students' abilities to evaluate models, evaluate methods, and suggest next steps in an experimental physics context.

`Valid_Matched.py` provides functions for filtering out invalid PLIC surveys from a dataset, as well as functions that match students' responses at up to three timepoints.
