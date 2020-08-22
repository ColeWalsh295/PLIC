library(tidyverse)
library(data.table)
library(docstring)

Collapse.vars <- function(df){
  #' Create readable demographic variables
  #' 
  #' @param df data.frame of merged PLIC responses
  #' 
  #' returns data.frame with appended demographic columns
  
  # we take posttest survey entries when available, otherwise pretest
  df <- df %>%
    mutate(Major = case_when(
      (Q6b_y == 1) | (Q6b_y == 2) | (Q6b_y == 3) ~ 'Physics',
      Q6b.i_y == 1 ~ 'Engineering',
      (Q6b.i_y == 2) | (Q6b.i_y == 3) ~ 'Other science',
      Q6b.i_y == 4 ~ 'Other',
      (Q6b_x == 1) | (Q6b_x == 2) | (Q6b_x == 3) ~ 'Physics',
      Q6b.i_x == 1 ~ 'Engineering',
      (Q6b.i_x == 2) | (Q6b.i_x == 3) ~ 'Other science',
      Q6b.i_x == 4 ~ 'Other',
      TRUE ~ 'Unknown'),
      Gender = case_when(
        (Q6e_3_y == 1) | (Q6e_7_y == 1) ~ 'Non-binary',
        Q6e_2_y == 1 ~ 'Woman',
        Q6e_1_y == 1 ~ 'Man',
        (Q6e_3_x == 1) | (Q6e_7_x == 1) ~ 'Non-binary',
        Q6e_2_x == 1 ~ 'Woman',
        Q6e_1_x == 1 ~ 'Man',
        TRUE ~ 'Unknown'
      ),
      Race.ethnicity.AmInd = 1 * ((Q6f_1_y == 1) | (Q6f_1_x == 1)),
      Race.ethnicity.Asian = 1 * ((Q6f_2_y == 1) | (Q6f_2_x == 1)),
      Race.ethnicity.Black = 1 * ((Q6f_3_y == 1) | (Q6f_3_x == 1)),
      Race.ethnicity.Hispanic = 1 * ((Q6f_4_y == 1) | (Q6f_4_x == 1)),
      Race.ethnicity.NatHawaii = 1 * ((Q6f_5_y == 1) | (Q6f_5_x == 1)),
      Race.ethnicity.White = 1 * ((Q6f_6_y == 1) | (Q6f_6_x == 1)),
      Race.ethnicity.Other = 1 * ((Q6f_7_y == 1) | (Q6f_7_x == 1)),
      Race.ethnicity.unknown = 1 * ((Race.ethnicity.AmInd == 0) & 
                                      (Race.ethnicity.Asian == 0) & 
                                      (Race.ethnicity.Black == 0) & 
                                      (Race.ethnicity.Hispanic == 0) & 
                                      (Race.ethnicity.NatHawaii == 0) & 
                                      (Race.ethnicity.White == 0) & 
                                      (Race.ethnicity.Other == 0))) %>%
    mutate(Major = relevel(as.factor(Major), ref = 'Physics'),
           Gender = relevel(as.factor(Gender), ref = 'Man'))
  
  df[is.na(df)] <- 0
  df[names(df) %like% "Race"] <- lapply(df[names(df) %like% "Race"], factor, 
                                        levels = c(1, 0))
  df[names(df) %like% "Race"] <- lapply(df[names(df) %like% "Race"], relevel, ref = '0')
  
  return(df)
}

Race.ethnicity.table <- function(df, Lab.Purpose = FALSE, normalize = TRUE){
  #' print contingency table for race/ethncity variable
  #' 
  #' @param df PLIC data.frame with demographic race/ethnicity column
  #' @param Lab.Purpose whether to produce contingency table with lab purpose
  #' @param normalize whether to produce results as fractions
  
  Race.ethnicity.cols <- names(df)[names(df) %like% 'Race']
  if(Lab.Purpose){
    for(col in Race.ethnicity.cols){
      print(col)
      print(table(df[, col], df$Lab_purpose))
    }
  } else {
    for(col in Race.ethnicity.cols){
      print(col)
      if(normalize){
        print(table(df[, col])/nrow(df) * 100)
      } else {
        print(table(df[, col]))
      }
    }
  }
}

Center.Variables <- function(df) {
  #' Center pre and posttest scores
  #' 
  #' @param df data.frame of PLIC pretest and posttest scores with Class_ID
  #' 
  #' returns data.frame with centered test variables appended
  
  df_Class <- df %>%
    mutate(Gain = PostScores - PreScores,
           PreScores.gmc = PreScores - mean(PreScores, na.rm = TRUE)) %>%
    group_by(Class_ID) %>%
    mutate(PreScores.cm = mean(PreScores, na.rm = TRUE),
           PreScores.cwc = PreScores - mean(PreScores, na.rm = TRUE)) %>%
    ungroup() %>%
    mutate(PreScores.cmc = PreScores.cm - mean(PreScores, na.rm = TRUE))
  
  return(df_Class)
}

PrePost.Long <- function(df){
  #' Convert PLIC scores into long form
  #' 
  #' @param df PLIC data.frame
  #' 
  #' returns PLIC data.frame with test scores in long form
  
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