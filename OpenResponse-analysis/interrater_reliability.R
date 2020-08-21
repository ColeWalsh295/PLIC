library(tidyverse)
library(mc2d)
library(docstring)

FuzzyKappa <- function(df1, df2){
  #' Compute interrater reliability with multiple non-mutually exclusive codes
  #' 
  #' @param df1 first dataframe
  #' @param df2 second dataframe, should have same dimensions as df1
  #'
  #' returns fuzzy kappa inetrrater reliability

  Get.Prob.Distributions <- function(df){
    df.res = data.frame()
    for(i in 1:ncol(df)){
      df.temp = data.frame(t(table(df[,i])))
      df.temp$Var1 = colnames(df)[i]
      
      
      df.res = rbind(df.res, df.temp)
    }
    names(df.res) = c("Variable","Levels","Freq")
    df.res$Freq <- df.res$Freq/nrow(df)
    
    return(df.res)
  }
  
  # normalize each row by sum
  df1.norm <- t(apply(df1, 1, function (x) x/sum(x)))
  df2.norm <- t(apply(df2, 1, function (x) x/sum(x)))
  
  df1.norm[is.na(df1.norm)] <- 0
  df2.norm[is.na(df2.norm)] <- 0
  
  P.obs = sum(mc2d::pmin(df1.norm, df2.norm))/nrow(df1.norm) # observed frequency with t norm min
  
  df1.freq <- Get.Prob.Distributions(df1.norm)
  df2.freq <- Get.Prob.Distributions(df2.norm)
  df.freq <- merge(x = df1.freq, y = df2.freq, by = 'Variable', all = TRUE)
  df.freq$Levels.x <- as.numeric(levels(df.freq$Levels.x))[df.freq$Levels.x]
  df.freq$Levels.y <- as.numeric(levels(df.freq$Levels.y))[df.freq$Levels.y]
  
  P.exp <- df.freq %>%
    mutate(Exp = Freq.x * Freq.y * pmin(Levels.x, Levels.y)) %>%
    summarize(sum(Exp)) %>%
    pull() # expected frequency with t norm min
  
  fuzzy.kappa <- (P.obs - P.exp)/(1 - P.exp) # same definition as Cohen's kappa
  return(fuzzy.kappa)
}