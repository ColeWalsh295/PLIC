# -*- coding: utf-8 -*-

import os
import pandas as pd
import pylatex.config as cf
from pylatex import Document, Package, Center, NewPage, Section, MiniPage, FootnoteText, Figure, Tabular, Table, NoEscape, Itemize
import ReportGraph

def Generate(fname, width, NumReportedStudents, Course_Level, ID, MainFolder, WeightsFile = 'Weights_May2019.csv', **Dataframes):
    """Generate a pdf report summarizing class performance on the PLIC

    Keyword arguments:
    fname -- filename to write report to as a pdf
    width -- width of file
    NumReportedStudents -- the number of students reported to be in the class
    Course_Level -- the level of the course students taking the surveyw were enrolled in
    ID -- ResponseID from course information survey
    MainDirectory -- path to main direcory with supplemental files for the report
    WeightsFile -- weights applied to PLIC item response choices during scoring
    Dataframes -- pandas dataframes of students responses to the PRE, MID, and/or POST survey
    """

    # Load the historical data
    CumulativePre = MainFolder + 'PreSurveys_ValMat.csv'
    CumulativePost = MainFolder + 'PostSurveys_ValMat.csv'
    Weightsdf = pd.read_csv(MainFolder + WeightsFile).transpose()[0]

    # Generate graphs for 1/2/3 class surveys in comparison to other classes
    if('PRE' in Dataframes.keys()):
        if('MID' in Dataframes.keys()):
            NumPreResponses, NumMidResponses, NumPostResponses, Predf, Middf, Postdf = ReportGraph.GenerateGraph(CumulativePre, CumulativePost, Course_Level, ID, Weightsdf, PRE = Dataframes['PRE'],
            MID = Dataframes['MID'], POST = Dataframes['POST'])
            Middf = Middf.fillna(0)
        else: # Set mid-survey to pre-survey
            NumPreResponses, NumPostResponses, Predf, Postdf = ReportGraph.GenerateGraph(CumulativePre, CumulativePost, Course_Level, ID, Weightsdf, PRE = Dataframes['PRE'], POST = Dataframes['POST'])
        Predf = Predf.fillna(0)
    else:
        NumPostResponses, Postdf = ReportGraph.GenerateGraph(CumulativePre, CumulativePost, Course_Level, ID, Weightsdf, POST = Dataframes['POST'])
    Postdf = Postdf.fillna(0)
    NumMatchedResponses = len(Postdf.index)

    cf.active = cf.Version1(indent = False) # Set the geometry for the .tex file
    geometry_options = {"right": "1.5cm", "left": "1.5cm", "top": "2.5cm", "bottom": "2.5cm"}
    doc = Document(fname, geometry_options = geometry_options) # Initialize the document
    doc.packages.append(Package('graphicx')) # Import packages necessary for building the .tex file
    doc.packages.append(Package('caption'))
    doc.packages.append(Package('multirow'))
    doc.packages.append(Package('makecell'))
    doc.packages.append(Package('subcaption'))
    doc.packages.append(Package('amsmath'))

    with doc.create(Section('Physics Lab Inventory of Critical thinking (PLIC)', numbering = False)):
        doc.append(NoEscape("""
                            Thank you for participating in the Physics Lab Inventory of Critical thinking (PLIC). We hope that you find this report useful in understanding
                            your students' critical thinking skills related to physics lab experiments. If you have any questions about the PLIC or this report, please do
                            not hesitate to contact us via email at: cperl@cornell.edu.\\

                            Sincerly,\\

                            The Cornell Physics Education Research Lab\\
                            """))

    with doc.create(Section("The PLIC Structure", numbering = False)):
        doc.append(NoEscape(r"""
                            The PLIC presents students with two case studies of groups conducting a mass-on-a-spring experiment to test the Hooke's Law model that: $T = 2\pi\sqrt{\frac{m}{k}}$.\\

                            Group 1 conducts 10 repeated trials for the period of oscillation for two different masses, uses the equation to find \textit{k} in each case, and compares the values.
                            Group 2 conducts two repeated trials for the period of oscillation for 10 different masses, plots $T^{2}$ versus $M$ and fits to a straight line with the intercept
                            fixed at the origin (1-parameter fit). They subsequently fit to a straight line with a free intercept (2-parameter fit). After Group 2 tries a 2-parameter fit, the
                            survey also asks which fit group 2 should use and why. At the end of the survey students are asked which group they think did a better job of testing the model and why.\\

                            The PLIC was designed to evaluate three critical thinking constructs that are important in physics experimentation: evaluating models, evaluating methods, and
                            suggesting follow-up actions. Each of these constructs was hypothesized to be represented by at least three questions (see Table~\ref{tab:Factors}):
                            the \textit{evaluating models} scale by questions Q1B, Q2B, Q3B, and Q3D; the \textit{evaluating methods} scale by questions Q1D, Q2D, and Q4B; and the
                            \textit{suggesting follow-ups} scale by questions Q1E, Q2E, and Q3E.\\

                            \begin{table*}[!htbp]
                                \caption{Multiple response questions from the PLIC with their hypothesized factor structures. The number in the question code corresponds to which page the question
                                            was asked on.}
                                \small
                                \begin{tabular}{c c l}
                                    \textbf{Hypothesized} & \textbf{Question} & \multirow{2}{*}{\textbf{Question Text}}\\
                                    \textbf{Factor} & \textbf{Code} &\\
                                    \hline
                                    & Q1B & What features were most important in comparing the two $k$-values?\\
                                    \multirowcell{2}{Evaluating\\Models} & Q2B & What features were most important in comparing the fit to the data?\\
                                    & Q3B & What features were most important in comparing the fit to the data? (after changing intercept)\\
                                    & Q3D & Which items reflect your reasoning for determining which fit you think Group 2 should use?\\
                                    \hline
                                    \multirowcell{3}{Evaluating\\Methods} & Q1D & What features of Group 1's method were most important for evaluating the method?\\
                                    & Q2D & What features of Group 2's method were most important for evaluating the method?\\
                                    & Q4B & What features were most important for comparing the two groups?\\
                                    \hline
                                    \multirowcell{3}{Suggesting\\Follow-ups} & Q1E & What do you think Group 1 should do next?\\
                                    & Q2E & What do you think Group 2 should do next?\\
                                    & Q3E & What do you think Group 2 should do next? (after changing intercept)\\
                                \end{tabular}
                                \label{tab:Factors}
                            \end{table*}
                            """))

    with doc.create(Section("Scoring the PLIC", numbering = False)):
        doc.append(NoEscape(r"""
                            The assessment uses a multiple response format where students may select up to three response choices from a pool of 6-17. The scoring scheme was developed through
                            evaluations of 78 responses to the PLIC from expert physicists (faculty, research scientists, instructors, and post-docs). We assign values to each response choice
                            equal to the fraction of experts who selected the response (rounded to the nearest tenth). A student's score on a question is equal to the sum of the values of
                            response choices selected divided by the maximum score a student could have obtained by selecting the same number of response choices. This is summarized in
                            Eq.~\ref{eq:Scoring}:
                            \begin{equation}\label{eq:Scoring}
                                Score = \frac{\sum_{n = 1}^{i} V_{n}}{V_{max_{i}}},
                            \end{equation}
                            where $V_{n}$ is the value of the $n^{th}$ response choice selected and $V_{max_{i}}$ is the maximum attainable score when $i$ response choices are selected. Explicitly,
                            the values of $V_{max_{i}}$ are:
                            \begin{equation}
                                \begin{split}
                                    V_{max_{1}} &= \text{Highest Value},\\
                                    V_{max_{2}} &= (\text{Highest Value}) + (\text{Second Highest Value}),\\
                                    V_{max_{3}} &= (\text{Highest Value}) + (\text{Second Highest Value})\\
                                    &+ (\text{Third Highest Value}).
                                \end{split}
                            \end{equation}
                            """))

    with doc.create(Section("Identifying Valid Responses", numbering = False)):
        doc.append(NoEscape(r"""
                            Only students' responses that pass the following basic filters are considered valid and included in the analysis that follows:
                            \begin{enumerate}
                                \item{The student must consent to take part in the study}
                                \item{The student must indicate that they are 18 years of age or older}
                                \item{The student must click through the entire survey and submit it}
                                \item{The student must spend at least 30s on at least one page of the survey (i.e., Q1, Q2, Q3, or Q4)}
                            \end{enumerate}
                            """))

    doc.append(NewPage())
    with doc.create(Section("Overall Statistics", numbering = False)):
        with doc.create(Table(position = '!htbp')) as Tab:
            with doc.create(MiniPage(width = NoEscape(r'0.5\linewidth'), pos = 'c', align = 'l')):
                doc.append(NoEscape(r"""
                                    Table~\ref{tab:Participation} summarizes the participation rates in your class. Figure~\ref{fig:Factors} displays the performance of your students on
                                    each of the latent critical constructs measured by the PLIC (see Table~\ref{tab:Factors}) calculated using Thurstone's regression method, as well as
                                    your students' total scores, found by summing scores on individual questions. Additionally, Fig.~\ref{fig:Factors} shows the performance of students
                                    from similar classes that have taken the PLIC for comparison purposes.
                                    """))
            try: # for when instructors do not enter a number in the 'number of students' field on the CIS
                NumReportedStudents = float(NumReportedStudents)
            except:
                NumReportedStudents = NumPostResponses
            with doc.create(MiniPage(width = NoEscape(r'0.5\linewidth'), pos = 'c', align = 'r')):
                    with doc.create(Center()) as centered:
                        with doc.create(Tabular('| l | r |')) as Tab1:
                            Tab1.add_hline()
                            Tab1.add_row(("Reported Number of students in class", NumReportedStudents))
                            if('PRE' in Dataframes.keys()):
                                Tab1.add_row(("Number of valid PRE-responses", NumPreResponses))
                            if('MID' in Dataframes.keys()):
                                Tab1.add_row(("Number of valid MID-responses", NumMidResponses))
                            Tab1.add_row(("Number of valid POST-responses", NumPostResponses))
                            if(len(Dataframes.keys()) >= 2):
                                Tab1.add_row(("Number of matched responses", NumMatchedResponses))
                                Tab1.add_row(("Estimated Fraction of class participating", round(NumMatchedResponses/float(NumReportedStudents), 2)))
                            else:
                                Tab1.add_row(("Estimated Fraction of class participating", round(NumPostResponses/float(NumReportedStudents), 2)))
                            Tab1.add_hline()
                        doc.append(NoEscape(r"\caption{Summary of class participation\label{tab:Participation}}"))
        doc.append(NoEscape(r"""
                            \begin{figure}[!htbp]
                            \centering
                            \includegraphics[width = \linewidth]{FactorsLevel.png}
                            \caption{Factor scores and total scores for your students and students enrolled in similar classes who have taken the PLIC. The whiskers represent the range of
                            student scores, while the lower and upper quartiles enclose the box. The median score is marked with a horizontal line inside the box and outliers, calulated
                            to be beyond 1.5 x Inter-Quartile Range (IQR) of either of the quartiles, are marked.\label{fig:Factors}}
                            \end{figure}
                            """))

    doc.append(NewPage())
    with doc.create(Section("Performance on individual questions", numbering = False)):
        doc.append(NoEscape(r"""
                            In Fig.~\ref{fig:Questions} you will see a summary of your students' performance on individual questions compared to students enrolled in similar classes who have
                            taken the PLIC.
                            \begin{figure}[!htbp]
                            \centering
                            \includegraphics[width = \linewidth]{QuestionsLevel.png}
                            \caption{Your students' performance on individual questions on the PLIC compared to students enrolled in similar classes who have taken the PLIC. The whiskers
                            represent the range of student scores, while the lower and upper quartiles enclose the box. The median score is marked with a horizontal line inside the box and
                            outliers, calulated to be beyond 1.5 x Inter-Quartile Range (IQR) of either of the quartiles, are marked.\label{fig:Questions}}
                            \end{figure}
                            """))

    doc.append(NewPage())
    with doc.create(Section("Your students' selected response choices", numbering = False)):
        doc.append(NoEscape(r"""
                            In Table~\ref{tab:Responses} you will find the most popular response choices selected by your students as well as the value of each response choice,
                            which also denotes the fraction of experts that selected this response choice.
                            """))

        Questions = ['Q1b', 'Q1d', 'Q1e', 'Q2b', 'Q2d', 'Q2e', 'Q3b', 'Q3d', 'Q3e', 'Q4b']
        StatementsSeries = pd.read_csv(MainFolder + 'Questions.csv', header = None, index_col = 0, squeeze = True)

        with doc.create(Center()) as centered:
            with doc.create(Table(position = 'h!')) as Tab:
                if(('PRE' in Dataframes.keys()) or ('MID' in Dataframes.keys())):
                    with doc.create(Tabular('c l c l c')) as Tab1:
                        Tab1.add_row((FootnoteText("Question"), FootnoteText("Pre-Survey"), FootnoteText('Value'), FootnoteText("Post-Survey"), FootnoteText('Value')))
                        Tab1.add_hline()
                        for Question in Questions:
                            Qcols = [col for col in StatementsSeries.index if Question in col]

                            PreFreq = Predf.loc[:, Qcols].mean(axis = 0).apply(lambda x: x * 100).round(0).nlargest(3)
                            PostFreq = Postdf.loc[:, Qcols].mean(axis = 0).apply(lambda x: x * 100).round(0).nlargest(3)
                            for KeyIndex, (PostKey, PostValue) in enumerate(PostFreq.items()):
                                Left_str = Question if KeyIndex == 1 else ''
                                Tab1.add_row((Left_str, FootnoteText(StatementsSeries[PreFreq.keys()[KeyIndex]]) + FootnoteText(' (' + str(int(PreFreq.tolist()[KeyIndex])) + '%)'),
                                                FootnoteText(Weightsdf[PreFreq.keys()[KeyIndex]]), FootnoteText(StatementsSeries[PostKey]) + FootnoteText(' (' + str(int(PostValue)) + '%)'),
                                                FootnoteText(Weightsdf[PostKey])))

                            Tab1.add_hline()
                else:
                    with doc.create(Tabular('c l c')) as Tab1:
                        Tab1.add_row((FootnoteText("Question"), FootnoteText("Post-Survey"), FootnoteText('Value')))
                        Tab1.add_hline()
                        for Question in Questions:
                            Qcols = [col for col in StatementsSeries.index if Question in col]
                            PostFreq = Postdf.loc[:, Qcols].mean(axis = 0).apply(lambda x: x * 100).round(0).nlargest(3)
                            for KeyIndex, (PostKey, PostValue) in enumerate(PostFreq.items()):
                                Left_str = Question if KeyIndex == 1 else ''
                                Tab1.add_row((Left_str, FootnoteText(StatementsSeries[PostKey]) + FootnoteText(' (' + str(int(PostValue)) + '%)'), FootnoteText(Weightsdf[PostKey])))

                            Tab1.add_hline()

                Tab.add_caption(NoEscape(r"""
                                        Most popular response choices selected by your students. The fraction of students that picked each option is included as well as the value of each
                                        response choice (equal to the fraction of 78 experts who selected the response choice)\label{tab:Responses}.
                                        """))

    with doc.create(Section("Acknowledgements", numbering = False)):
        doc.append(NoEscape(r"""We would like to acknowledge that the code for generating this report were based on the work by Wilcox et al.:
                            \begin{itemize}
                                \item{Wilcox, B. R., Zwickl, B. M., Hobbs, R. D., Aiken, J. M., Welch, N. M., \& Lewandowski, H. J. (2016). Alternative model for administration and analysis of
                                        research-based assessments. Physical Review Physics Education Research, 12(1), 010139.}
                            \end{itemize}
                            For more information about the PLIC see: cperl.lassp.cornell.edu/PLIC \textbf{or} physport.org/assessments/PLIC.
                            """))

    doc.generate_pdf(clean_tex = True)
    os.remove("FactorsLevel.png")
    os.remove("QuestionsLevel.png")

    return
