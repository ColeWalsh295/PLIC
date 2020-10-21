# Open-response analysis

These files were used to analyze open-response versions of the PLIC. `ML-open_response.ipynb` uses natural language processing and supervised machine learning to code students' written responses according to pre-defined codes used on the PLIC closed-response assessment.

`interrater_reliability.R` contains functions for computing interrater reliability between two coders when multiple non-mutually exclusive codes are used. In this situation, Cohen's Kappa and other common measures of interrater reliability are inappropriate. We use a *fuzzy kappa* measure of interrater reliability as discussed by [Kirilenko and Stepchenkova](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0149787). We compute interrater reliability in such a situation in `Compare-OR.Rmd` for two coders who independently coded 50 open-response PLIC surveys.
