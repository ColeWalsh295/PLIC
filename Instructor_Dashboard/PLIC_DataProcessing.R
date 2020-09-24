library(data.table)
library(dplyr)

PrePost.Long <- function(df){
  # convert wide form PLIC data.frame to long form on pre/posttest variable
  df <- data.table(df)[, N.Students := .N, by = .(Class_ID)]
  
  # Split dataframe into pre and post dataframes for concatenating in long form
  Pre.df <- df %>%
    mutate(Class_ID_PRE = Class_ID,
           Gender_PRE = Gender,
           Major_PRE = Major,
           URM_Status_PRE = URM_Status,
           Class_Standing_PRE = Class_Standing,
           Student.ID.Anon_PRE = Student.ID.Anon,
           ID_PRE = ID,
           LastName_PRE =	LastName,
           FirstName_PRE = FirstName,
           N.Students_PRE = N.Students) %>%
    select(grep('_PRE', names(.))) %>% # pretest columns end in '_x'
    `colnames<-`(gsub(x = names(.), pattern = "\\_PRE", replacement = "")) %>%
    mutate(TimePoint = 'PRE')
  
  Post.df <- df %>%
    mutate(Class_ID_POST = Class_ID,
           Gender_POST = Gender,
           Major_POST = Major,
           URM_Status_POST = URM_Status,
           Class_Standing_POST = Class_Standing,
           Student.ID.Anon_POST = Student.ID.Anon,
           ID_POST = ID,
           LastName_POST =	LastName,
           FirstName_POST = FirstName,
           N.Students_POST = N.Students) %>%
    select(grep('_POST', names(.))) %>% # posttest columns end in '_x'
    `colnames<-`(gsub(x = names(.), pattern = "\\_POST", replacement = "")) %>%
    mutate(TimePoint = 'POST')

  df <- rbind(Pre.df, Post.df) %>%
    data.frame(.)
  df$TimePoint <- ordered(df$TimePoint, c('PRE', 'POST'))
  
  return(df)
}