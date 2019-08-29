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
           Gender_x = Gender,
           Major_x = Major,
           URM_Status_x = URM_Status,
           Class_Standing_x = Class_Standing,
           Student.ID.Anon_x = Student.ID.Anon) %>%
    select(grep('_x|Available', names(.))) %>%
    `colnames<-`(gsub(x = names(.), pattern = "\\_x", replacement = "")) %>%
    mutate(TimePoint = 'PRE')
  
  Post.df <- df %>%
    mutate(TotalScores_y = PostScores,
           Class_ID_y = Class_ID,
           Gender_y = Gender,
           Major_y = Major,
           URM_Status_y = URM_Status,
           Class_Standing_y = Class_Standing,
           Student.ID.Anon_y = Student.ID.Anon) %>%
    select(grep('_y|Available', names(.))) %>%
    `colnames<-`(gsub(x = names(.), pattern = "\\_y", replacement = "")) %>%
    mutate(TimePoint = 'POST')
  
  # Concatenate dataframes
  df <- rbind(Pre.df, Post.df) %>%
    rename(Q1B = Q1Bs, Q1D = Q1Ds, Q1E = Q1Es, Q2B = Q2Bs, Q2D = Q2Ds, Q2E = Q2Es, Q3B = Q3Bs, Q3D = Q3Ds, Q3E = Q3Es, Q4B = Q4Bs)
  df$TimePoint <- ordered(df$TimePoint, c('PRE', 'POST'))
  
  return(df)
}