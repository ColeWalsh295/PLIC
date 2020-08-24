library(dplyr)

Merge.df.CIS <- function(df_path, 
                         CIS_path = 'C:/Users/Cole/Documents/GRA_Summer2018/Surveys/Collective_Surveys/Course_Information_Survey.csv', 
                         DeBug = FALSE, cols.to.use = 'General') {
  df <- read.csv(df_path, na.strings=c("","NA"))
  
  df_CIS <- read.csv(CIS_path)[-1,]
  
  df_CIS_cleaned <- df_CIS %>%
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
  if(cols.to.use == 'General') {
    df_CIS_cleaned <- df_CIS_cleaned %>%
      select(V1, Semester, Lab_Level, School, Institution_Type, N_Students)
  } else if (cols.to.use == 'Lab.Type') {
    subset(df_CIS_cleaned, select = c(V1, Semester, Lab_Level, School, Q2, Q6, Q27, Q28_1:Q33_4))
    }
  
  df2 <- merge(df, df_CIS_cleaned, by.x = 'Class_ID', by.y = 'V1') %>%
    distinct(V1_x, V1_y, .keep_all = TRUE)
  
  print('Total number of students...')
  print(nrow(df2))
  
  if (DeBug == TRUE) {
    print(df[(!(df$V1_y %in% df2$V1_y) | !(df$V1_y %in% df2$V1_y)), c('V1_x', 'V1_y')])
  }
  
  CTLabs <- c('R_6rq9bCkfvLDJEdz', 'R_3fNprNmbwV9C4X0', 'R_2R8MnTyv2jFgPzA', 'R_1IB300CxBKh0Tw7', 'R_1n7wUeClpEuZOkp')
  
  # Check 1116 from Fall 2017 where half of the class fell into each lab
  
  Pre1116_Intervention_IDS <-read.xlsx('C:/Users/Cole/Documents/GRA_Summer2018/Surveys/Fall2017/PRE/Fall2017_Cornell_University_1116_Smith_PRE_R_1Oko8BpPfb9rt0G_180202_I.xlsx', sheetIndex = 1) %>%
    filter(Intervention == 1) %>%
    select(V1)
  
  Post1116_Intervention_IDS <-read.xlsx('C:/Users/Cole/Documents/GRA_Summer2018/Surveys/Fall2017/POST/Fall2017_Cornell_University_1116_Smith_POST_R_1Oko8BpPfb9rt0G_180202_I.xlsx', sheetIndex = 1) %>%
    filter(Intervention == 1) %>%
    select(V1)
  
  df_cleaned <- df2 %>%
    mutate(Lab_Type = ifelse(Class_ID %in% CTLabs, 'CT', 'Other'),
           Gender = case_when(
             Q6e_1_y == 1 ~ 'M',
             Q6e_2_y == 1 ~ 'F',
             Q6e_3_y == 1 ~ 'Other',
             Q6e_1_x == 1 ~ 'M',
             Q6e_2_x == 1 ~ 'F',
             Q6e_3_x == 1 ~ 'Other'
           ),
           Major = case_when(
             Q6b_y < 4 ~ 'Physics',
             Q6b.i_y == 1 ~ 'Engineering',
             Q6b.i_y == 2 | Q6b.i_y == 3 ~ 'Other Science',
             Q6b.i_y == 4 ~ 'Other',
             Q6b_x < 4 ~ 'Physics',
             Q6b.i_x == 1 ~ 'Engineering',
             Q6b.i_x == 2 | Q6b.i_x == 3 ~ 'Other Science',
             Q6b.i_x == 4 ~ 'Other'
           ),
           Ethnicity = case_when(
             Q6f_2_y == 1 ~ 'Asian/Asian American',
             Q6f_6_y == 1 ~ 'White/Caucasian',
             Q6f_1_y == 1 ~ 'American Indian/Alaska Native',
             Q6f_3_y == 1 ~ 'African American',
             Q6f_4_y == 1 ~ 'Hispanic/Latino',
             Q6f_5_y == 1 ~ 'Native Hawaiian/Pacific Islander',
             Q6f_7_y == 1 ~ 'Other',
             Q6f_2_x == 1 ~ 'Asian/Asian American',
             Q6f_6_x == 1 ~ 'White/Caucasian',
             Q6f_1_x == 1 ~ 'American Indian/Alaska Native',
             Q6f_3_x == 1 ~ 'African American',
             Q6f_4_x == 1 ~ 'Hispanic/Latino',
             Q6f_5_x == 1 ~ 'Native Hawaiian/Pacific Islander',
             Q6f_7_x == 1 ~ 'Other'
           ),
           Research_Exp = case_when(
             Q6j_1_y == 1 & Q6j_2_y == 1 ~ 'None',
             Q6j_1_y + Q6j_2_y == 3 ~ '1 Semester',
             Q6j_1_y + Q6j_2_y == 4 ~ '2 Semesters',
             Q6j_1_y + Q6j_2_y > 4 ~ 'More than 2 Semesters',
             Q6j_1_x == 1 & Q6j_2_x == 1 ~ 'None',
             Q6j_1_x + Q6j_2_x == 3 ~ '1 Semester',
             Q6j_1_x + Q6j_2_x == 4 ~ '2 Semesters',
             Q6j_1_x + Q6j_2_x > 4 ~ 'More than 2 Semesters',
             TRUE ~ NA_character_
           ),
           Academic_Level = case_when(
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
  
  df_cleaned$Lab_Type[df2$V1_x %in% Pre1116_Intervention_IDS$V1] <- 'CT'
  df_cleaned$Lab_Type[df2$V1_y %in% Post1116_Intervention_IDS$V1] <- 'CT'
  
  print('Number of distinct classes...')
  print(length(unique(df_cleaned$Class_ID)))
  print('Number of unique schools...')
  print(length(unique(df_cleaned$School)))
  
  df_cleaned %>%
    distinct(Class_ID, .keep_all = TRUE) %>%
    count(Institution_Type, Lab_Level)
  
  df_cleaned$Survey_x[is.na(df_cleaned$Survey_x)] = 'F'
  df_cleaned$Survey_y[is.na(df_cleaned$Survey_y)] = 'F'
  
  df_cleaned[df_cleaned$Survey_x == 'F', 'PreScores'] <- NA
  df_cleaned[df_cleaned$Survey_y == 'F', 'PostScores'] <- NA
  
  df_cleaned$N_Students <- droplevels(df_cleaned$N_Students)
  df_cleaned$N_Students <- as.numeric(levels(df_cleaned$N_Students))[df_cleaned$N_Students]
  
  df_cleaned[(df_cleaned$Qt1_3_x < 30) & (df_cleaned$Qt2_3_x < 30) & (df_cleaned$Qt3_3_x < 30) & (df_cleaned$Qt4_3_x < 30) & (!is.na(df_cleaned$PreScores)) , 'PreScores'] <- NA
  df_cleaned[(df_cleaned$Qt1_3_y < 30) & (df_cleaned$Qt2_3_y < 30) & (df_cleaned$Qt3_3_y < 30) & (df_cleaned$Qt4_3_y < 30) & (!is.na(df_cleaned$PostScores)), 'PostScores'] <- NA

  return(df_cleaned)
}

Clean.Variables <- function (df, Scratch = TRUE, Old = FALSE, Question_cols = FALSE) {
  
  if (Scratch & !Old) {
    df_new <- df %>%
      mutate(Gender = case_when(
        Q6e_1 == 1 ~ 'M',
        Q6e_2 == 1 ~ 'F',
        Q6e_3 == 1 | Q6e_7 == 1 ~ 'Other'
      ),
      Major = case_when(
        Q6b == 1 | Q6b == 7 ~ 'Physics',
        Q6b == 2 ~ 'Engineering Physics',
        Q6b.i == 3 ~ 'Engineering',
        Q6b.i == 4 ~ 'Life Science',
        Q6b.i == 8 ~ 'Other Physical Science',
        Q6b.i == 5 ~ 'Other'
      ),
      Ethnicity = case_when(
        Q6f_2 == 1 ~ 'Asian/Asian American',
        Q6f_6 == 1 ~ 'White/Caucasian',
        Q6f_1 == 1 ~ 'American Indian/Alaska Native',
        Q6f_3 == 1 ~ 'African American',
        Q6f_4 == 1 ~ 'Hispanic/Latino',
        Q6f_5 == 1 ~ 'Native Hawaiian/Pacific Islander',
        Q6f_7 == 1 ~ 'Other'
      ),
      Research_Exp = case_when(
        Q6j_1 == 1 & Q6j_2 == 1 ~ 'None',
        Q6j_1 + Q6j_2 == 3 ~ '1 Semester',
        Q6j_1 + Q6j_2 == 4 ~ '2 Semesters',
        Q6j_1 + Q6j_2 > 4 ~ 'More than 2 Semesters',
        TRUE ~ NA_character_
      ),
      Academic_Level = case_when(
        Q6a == 1 ~ 'Freshman',
        Q6a == 2 ~ 'Sophomore',
        Q6a == 3 ~ 'Junior',
        Q6a == 4 ~ 'Senior',
        Q6a == 5 ~ 'Graduate',
        TRUE ~ NA_character_
      ))
  } else if (Old) {
    df_new <- df %>%
      mutate(Gender = case_when(
        Q9_1 == 1 ~ 'M',
        Q9_2 == 1 ~ 'F',
        Q9_3 == 1 ~ 'Other'
      ),
      Major = case_when(
        Q7 == 1 ~ 'Physics',
        Q7 == 2 ~ 'Engineering Physics',
        Q7 == 3 ~ 'Engineering',
        Q7 == 4 ~ 'Other Science',
        Q7 == 5 ~ 'Other'
      ),
      Ethnicity = case_when(
        Q10_2 == 1 ~ 'Asian/Asian American',
        Q10_6 == 1 ~ 'White/Caucasian',
        Q10_1 == 1 ~ 'American Indian/Alaska Native',
        Q10_3 == 1 ~ 'African American',
        Q10_4 == 1 ~ 'Hispanic/Latino',
        Q10_5 == 1 ~ 'Native Hawaiian/Pacific Islander',
        Q10_7 == 1 ~ 'Other'
      ),
      Research_Exp = case_when(
        Q12_1 == 1 & Q12_2 == 1 ~ 'None',
        Q12_1 + Q12_2 == 3 ~ '1 Semester',
        Q12_1 + Q12_2 == 4 ~ '2 Semesters',
        Q12_1 + Q12_2 > 4 ~ 'More than 2 Semesters',
        TRUE ~ NA_character_
      ),
      Academic_Level = case_when(
        Q6 == 1 ~ 'Freshman',
        Q6 == 2 ~ 'Sophomore',
        Q6 == 3 ~ 'Junior',
        Q6 == 4 ~ 'Senior',
        Q6 == 5 ~ 'Graduate',
        TRUE ~ NA_character_
      ))
  } else {
    df_new <- df %>%
      mutate(Gender = relevel(as.factor(ifelse(Gender == 'Other', NA_character_, Gender)), ref = 'M'),
             #Major = relevel(as.factor(Major), ref = 'Other'),
             Major = relevel(as.factor(case_when(
               Major == 'Physics' ~ 'Physics',
               Major == 'Engineering' ~ 'Engineering',
               TRUE ~ 'Other'
             )), ref = 'Other'),
             Ethnicity = relevel(as.factor(case_when(
               Ethnicity == 'White/Caucasian' ~ 'Majority',
               Ethnicity == 'Asian/Asian American' ~ 'Majority',
               TRUE ~ 'URM'
             )), ref = 'Majority'),
             Research_Exp = relevel(as.factor(case_when(
               Research_Exp == 'None' ~ 'None',
               TRUE ~ 'Some')), ref = 'None'),
             Research_Exp = relevel(as.factor(case_when(
               Research_Exp == 'None' ~ 'None',
               TRUE ~ 'Some')), ref = 'None')) 
    
    if(Question_cols == FALSE) {
      df_new = df_new %>%
        select(Class_ID, Gender, Major, Ethnicity, Lab_Level, Lab_Type, PostScores, PreScores)
    } else {
      df_new <- df_new %>%
        select(c(Class_ID, Gender, Major, Ethnicity, Lab_Level, Lab_Type, PostScores, PreScores,
                 grep('[BDE]s_', names(.))))
    }
  }
  
  return(df_new)
}

Create.Class.Variables <- function(df) {
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

Remove.Surveys.Time <- function(df) {
  df_new <- df %>%
    filter((Survey == 'C') & ((df$Qt1_3 >= 30) | (df$Qt2_3 >= 30) | (df$Qt3_3 >= 30) 
           & (df$Qt4_3 >= 30)))
  
  return(df_new)
  
  return(df_new)
}
