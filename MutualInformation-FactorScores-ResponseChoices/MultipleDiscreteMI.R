library(dplyr)
library(infotheo)

Multiple.Mutual.Information <- function(df1, mod = NULL, df2 = NULL, df_Scores = NULL, i_start = floor(nrow(df)^(1/3)), 
                                        i_end = ceiling(nrow(df)^(1/3))) {
  df_Items <- df1 %>%
    lapply(., as.factor) %>%
    as.data.frame(.)
  
  if(is.null(df_Scores)){
    if(is.null(df2)){
      df_Scores <- data.frame(factor.scores(df1, mod)$scores) %>%
        lapply(., as.factor) %>%
        as.data.frame(.)
    } else {
      df_Scores <- data.frame(factor.scores(df2, mod)$scores) %>%
        lapply(., as.factor) %>%
        as.data.frame(.)
    }
  }

  
  for(i in i_start:i_end){
    if(i > i_start){
      MI.Matrix <- cbind(MI.Matrix, sapply(df_Items, MI.vec.to.bits, 
                                           df_Features = discretize(df_Scores, nbins = i)))
    } else {
      MI.Matrix <- sapply(df_Items, MI.vec.to.bits, df_Features = discretize(df_Scores, nbins = i))
    }
  }
  
  return(MI.Matrix)
  
}

MI.vec.to.bits <- function (Response_vec, df_Features) {
  MI <- round(natstobits(mutinformation(Response_vec, df_Features)), 3)
  return(MI)
}