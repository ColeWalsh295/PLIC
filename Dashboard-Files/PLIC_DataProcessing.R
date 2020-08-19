PrePost.Long <- function(df){
  # convert wide form PLIC data.frame to long form on pre/posttest variable
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
    select(grep('_x|Available', names(.))) %>% # pretest columns end in '_x'
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
    select(grep('_y|Available', names(.))) %>% # posttest columns end in '_x'
    `colnames<-`(gsub(x = names(.), pattern = "\\_y", replacement = "")) %>%
    mutate(TimePoint = 'POST')
  
  # Concatenate dataframes
  df <- rbind(Pre.df, Post.df) %>% # rename score columns to get rid of the s at the end
    rename(Q1B = Q1Bs, Q1D = Q1Ds, Q1E = Q1Es, Q2B = Q2Bs, Q2D = Q2Ds, Q2E = Q2Es, 
           Q3B = Q3Bs, Q3D = Q3Ds, Q3E = Q3Es, Q4B = Q4Bs)
  df$TimePoint <- ordered(df$TimePoint, c('PRE', 'POST'))
  
  return(df)
}