# -*- coding: utf-8 -*-

import os
import pandas as pd
import pylatex.config as cf
from pylatex import Document, Package, Center, NewPage, Section, MiniPage, FootnoteText, Figure, Tabular, Table, NoEscape, Itemize
import ReportGraph

def Generate(fname, width, NumReportedStudents, Course_Level, Where = 'Local', **Surveys):

    NumSurveys = len(Surveys)
    PRE_Truth = False
    MID_Truth = False
    for key, value in Surveys.items():
        if(key == 'PRE'):
            PRE_Truth = True
            PreFile = value
        elif(key == 'MID'):
            MID_Truth = True
            MidFile = value
        else:
            PostFile = value

    if(Where == 'Local'):
        CumulativePre = 'C:/Users/Cole/Documents/GRA_Summer2018/PLIC_Reports/PreSurveys_ValMat.csv'
        CumulativePost = 'C:/Users/Cole/Documents/GRA_Summer2018/PLIC_Reports/PostSurveys_ValMat.csv'
    else:
        CumulativePre = 'C:/PLIC/PreSurveys_ValMat.csv'
        CumulativePost = 'C:/PLIC/PostSurveys_ValMat.csv'

    if(PRE_Truth and MID_Truth):
        NumPreResponses, NumMidResponses, NumPostResponses, Predf, Middf, Postdf = ReportGraph.GenerateGraph3(PreFile, MidFile, PostFile, CumulativePre, CumulativePost, Course_Level, Where = Where)
    elif(PRE_Truth and not MID_Truth):
        NumPreResponses, NumPostResponses, Predf, Postdf = ReportGraph.GenerateGraph2(CumulativePre, CumulativePost, Course_Level, Where = Where, PRE = PreFile, POST = PostFile)
    elif(not PRE_Truth and MID_Truth):
        NumMidResponses, NumPostResponses, Middf, Postdf = ReportGraph.GenerateGraph2(CumulativePre, CumulativePost, Course_Level, Where = Where, MID = MidFile, POST = PostFile)
    else:
        NumPostResponses, Postdf = ReportGraph.GenerateGraph1(PostFile, CumulativePre, CumulativePost, Course_Level, Where = Where)

    cf.active = cf.Version1(indent = False)
    geometry_options = {"right": "1.5cm", "left": "1.5cm", "top": "2.5cm", "bottom": "2.5cm"}
    doc = Document(fname, geometry_options = geometry_options)
    doc.packages.append(Package('graphicx'))
    doc.packages.append(Package('caption'))

    if PRE_Truth:
        Predf = Predf.fillna(0)
    if MID_Truth:
        Middf = Middf.fillna(0)
    Postdf = Postdf.fillna(0)

    NumMatchedResponses = len(Postdf.index)

    with doc.create(Section('Physics Lab Inventory of Critical thinking (PLIC)', numbering = False)):
        doc.append(NoEscape("""
                            Thank you for participating in the Physics Lab Inventory of Critical thinking (PLIC). We hope that you find this report useful in understanding
                            your students' critical thinking skills related to physics lab experiments. If you have any questions about the PLIC or this report, please do
                            not hesitate to contact us via email at: cperl@cornell.edu.

                            Sincerly,

                            The Cornell Physics Education Research Lab
                            """))

    with doc.create(Section("The PLIC Structure", numbering = False)):
        doc.append(NoEscape(r"The PLIC presents students with two case studies of groups conducting a mass-on-a-spring experiment to test the Hooke's Law model that: $T = 2\pi\sqrt{\frac{m}{k}}$.\\\\"))

        doc.append(NoEscape(r"Group 1 conducts 10 repeated trials for the period of oscillation for two different masses, uses the equation to find \textit{k} in each case, and compares the values. Group 2 conducts two repeated trials \
        for the period of oscillation for 10 different masses, plots $T^{2}$ versus $M$ and fits to a straight line with the intercept fixed at the origin (1-parameter fit). They subsequently fit to a straight line with a free intercept \
        (2-parameter fit).\\\\"))
        doc.append("The survey asks a series of questions in each case that generally follow the format:\n\n")
        doc.append("A) How well do the data agree (with each other (Group 1) or with the line (Group 2))?\n")
        doc.append("B) What is your reasoning?\n")
        doc.append("C) How well did the group's method test the model?\n")
        doc.append("D) What is your reasoning?\n")
        doc.append("E) What should the group do next?\n\n")
        doc.append(NoEscape(r"After Group 2 tries a 2-parameter fit, the survey also asks which fit group 2 should use and why. At the end of the survey students are asked which group they think did a better job of testing the model \
        and why.\\\\"))
        doc.append(NoEscape(r"Our analysis focuses on the \textit{Reasoning} questions (of the format B, D, and E as well as the summary question concerning which group did a better job). That is, we do not score based on which group \
        they think did better or how well they think the groups tested the model, just which ideas they used to make their decisions. There are anywhere from 5-10 options per \textit{Reasoning} question, and students are limited to \
        selecting no more than three of the options. Responses from experts have identified 1-2 options per question as `consensus expert-reponses' (E). A further 1-2 options have been identified as `partial-expert responses' (P) and \
        another 2-3 responses have been identified as being particularly `novice' (N). Students are scored on each question in the following way:\\\\"))
        doc.append(NoEscape(r"1. Students receive 1 point if they select \textbf{at least one} \textit{E} response.\\"))
        doc.append(NoEscape(r"2. If the student selects \textbf{0} \textit{E} responses, they will receive 0.5 points if they select \textbf{at least one} \textit{P} response.\\"))
        doc.append(NoEscape(r"3. If a student selects \textbf{at least one} \textit{N} response, they will have 0.25 points deducted from their score.\\"))
        doc.append(NoEscape(r"4. A student can score no lower than \textbf{0} on a particular question."))

    with doc.create(Section("Identifying Valid Responses", numbering = False)):
        doc.append(NoEscape("""
                            Only students' responses that pass the following basic filters are considered valid and included in the analysis that follows:\n
                            1. The student must consent to take part in the study\n
                            2. The student must indicate that they are 18 years of age or older\n
                            3. The student must click through the entire survey and submit it\n
                            """))
    doc.append(NewPage())
    with doc.create(Section("About this Report and Overall Statistics", numbering = False)):
        with doc.create(Table(position = 'h!')) as Tab:
            with doc.create(MiniPage(width = NoEscape(r'0.5\linewidth'), pos = 'b', align = 'l')):
                doc.append("Table 1 below summarizes the overall results for your class, while Figure 1 to the right gives the overall performance of students in your class along with those in similar classes. The total score is out of 10 \
                possible points (1 point for each question) and a higher score indicates more expert-like performance on the assessment.\n\n")
                with doc.create(Center()) as centered:
                    with doc.create(Tabular('| l | r |')) as Tab1:
                        Tab1.add_hline()
                        if PRE_Truth:
                            Tab1.add_row(("Number of valid PRE-responses", NumPreResponses))
                        if MID_Truth:
                            Tab1.add_row(("Number of valid MID-responses", NumMidResponses))
                        Tab1.add_row(("Number of valid POST-responses", NumPostResponses))
                        if(not ((not PRE_Truth) and (not MID_Truth))):
                            Tab1.add_row(("Number of matched responses", NumMatchedResponses))
                        Tab1.add_row(("Reported Number of students in class", NumReportedStudents))
                        if(~((not PRE_Truth) and (not MID_Truth))):
                            Tab1.add_row(("Estimated Fraction of class participating", round(NumMatchedResponses/float(NumReportedStudents), 2)))
                        else:
                            Tab1.add_row(("Estimated Fraction of class participating", round(NumPostResponses/float(NumReportedStudents), 2)))
                        Tab1.add_hline()
                    doc.append(NoEscape(r"\caption{Summary of class participation}"))
            with doc.create(MiniPage(width = NoEscape(r'0.5\linewidth'), pos = 'b', align = 'r')):
                    with doc.create(Center()) as centered:
                        if Where == 'Automation':
                            doc.append(NoEscape(r"\includegraphics[width = 0.95\linewidth]{C:/PLIC/TotalScores.png}"))
                        else:
                            doc.append(NoEscape(r"\includegraphics[width = 0.95\linewidth]{C:/Users/Cole/Documents/GRA_Summer2018/PLIC_Reports/TotalScores.png}"))
                        doc.append(NoEscape(r"\captionof{figure}{Box plots of students' overall scores on the PLIC. The whiskers represent the range of student scores, while the lower and upper quartiles enclose the box. The median score is marked \
                        with a horizontal line inside the box and outliers, calulated to be beyond 1.5 x Inter-Quartile Range (IQR) of either of the quartiles, are marked.}"))

        if(PRE_Truth and MID_Truth):
            doc.append(NoEscape(r"On page 3 you will see a summary of your students’ responses on the \textit{Reasoning} questions (Figure 3). A sample question is illustrated in Figure 2. The full length bars represent the \textbf{fraction} of \
                                students achieving each possible score (1, 0.75, 0.5, 0.25, 0) on a given question. The PRE-survey results are displayed above the MID- and POST-survey results. The left-hand-side presents the results of your class. The right-hand-side presents \
                                the results of other classes similar to yours, matched based on instructors’ responses to the instructor survey. Above these bars is an arrow representing the shift in \textbf{average} score on a given question from PRE- to POST-survey. \
                                The shaded region around the starting point of the arrow is indicative of the 95\% confidence interval for the PRE-survey average. Thus, a POST-survey average lying outside of this region can be interpreted as a statistically significant \
                                shift."))
        elif(PRE_Truth and (not MID_Truth)):
            doc.append(NoEscape(r"On page 3 you will see a summary of your students’ responses on the \textit{Reasoning} questions (Figure 3). A sample question is illustrated in Figure 2. The full length bars represent the \textbf{fraction} of \
                                students achieving each possible score (1, 0.75, 0.5, 0.25, 0) on a given question. The PRE-survey results are displayed above the POST-survey results. The left-hand-side presents the results of your class. The right-hand-side presents \
                                the results of other classes similar to yours, matched based on instructors’ responses to the instructor survey. Above these bars is an arrow representing the shift in \textbf{average} score on a given question from PRE- to POST-survey. \
                                The shaded region around the starting point of the arrow is indicative of the 95\% confidence interval for the PRE-survey average. Thus, a POST-survey average lying outside of this region can be interpreted as a statistically significant \
                                shift."))
        elif((not PRE_Truth) and MID_Truth):
            doc.append(NoEscape(r"On page 3 you will see a summary of your students’ responses on the \textit{Reasoning} questions (Figure 3). A sample question is illustrated in Figure 2. The full length bars represent the \textbf{fraction} of \
                                students achieving each possible score (1, 0.75, 0.5, 0.25, 0) on a given question. The PRE-survey results are displayed above the POST-survey results. The left-hand-side presents the results of your class. The right-hand-side presents \
                                the results of other classes similar to yours, matched based on instructors’ responses to the instructor survey. Above these bars is an arrow representing the shift in \textbf{average} score on a given question from PRE- to POST-survey. \
                                The shaded region around the starting point of the arrow is indicative of the 95\% confidence interval for the PRE-survey average. Thus, a POST-survey average lying outside of this region can be interpreted as a statistically significant \
                                shift. \textbf{Note that the PRE-survey data displayed for your class was given as a mid-survey.}"))
        else:
            doc.append(NoEscape(r"On page 3 you will see a summary of your students’ responses on the \textit{Reasoning} questions (Figure 3). A sample question is illustrated in Figure 2. The full length bars represent the \textbf{fraction} of \
                                students achieving each possible score (1, 0.75, 0.5, 0.25, 0) on a given question. The PRE-survey results are displayed above the POST-survey results. The left-hand-side presents the results of your class. The right-hand-side presents \
                                the results of other classes similar to yours, matched based on instructors’ responses to the instructor survey. Above these bars is an arrow representing the shift in \textbf{average} score on a given question from PRE- to POST-survey. \
                                The shaded region around the starting point of the arrow is indicative of the 95\% confidence interval for the PRE-survey average. Thus, a POST-survey average lying outside of this region can be interpreted as a statistically significant \
                                shift. \textbf{For your class, with only a post-survey, you will only see one bar and a single point representing the average score on this survey.}"))

        with doc.create(Center()) as centered:
            if Where == 'Automation':
                doc.append(NoEscape(r"\includegraphics[width = 0.45\linewidth]{C:/PLIC/Sample_Question.png}"))
            else:
                doc.append(NoEscape(r"\includegraphics[width = 0.45\linewidth]{C:/Users/Cole/Documents/GRA_Summer2018/PLIC_Reports/Sample_Question.png}"))
            doc.append(NoEscape(r"\captionof{figure}{Sample report of results from one question on the PLIC. The full length bars report the \textbf{fraction} of students who score in each category, while the arrows show shifts \
            in \textbf{average} score on a given question. The shaded region around the PRE-survey average is the 95\% confidence interval for this average.}"))

        doc.append(NoEscape(r"On Page 4 you will find information about the most selected options for each \textit{Reasoning} question by your class. The expert (E), partial-expert (P), and novice (N) responses are indicated."))

    doc.append(NewPage())
    with doc.create(Section("Your students' expert-like thinking compared to similar classes", numbering = False)):
        with doc.create(Center()) as centered:
            if Where == 'Automation':
                doc.append(NoEscape(r"\includegraphics[width = \linewidth]{C:/PLIC/Matched_PrePost.png}"))
            else:
                doc.append(NoEscape(r"\includegraphics[width = \linewidth]{C:/Users/Cole/Documents/GRA_Summer2018/PLIC_Reports/Matched_PrePost.png}"))
            if(PRE_Truth and MID_Truth):
                doc.append(NoEscape(r"\captionof{figure}{Pre/Mid/Post changes in expert-like views expressed by students in your class (left) compared to students in other classes (right). The full length bars represent the fraction of students scoring \
                                    in each particular category with the darker shades representing higher scores. Above these bars is an arrow representing the change in average score on a question from PRE- to POST-survey. The shaded region around the average \
                                    PRE-survey score represents the 95\% confidence interval. An arrow pointing to the right or an increase in the length of darker bars are both indicative of positive shifts from PRE- to POST-survey.}"))
            elif(PRE_Truth and (not MID_Truth)):
                doc.append(NoEscape(r"\captionof{figure}{Pre/Post changes in expert-like views expressed by students in your class (left) compared to students in other classes (right). The full length bars represent the fraction of students scoring \
                                    in each particular category with the darker shades representing higher scores. Above these bars is an arrow representing the change in average score on a question from PRE- to POST-survey. The shaded region around the average \
                                    PRE-survey score represents the 95\% confidence interval. An arrow pointing to the right or an increase in the length of darker bars are both indicative of positive shifts from PRE- to POST-survey.}"))
            elif((not PRE_Truth) and MID_Truth):
                doc.append(NoEscape(r"\captionof{figure}{Pre/Post changes in expert-like views expressed by students in your class (left) compared to students in other classes (right). The full length bars represent the fraction of students scoring \
                                    in each particular category with the darker shades representing higher scores. Above these bars is an arrow representing the change in average score on a question from Pre- to POST-survey. The shaded region around the average \
                                    PRE-survey score represents the 95\% confidence interval. An arrow pointing to the right or an increase in the length of darker bars are both indicative of positive shifts from PRE- to POST-survey. \
                                    \textbf{Note that the PRE-survey data displayed for your class was given as a mid-survey.}}"))
            else:
                doc.append(NoEscape(r"\captionof{figure}{Pre/Post changes in expert-like views expressed by students in your class (left) compared to students in other classes (right). The full length bars represent the fraction of students scoring \
                                    in each particular category with the darker shades representing higher scores. Above these bars is an arrow representing the change in average score on a question from PRE- to POST-survey. The shaded region around the average \
                                    PRE-survey score represents the 95\% confidence interval. An arrow pointing to the right or an increase in the length of darker bars are both indicative of positive shifts from PRE- to POST-survey. \
                                    \textbf{For your class, with only a post-survey, you will only see one bar and a single point representing the average score and the 95\% confidence interval for the POST-survey.}}"))


    FreqPredf = pd.DataFrame()
    FreqPostdf = pd.DataFrame()
    Questions = ['Q1b', 'Q1d', 'Q1e', 'Q2b', 'Q2d', 'Q2e', 'Q3b', 'Q3d', 'Q3e', 'Q4b']
    if Where == 'Automation':
        StatementsSeries = pd.read_csv('C:/PLIC/Questions.csv', header = None, index_col = 0, squeeze = True)
    else:
        StatementsSeries = pd.read_csv('C:/Users/Cole/Documents/GRA_Summer2018/PLIC_Reports/Questions.csv', header = None, index_col = 0, squeeze = True)
    Experts = ['Q1b_5', 'Q1d_3', 'Q1e_1', 'Q2b_2', 'Q2b_11', 'Q2d_4', 'Q2d_33', 'Q2e_19', 'Q2e_28', 'Q3b_2', 'Q3b_11', 'Q3d_8', 'Q3e_11', 'Q3e_28', 'Q4b_4', 'Q4b_33']
    Pseudos = ['Q1b_28', 'Q1d_5', 'Q1d_63', 'Q1e_4', 'Q1e_20', 'Q2b_6', 'Q2d_8', 'Q2e_6', 'Q2e_14', 'Q3b_6', 'Q3d_5', 'Q3e_13', 'Q4b_21']
    Novices = ['Q1b_16', 'Q1b_31', 'Q1d_57', 'Q1d_61', 'Q1e_17', 'Q1e_23', 'Q2b_9', 'Q2b_21', 'Q2d_27', 'Q2d_35', 'Q2e_15', 'Q2e_18', 'Q2e_23', 'Q3b_9', 'Q3b_21', 'Q3d_3', 'Q3d_6', 'Q3e_22', 'Q3e_24', 'Q3e_32', 'Q4b_27', 'Q4b_35']

    if((not PRE_Truth) and (not MID_Truth)):
        for Question in Questions:
            Qcols = [col for col in Postdf.columns if Question in col and 'TEXT' not in col and 'l' not in col and len(col) > 3]

            dfQPost = Postdf.loc[:, Qcols]

            MostFreqPost = dfQPost.sum(axis = 0).idxmax(axis = 1)
            del dfQPost[MostFreqPost]
            SecondFreqPost = dfQPost.sum(axis = 0).idxmax(axis = 1)
            del dfQPost[SecondFreqPost]
            ThirdFreqPost = dfQPost.sum(axis = 0).idxmax(axis = 1)

            MostFracPost = round(Postdf.loc[:, MostFreqPost].sum()/NumMatchedResponses * 100, 0)
            SecondFracPost = round(Postdf.loc[:, SecondFreqPost].sum()/NumMatchedResponses * 100, 0)
            ThirdFracPost = round(Postdf.loc[:, ThirdFreqPost].sum()/NumMatchedResponses * 100, 0)

            if(MostFreqPost in Experts):
                MostDes = 'E'
            elif(MostFreqPost in Pseudos):
                MostDes = 'P'
            elif(MostFreqPost in Novices):
                MostDes = 'N'
            else:
                MostDes = ''

            if(SecondFreqPost in Experts):
                SecondDes = 'E'
            elif(SecondFreqPost in Pseudos):
                SecondDes = 'P'
            elif(SecondFreqPost in Novices):
                SecondDes = 'N'
            else:
                SecondDes = ''

            if(ThirdFreqPost in Experts):
                ThirdDes = 'E'
            elif(ThirdFreqPost in Pseudos):
                ThirdDes = 'P'
            elif(ThirdFreqPost in Novices):
                ThirdDes = 'N'
            else:
                ThirdDes = ''

            FreqPostdf.loc[Question, 'Most Frequent'] = MostFreqPost
            FreqPostdf.loc[Question, 'Most Fraction'] = MostFracPost
            FreqPostdf.loc[Question, 'Most Designation'] = MostDes
            FreqPostdf.loc[Question, 'Second Frequent'] = SecondFreqPost
            FreqPostdf.loc[Question, 'Second Fraction'] = SecondFracPost
            FreqPostdf.loc[Question, 'Second Designation'] = SecondDes
            FreqPostdf.loc[Question, 'Third Frequent'] = ThirdFreqPost
            FreqPostdf.loc[Question, 'Third Fraction'] = ThirdFracPost
            FreqPostdf.loc[Question, 'Third Designation'] = ThirdDes

        doc.append(NewPage())
        with doc.create(Section("Your students' responses", numbering = False)):
            with doc.create(Center()) as centered:
                with centered.create(Table(position = 'h!')) as Tab:
                    with doc.create(Tabular('c l c')) as Tab1:
                        Tab1.add_row((FootnoteText("Question"), FootnoteText("Post-Survey"), FootnoteText('')))
                        for Question in Questions:
                            Tab1.add_hline()

                            Tab1.add_row(('', FootnoteText(StatementsSeries[FreqPostdf.loc[Question, 'Most Frequent']]) + FootnoteText(' (' + str(FreqPostdf.loc[Question, 'Most Fraction'].astype(int)) + '%)'), FootnoteText(FreqPostdf.loc[Question, 'Most Designation'])))

                            Tab1.add_row((FootnoteText(Question), FootnoteText(StatementsSeries[FreqPostdf.loc[Question, 'Second Frequent']]) + FootnoteText(' (' + str(FreqPostdf.loc[Question, 'Second Fraction'].astype(int)) + '%)'), FootnoteText(FreqPostdf.loc[Question, 'Second Designation'])))

                            Tab1.add_row(('', FootnoteText(StatementsSeries[FreqPostdf.loc[Question, 'Third Frequent']]) + FootnoteText(' (' + str(FreqPostdf.loc[Question, 'Third Fraction'].astype(int)) + '%)'), FootnoteText(FreqPostdf.loc[Question, 'Third Designation'])))

                        Tab1.add_hline()

                    Tab.add_caption(NoEscape("""
                                            Most popular responses selected by your students on post survey. The fraction of students that picked each option is
                                            included and expert (E), partial-expert (P), and novice (N) responses are indicated.
                                            """))

    else:
        for Question in Questions:
            Qcols = [col for col in Postdf.columns if Question in col and 'TEXT' not in col and 'l' not in col and len(col) > 3]

            if((not PRE_Truth) and MID_Truth):
                Predf = Middf.copy()

            dfQPre = Predf.loc[:, Qcols]
            dfQPost = Postdf.loc[:, Qcols]

            MostFreqPre = dfQPre.sum(axis = 0).idxmax(axis = 1)
            del dfQPre[MostFreqPre]
            SecondFreqPre = dfQPre.sum(axis = 0).idxmax(axis = 1)
            del dfQPre[SecondFreqPre]
            ThirdFreqPre = dfQPre.sum(axis = 0).idxmax(axis = 1)

            MostFracPre = round(Predf.loc[:, MostFreqPre].sum()/NumMatchedResponses * 100, 0)
            SecondFracPre = round(Predf.loc[:, SecondFreqPre].sum()/NumMatchedResponses * 100, 0)
            ThirdFracPre = round(Predf.loc[:, ThirdFreqPre].sum()/NumMatchedResponses * 100, 0)

            if(MostFreqPre in Experts):
                MostDes = 'E'
            elif(MostFreqPre in Pseudos):
                MostDes = 'P'
            elif(MostFreqPre in Novices):
                MostDes = 'N'
            else:
                MostDes = ''

            if(SecondFreqPre in Experts):
                SecondDes = 'E'
            elif(SecondFreqPre in Pseudos):
                SecondDes = 'P'
            elif(SecondFreqPre in Novices):
                SecondDes = 'N'
            else:
                SecondDes = ''

            if(ThirdFreqPre in Experts):
                ThirdDes = 'E'
            elif(ThirdFreqPre in Pseudos):
                ThirdDes = 'P'
            elif(ThirdFreqPre in Novices):
                ThirdDes = 'N'
            else:
                ThirdDes = ''

            FreqPredf.loc[Question, 'Most Frequent'] = MostFreqPre
            FreqPredf.loc[Question, 'Most Fraction'] = MostFracPre
            FreqPredf.loc[Question, 'Most Designation'] = MostDes
            FreqPredf.loc[Question, 'Second Frequent'] = SecondFreqPre
            FreqPredf.loc[Question, 'Second Fraction'] = SecondFracPre
            FreqPredf.loc[Question, 'Second Designation'] = SecondDes
            FreqPredf.loc[Question, 'Third Frequent'] = ThirdFreqPre
            FreqPredf.loc[Question, 'Third Fraction'] = ThirdFracPre
            FreqPredf.loc[Question, 'Third Designation'] = ThirdDes

            MostFreqPost = dfQPost.sum(axis = 0).idxmax(axis = 1)
            del dfQPost[MostFreqPost]
            SecondFreqPost = dfQPost.sum(axis = 0).idxmax(axis = 1)
            del dfQPost[SecondFreqPost]
            ThirdFreqPost = dfQPost.sum(axis = 0).idxmax(axis = 1)

            MostFracPost = round(Postdf.loc[:, MostFreqPost].sum()/NumMatchedResponses * 100, 0)
            SecondFracPost = round(Postdf.loc[:, SecondFreqPost].sum()/NumMatchedResponses * 100, 0)
            ThirdFracPost = round(Postdf.loc[:, ThirdFreqPost].sum()/NumMatchedResponses * 100, 0)

            if(MostFreqPost in Experts):
                MostDes = 'E'
            elif(MostFreqPost in Pseudos):
                MostDes = 'P'
            elif(MostFreqPost in Novices):
                MostDes = 'N'
            else:
                MostDes = ''

            if(SecondFreqPost in Experts):
                SecondDes = 'E'
            elif(SecondFreqPost in Pseudos):
                SecondDes = 'P'
            elif(SecondFreqPost in Novices):
                SecondDes = 'N'
            else:
                SecondDes = ''

            if(ThirdFreqPost in Experts):
                ThirdDes = 'E'
            elif(ThirdFreqPost in Pseudos):
                ThirdDes = 'P'
            elif(ThirdFreqPost in Novices):
                ThirdDes = 'N'
            else:
                ThirdDes = ''

            FreqPostdf.loc[Question, 'Most Frequent'] = MostFreqPost
            FreqPostdf.loc[Question, 'Most Fraction'] = MostFracPost
            FreqPostdf.loc[Question, 'Most Designation'] = MostDes
            FreqPostdf.loc[Question, 'Second Frequent'] = SecondFreqPost
            FreqPostdf.loc[Question, 'Second Fraction'] = SecondFracPost
            FreqPostdf.loc[Question, 'Second Designation'] = SecondDes
            FreqPostdf.loc[Question, 'Third Frequent'] = ThirdFreqPost
            FreqPostdf.loc[Question, 'Third Fraction'] = ThirdFracPost
            FreqPostdf.loc[Question, 'Third Designation'] = ThirdDes

        doc.append(NewPage())
        with doc.create(Section("Your students' responses", numbering = False)):
            with doc.create(Center()) as centered:
                with doc.create(Table(position = 'h!')) as Tab:
                    with doc.create(Tabular('c l c l c')) as Tab1:
                        if((not PRE_Truth) and MID_Truth):
                            Tab1.add_row((FootnoteText("Question"), FootnoteText("Mid-Survey"), FootnoteText(''), FootnoteText("Post-Survey"), FootnoteText('')))
                        else:
                            Tab1.add_row((FootnoteText("Question"), FootnoteText("Pre-Survey"), FootnoteText(''), FootnoteText("Post-Survey"), FootnoteText('')))
                        for Question in Questions:
                            Tab1.add_hline()

                            Tab1.add_row(('', FootnoteText(StatementsSeries[FreqPredf.loc[Question, 'Most Frequent']]) + FootnoteText(' (' + str(FreqPredf.loc[Question, 'Most Fraction'].astype(int)) + '%)'), FootnoteText(FreqPredf.loc[Question, 'Most Designation']),
                                FootnoteText(StatementsSeries[FreqPostdf.loc[Question, 'Most Frequent']]) + FootnoteText(' (' + str(FreqPostdf.loc[Question, 'Most Fraction'].astype(int)) + '%)'), FootnoteText(FreqPostdf.loc[Question, 'Most Designation'])))

                            Tab1.add_row((FootnoteText(Question), FootnoteText(StatementsSeries[FreqPredf.loc[Question, 'Second Frequent']]) + FootnoteText(' (' + str(FreqPredf.loc[Question, 'Second Fraction'].astype(int)) + '%)'), FootnoteText(FreqPredf.loc[Question, 'Second Designation']),
                                FootnoteText(StatementsSeries[FreqPostdf.loc[Question, 'Second Frequent']]) + FootnoteText(' (' + str(FreqPostdf.loc[Question, 'Second Fraction'].astype(int)) + '%)'), FootnoteText(FreqPostdf.loc[Question, 'Second Designation'])))

                            Tab1.add_row(('', FootnoteText(StatementsSeries[FreqPredf.loc[Question, 'Third Frequent']]) + FootnoteText(' (' + str(FreqPredf.loc[Question, 'Third Fraction'].astype(int)) + '%)'), FootnoteText(FreqPredf.loc[Question, 'Third Designation']),
                                FootnoteText(StatementsSeries[FreqPostdf.loc[Question, 'Third Frequent']]) + FootnoteText(' (' + str(FreqPostdf.loc[Question, 'Third Fraction'].astype(int)) + '%)'), FootnoteText(FreqPostdf.loc[Question, 'Third Designation'])))

                        Tab1.add_hline()

                    if((not PRE_Truth) and MID_Truth):
                        Tab.add_caption(NoEscape("""
                                                Most popular responses selected by your students on mid and post surveys. The fraction of students that picked each option is
                                                included and expert (E), partial-expert (P), and novice (N) responses are indicated.
                                                """))
                    else:
                        Tab.add_caption(NoEscape("""
                                                Most popular responses selected by your students on pre and post surveys. The fraction of students that picked each option is
                                                included and expert (E), partial-expert (P), and novice (N) responses are indicated.
                                                """))


    with doc.create(Section("Acknowledgements", numbering = False)):
        doc.append('We would like to acknowledge that the code for generating this report were based on the work by Wilcox et al.:\n\n')
        with doc.create(Itemize()) as itemize:
            itemize.add_item('Wilcox, B. R., Zwickl, B. M., Hobbs, R. D., Aiken, J. M., Welch, N. M., & Lewandowski, H. J. (2016). Alternative model for administration and analysis of research-based assessments. Physical Review Physics Education \
            Research, 12(1), 010139.')

        doc.append(NoEscape(r'For more information about the PLIC see: cperl.lassp.cornell.edu/PLIC \textbf{or} physport.org/assessments/PLIC.'))

    doc.generate_pdf(clean_tex = False)
    if Where == 'Automation':
        os.remove("C:/PLIC/Matched_PrePost.png")
        os.remove("C:/PLIC/TotalScores.png")
    else:
        os.remove("C:/Users/Cole/Documents/GRA_Summer2018/PLIC_Reports/Matched_PrePost.png")
        os.remove("C:/Users/Cole/Documents/GRA_Summer2018/PLIC_Reports/TotalScores.png")

    return
