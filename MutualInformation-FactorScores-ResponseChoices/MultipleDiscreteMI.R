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

MI.CI <- function(raw.dataframe, scores, reps = 1000, CI.Low = 0.025, 
                  CI.High = 0.975) {
  
  out.dataframe <- sapply(raw.dataframe, MI.vec.to.bits, df_Features = scores) %>%
    data.frame(.) %>%
    `colnames<-`(c("MI")) %>%
    mutate(Item = sapply(colnames(raw.dataframe), function(x) toupper(x)),
           Prop.Sel = round(colMeans(raw.dataframe), 3),
           Question = sapply(Item, function(x) toupper(substr(x, 1, 3)))) %>%
    select(Item, Question, Prop.Sel, MI) %>%
    arrange(desc(MI))
  
  df <- cbind(raw.dataframe, scores)
  df.boot <- replicate(reps, df[sample(1:nrow(df), replace = T),], simplify = F)
  MI.boot <- sapply(df.boot, function(x) apply(x, 2, MI.vec.to.bits, df_Features = x[, ncol(x)]))
  
  MI.CI <- apply(MI.boot, 1, quantile, probs = c(CI.Low, CI.High))
  MI.CI <- data.frame(t(MI.CI))
  MI.CI$Item <- toupper(row.names(MI.CI))
  
  dataframe.CI <- left_join(out.dataframe, MI.CI, 'Item')
  colnames(dataframe.CI)[(ncol(dataframe.CI) - 1):ncol(dataframe.CI)] <- c('CI.Low', 'CI.High')
  return(dataframe.CI)
}