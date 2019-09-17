Merge.CIS <- function(df,
                      CIS.path = 'C:/Users/Cole/Documents/PLIC_DATA/Course_Information_Survey_re-populated.csv'){
  
  df_CIS <- read.csv(CIS.path)[-1,] %>%
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
      Q4 == 'Cornell University ' ~ 'Cornell University',
      Q4 == 'Appalachian State Univ' ~ 'Appalachian State University',
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
  names(df_CIS)[1] <- 'V1'
  df.merged <- merge(df, df_CIS, by.x = 'Class_ID', by.y = 'V1') %>%
    dplyr::distinct(V1_x, V1_y, .keep_all = TRUE)
  return(df.merged)
}

Clean.PLIC <- function(df, Collapse.vars = TRUE){
  
  df.PLIC.clean <- df %>%
  mutate(Gender = case_when(
           Q6e_1_y == 1 & is.na(Q6e_2_y) & is.na(Q6e_3_y) & is.na(Q6e_7_y) ~ 'Men',
           Q6e_2_y == 1 & is.na(Q6e_1_y) & is.na(Q6e_3_y) & is.na(Q6e_7_y) ~ 'Women',
           (Q6e_3_y == 1 | Q6e_7_y == 1) & is.na(Q6e_1_y) & is.na(Q6e_2_y)  ~ 'Non-binary',
           Q6e_1_x == 1 & is.na(Q6e_2_x) & is.na(Q6e_3_x) & is.na(Q6e_7_x) ~ 'Men',
           Q6e_2_x == 1 & is.na(Q6e_1_x) & is.na(Q6e_3_x) & is.na(Q6e_7_x) ~ 'Women',
           (Q6e_3_x == 1 | Q6e_7_x == 1) & is.na(Q6e_1_x) & is.na(Q6e_2_x)  ~ 'Non-binary',
           #Q6e_1_y == 1 | Q6e_2_y == 1 | Q6e_3_y == 1 | Q6e_7_y == 1 | 
            # Q6e_1_x == 1 | Q6e_2_x == 1 | Q6e_3_x == 1 | Q6e_7_x == 1 ~ 'Multiple',
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
           Q6f_3_y == 1 ~ 'African American',
           Q6f_4_y == 1 ~ 'Hispanic/Latino',
           Q6f_7_y == 1 ~ 'Other',
           Q6f_2_y == 1 ~ 'Asian/Asian American',
           Q6f_6_y == 1 ~ 'White/Caucasian',
           Q6f_5_x == 1 ~ 'Native Hawaiian/Pacific Islander',
           Q6f_1_x == 1 ~ 'American Indian/Alaska Native',
           Q6f_3_x == 1 ~ 'African American',
           Q6f_4_x == 1 ~ 'Hispanic/Latino',
           Q6f_7_x == 1 ~ 'Other',
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
  
  if(Collapse.vars){
    df.PLIC.clean <- df.PLIC.clean %>%
      mutate(Gender = relevel(as.factor(ifelse(Gender == 'Non-binary', NA_character_, Gender)),
                              ref = 'Men'),
             Major = relevel(as.factor(case_when(
               Major == 'Physics' ~ 'Physics',
               Major == 'Engineering' ~ 'Engineering',
               !is.na(Major) ~ 'Other',
               TRUE ~ NA_character_)), ref = 'Other'),
             URM_Status = relevel(as.factor(case_when(
               Ethnicity == 'White/Caucasian' | Ethnicity == 'Asian/Asian American' ~ 'Majority',
               !is.na(Ethnicity) ~ 'URM',
               TRUE ~ NA_character_)), ref = 'Majority'),
             Class_Standing = relevel(as.factor(case_when(
               Class_Standing == 'Freshman' ~ 'First Year',
               !is.na(Class_Standing) ~ 'Beyond First Year',
               TRUE ~ NA_character_)), ref = 'First Year'))
  }
  
  
  return(df.PLIC.clean)
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

Drop.Demgraphics <- function(df){
  df <- df %>%
    select(grep('Q5', '', names(.)))
}

PrePost.Long <- function(df){
  # Clean demographic data
  df <- data.table(df)[, N.Students := .N, by = .(Class_ID)]
  
  # Split dataframe into pre and post dataframes for concatenating in long form
  Pre.df <- df %>%
    mutate(TotalScores_x = PreScores,
           Class_ID_x = Class_ID,
           N.Students_x = N.Students,
           Gender_x = Gender,
           Major_x = Major,
           URM_Status_x = URM_Status,
           Class_Standing_x = Class_Standing,
           Student.ID.Anon_x = Student.ID.Anon) %>%
    select(grep('_x', names(.))) %>%
    `colnames<-`(gsub(x = names(.), pattern = "\\_x", replacement = "")) %>%
    #filter(Survey == 'C') %>%
    mutate(TimePoint = 'PRE')
  
  Post.df <- df %>%
    mutate(TotalScores_y = PostScores,
           Class_ID_y = Class_ID,
           N.Students_y = N.Students,
           Gender_y = Gender,
           Major_y = Major,
           URM_Status_y = URM_Status,
           Class_Standing_y = Class_Standing,
           Student.ID.Anon_y = Student.ID.Anon) %>%
    select(grep('_y', names(.))) %>%
    `colnames<-`(gsub(x = names(.), pattern = "\\_y", replacement = "")) %>%
    #filter(Survey == 'C') %>%
    mutate(TimePoint = 'POST')
  
  # Concatenate dataframes
  df <- rbind(Pre.df, Post.df) %>%
    rename(Q1B = Q1Bs, Q1D = Q1Ds, Q1E = Q1Es, Q2B = Q2Bs, Q2D = Q2Ds, Q2E = Q2Es, Q3B = Q3Bs, Q3D = Q3Ds, Q3E = Q3Es, Q4B = Q4Bs)
  df$TimePoint <- ordered(dfTimePoint, c('PRE', 'POST'))
  
  return(df)
}

DeIdentify <- function(file = 'C:/Users/Cole/Documents/PLIC_DATA/Collective_Surveys/Complete/Complete_Concat.csv', 
                       Headers.File = 'C:/Users/Cole/Documents/PLIC_DATA/PLIC_May2019.csv',
                       Out.File = 'C:/Users/Cole/Documents/PLIC_DATA/Collective_Surveys/Complete/Complete_Concat_DeIdentified.csv'){
  id.cols <- c('Gender', 'Major', 'URM_Status', 'Class_Standing', 'Class_ID', 
               'PreScores', 'PostScores')
  
  df <- fread(file) %>%
    Clean.PLIC(.) %>%
    select(c(grep('(Q1|Q2|Q3|Q4|Q7|Qt\\d|Q_Total|Survey)', names(.))), id.cols)
  
  df.Class <- Merge.CIS(df) %>%
    mutate(Lab_Level = relevel(as.factor(case_when(
      (Lab_Level == 'Intro-Algebra') | (Lab_Level == 'Intro-Calculus') ~ 'FY',
      (Lab_Level == 'Sophomore') | (Lab_Level == 'Junior') | (Lab_Level == 'Senior') ~ 'BFY',
      TRUE ~ NA_character_
    )), ref = 'FY')) %>%
    select(c(names(df), Lab_Level)) %>%
    mutate_all(as.character)
  
  df.Class <- data.table(df.Class)[Survey_x == 'F', `:=`(Q1Bs_x = '', Q1Ds_x = '', Q1Es_x = '', 
                                                         Q2Bs_x = '', Q2Ds_x = '', Q2Es_x = '', 
                                                         Q3Bs_x = '', Q3Ds_x = '', Q3Es_x = '', 
                                                         Q4Bs_x = '', PreScores = '')]
  df.Class <- data.table(df.Class)[Survey_y == 'F', `:=`(Q1Bs_y = '', Q1Ds_y = '', Q1Es_y = '', 
                                                         Q2Bs_y = '', Q2Ds_y = '', Q2Es_y = '', 
                                                         Q3Bs_y = '', Q3Ds_y = '', Q3Es_y = '', 
                                                         Q4Bs_y = '', PostScores = '')]
                                                         
  df.headers <- fread(Headers.File, nrows = 1, 
                      header = TRUE)
  
  Scores.df <- data.frame(Q1Bs = 'Q1B Score', Q1Ds = 'Q1D Score', Q1Es = 'Q1E Score', 
                          Q2Bs = 'Q2B Score', Q2Ds = 'Q2D Score', Q2Es = 'Q2E Score', 
                          Q3Bs = 'Q3B Score', Q3Ds = 'Q3D Score', Q3Es = 'Q3E Score', 
                          Q4Bs = 'Q4B Score')
  df.headers <- cbind(df.headers, Scores.df)
  
  FR.df <- data.frame(Q1b = 'Q1B FR', Q1d = 'Q1D FR', Q1e = 'Q1E FR', Q2b = 'Q2B FR', 
                      Q2d = 'Q2D FR', Q2e = 'Q2E FR', Q3b = 'Q3B FR', Q3d = 'Q3D FR', 
                      Q3e = 'Q3E FR', Q4b = 'Q4B FR', Survey = 'Survey closed/free response')
  df.headers <- cbind(df.headers, FR.df)
  
  df.headers.x <- data.frame(df.headers)
  colnames(df.headers.x) <- paste(colnames(df.headers.x), '_x', sep = '')
  
  df.headers.y <- data.frame(df.headers)
  colnames(df.headers.y) <- paste(colnames(df.headers.y), '_y', sep = '')
  
  df.headers <- cbind(df.headers.x, df.headers.y)
  df.headers <- df.headers[, which(names(df.headers) %in% names(df))]
  
  IDs.df <- data.frame(Gender = 'Gender', Major = 'Major', URM_Status = 'URM Status', 
                       Class_Standing = 'Class Standing', Class_ID = 'Class ID', 
                       PreScores = 'PreScores', PostScores = 'PostScores', 
                       Lab_Level = 'Your indicated Lab Level')
  df.headers <- cbind(df.headers, IDs.df)
  
  df.out <- rbind(df.headers, df.Class) %>%
    mutate_all(as.character)
  df.out[is.na(df.out)] <- ''
  write.csv(df.out, file = Out.File, row.names = FALSE)
  
  df[is.na(df.out$Q1Bs_y), 'Q1BS_y'] <- ''
  print(class(df.out$Q1Bs_y))
  
  return(df.Class)
}

