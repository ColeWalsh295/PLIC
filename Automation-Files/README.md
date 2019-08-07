# PLIC Automation

Code used for automatically administering PLIC surveys at specified times by instructors in an online Qualtrics survey.

PythonAutomation.py --- main code that is run on a loop to handle the creation of new PLIC surveys and send emails with links and reminders to instructors. When all surveys have closed for a particular class, summary reports are created and emailed to instructors.

ReportGen.py --- pdf reports are created for an instructor's class compared to similar classes using pylatex.

ReportGraph.py --- figures that are used in the reports are generated.

Valid_Matched.py --- PLIC surveys are filtered so that only valid entries are kept. These are matched across pre-(mid)-post iterations by student.

Scoring.py --- Calculates scores for each student on each question on the PLIC as well as factor scores and total scores.