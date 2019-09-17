library(dplyr)

Generate.CIS <- function(CIS.path = 'C:/Users/Cole/Documents/PLIC_DATA/Course_Information_Survey.csv'){

  df_CIS <- read.csv(CIS.path)[-1,]
  
  df.CIS.clean <- df_CIS %>%
    mutate(Semester = case_when(
      Q9a == 1 ~ 'Fall',
      (Q9 == 1 & Q9a == 2) | (Q9 == 2 & Q9b == 3) ~ 'Spring',
      (Q9 == 1 & Q9a == 3) | (Q9 == 2 & Q9b == 4) ~ 'Summer',
      (Q9 == 1 & Q9a == 4) | (Q9 == 2 & Q9b == 5) ~ 'Year',
      Q9 == 2 & Q9b == 2 ~ 'Winter',
      TRUE ~ NA_character_
    ),
    Lab_Level = case_when(
      Q7 == 1 ~ 'Intro-Algebra',
      Q7 == 2 ~ 'Intro-Calculus',
      Q7 == 3 ~ 'Sophomore',
      Q7 == 4 ~ 'Junior',
      Q7 == 5 ~ 'Senior',
      TRUE ~ NA_character_
    ),
    Where_Completed = case_when(
      Q44 == 1 ~ 'In Class/Lab',
      Q44 == 2 ~ 'At Home',
      TRUE ~ NA_character_
    ),
    N_Students = Q8,
    School = case_when(
      Q4 == 'UBC' ~ 'University of British Columbia',
      Q4 == 'University of Maine Orono' ~ 'University of Maine',
      Q4 == 'University of Maine, Orono' ~ 'University of Maine',
      Q4 == '1971' ~ 'CSU Chico',
      TRUE ~ as.character(Q4)),
    Institution_Type = case_when(
      Q19 == 1 ~ '2 year college',
      Q19 == 2 ~ '4 year college',
      Q19 == 3 ~ "Master's granting institution",
      Q19 == 4 ~ 'PhD granting institution',
      Q17 == 1 ~ 'Cole needs to input this info manually',
      TRUE ~ NA_character_
    ),
    Lab_Purpose = case_when(
      Q27 == 1 ~ 'Reinforce physics concepts',
      Q27 == 2 ~ 'Develop lab skills',
      Q27 == 3 ~ 'Both about equally',
      Q17 == 1 ~ 'Cole needs to input this info manually',
      TRUE ~ NA_character_
    ))
}

Clean.PLIC <- function(df, CR.only = TRUE, Collapse.vars = TRUE){
  
  df.PLIC.clean <- df %>%
  mutate(Gender = case_when(
    Q6e_2_y == 1 ~ 'F',
    Q6e_1_y == 1 ~ 'M',
    Q6e_3_y == 1 | Q6e_7_y == 1 ~ 'Other',
    Q6e_2_x == 1 ~ 'F',
    Q6e_1_x == 1 ~ 'M',
    Q6e_3_x == 1 | Q6e_7_x == 1 ~ 'Other',
    TRUE ~ NA_character_
    ),
    Major = case_when(
      Q6b_y < 4 ~ 'Physics',
      Q6b.i_y == 1 ~ 'Engineering',
      Q6b.i_y == 2 | Q6b.i_y == 3 ~ 'Other Science',
      Q6b.i_y == 4 ~ 'Other',
      Q6b_x < 4 ~ 'Physics',
      Q6b.i_x == 1 ~ 'Engineering',
      Q6b.i_x == 2 | Q6b.i_x == 3 ~ 'Other Science',
      Q6b.i_x == 4 ~ 'Other',
      TRUE ~ NA_character_
      ),
    Ethnicity = case_when(
      Q6f_5_y == 1 ~ 'Native Hawaiian/Pacific Islander',
      Q6f_1_y == 1 ~ 'American Indian/Alaska Native',
      Q6f_7_y == 1 ~ 'Other',
      Q6f_3_y == 1 ~ 'African American',
      Q6f_4_y == 1 ~ 'Hispanic/Latino',
      Q6f_2_y == 1 ~ 'Asian/Asian American',
      Q6f_6_y == 1 ~ 'White/Caucasian',
      Q6f_5_x == 1 ~ 'Native Hawaiian/Pacific Islander',
      Q6f_1_x == 1 ~ 'American Indian/Alaska Native',
      Q6f_7_x == 1 ~ 'Other',
      Q6f_3_x == 1 ~ 'African American',
      Q6f_4_x == 1 ~ 'Hispanic/Latino',
      Q6f_2_x == 1 ~ 'Asian/Asian American',
      Q6f_6_x == 1 ~ 'White/Caucasian',
      TRUE ~ NA_character_
      ),
    Class_Standing = case_when(
      Q6a_y == 1 ~ 'Freshman',
      Q6a_y == 2 ~ 'Sophomore',
      Q6a_y == 3 ~ 'Junior',
      Q6a_y == 4 ~ 'Senior',
      Q6a_y == 5 ~ 'Graduate',
      Q6a_x == 1 ~ 'Freshman',
      Q6a_x == 2 ~ 'Sophomore',
      Q6a_x == 3 ~ 'Junior',
      Q6a_x == 4 ~ 'Senior',
      Q6a_x == 5 ~ 'Graduate',
      TRUE ~ NA_character_
      ))
  
  if(CR.only){
    df.PLIC.clean <- df.PLIC.clean[(df.PLIC.clean$Survey_x == 'C') & (df.PLIC.clean$Survey_y == 'C'),]
  }
  
  if(Collapse.vars){
    df.PLIC.clean <- df.PLIC.clean %>%
      mutate(Gender = relevel(as.factor(ifelse(Gender == 'Other', NA_character_, Gender)), 
                              ref = 'M'),
             Major = relevel(as.factor(case_when(
               Major == 'Physics' ~ 'Physics',
               Major == 'Engineering' ~ 'Engineering',
               !is.na(Major) ~ 'Other',
               TRUE ~ NA_character_)), ref = 'Other'),
             Ethnicity = relevel(as.factor(case_when(
               Ethnicity == 'White/Caucasian' | Ethnicity == 'Asian/Asian American' ~ 'Majority',
               !is.na(Ethnicity) ~ 'URM',
               TRUE ~ NA_character_)), ref = 'Majority'),
             Class_Standing = relevel(as.factor(case_when(
               Class_Standing == 'Freshman' ~ 'FY',
               !is.na(Class_Standing) ~ 'BFY',
               TRUE ~ NA_character_)), ref = 'FY'))
  }
  
  return(df.PLIC.clean)
}

Create.Class.PreScore <- function(df) {
  df_Class <- aggregate(df$PreScores, by = list(df$Class_ID), FUN = mean)
  colnames(df_Class) <- c('Class_ID', 'Class_PreScore')
  df_Class$Class_PreScore_GrandMC <- scale(df_Class$Class_PreScore, scale = FALSE) %>%
    as.vector()
  df_reg <- merge(df, df_Class, by = 'Class_ID') %>%
    mutate(PreScores_GroupMC = PreScores - Class_PreScore,
           PreScores_GrandMC = PreScores - mean(PreScores)) %>%
    select(-c(Class_PreScore))
  
  return(df_reg)
}


