library(tidyverse)
library(mc2d)
library(docstring)

Fuzzy.Kappa <- function(df1, df2){
  #' Calculate fuzzy kappa between two coders
  #' 
  #' @param df1 first data.frame of codes applied by one coder
  #' @param df2 second data.frame of codes applied by second coder, should be same
  #' dimensions as df1
  #' 
  #' returns fuzzy kappa interrater reliability
  
  df1.norm <- Get.Norm(df1)
  df2.norm <- Get.Norm(df2)
  P.obs <- sum(mc2d::pmin(df1.norm, df2.norm))/nrow(df1) # observed frequencies using t-norm min
  
  df1.freq <- Get.Prob.Distribution(df1.norm)
  df2.freq <- Get.Prob.Distribution(df2.norm)
  
  df.freq <- merge(x = df1.freq, y = df2.freq, by = 'Variable', all = TRUE)
  df.freq$Levels.x <- as.numeric(levels(df.freq$Levels.x))[df.freq$Levels.x]
  df.freq$Levels.y <- as.numeric(levels(df.freq$Levels.y))[df.freq$Levels.y]
  
  P.exp <- df.freq %>%
    mutate(Exp = Freq.x * Freq.y * pmin(Levels.x, Levels.y)) %>%
    summarize(sum(Exp)) %>%
    pull() # expected frequencies using t-norm min
  
  Fuzzy.K <- (P.obs - P.exp)/(1 - P.exp)
  return(Fuzzy.K)
}

Get.Norm <- function(df){
  #' normalize rows of dataframe
  #' 
  #' @param df data.frame
  #' 
  #' reuturns data.frame where rows are normalized to sum one
  
  df.norm <- t(apply(df, 1, function (x) x/sum(x)))
  df.norm[is.na(df.norm)] <- 0
  return(df.norm)
}

Get.Prob.Distribution <- function(df){
  #' get observed probability of coding a response
  #' 
  #' @param df data.frame of normalized responses
  #' 
  #' returns data.frame of fraction of times each normalized value appears for each code
  
  df.res = data.frame()
  for(i in 1:ncol(df)){
    df.temp = data.frame(t(table(df[,i])))
    df.temp$Var1 = colnames(df)[i]
    
    
    df.res = rbind(df.res, df.temp)
  }
  # variable is the code, levels are the normalized values (e.g., 0.5 if 2 codes applied, 
  # 0.33 if 3 codes applied), and fre is the fraction of times a normalized value appears
  # for each code for each value
  names(df.res) = c("Variable","Levels","Freq")
  df.res$Freq <- df.res$Freq/nrow(df)

  return(df.res)
}