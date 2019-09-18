library(tidyverse)
library(mc2d)

Fuzzy.Kappa <- function(df1, df2){
  
  df1.norm <- Get.Norm(df1)
  df2.norm <- Get.Norm(df2)
  P.obs <- sum(mc2d::pmin(df1.norm, df2.norm))/nrow(df1)
  
  df1.freq <- Get.Prob.Distribution(df1.norm)
  df2.freq <- Get.Prob.Distribution(df2.norm)
  
  df.freq <- merge(x = df1.freq, y = df2.freq, by = 'Variable', all = TRUE)
  df.freq$Levels.x <- as.numeric(levels(df.freq$Levels.x))[df.freq$Levels.x]
  df.freq$Levels.y <- as.numeric(levels(df.freq$Levels.y))[df.freq$Levels.y]
  
  P.exp <- df.freq %>%
    mutate(Exp = Freq.x * Freq.y * pmin(Levels.x, Levels.y)) %>%
    summarize(sum(Exp)) %>%
    pull()
  
  Fuzzy.K <- (P.obs - P.exp)/(1 - P.exp)
  return(Fuzzy.K)
}

Get.Norm <- function(df){
  df.norm <- t(apply(df, 1, function (x) x/sum(x)))
  df.norm[is.na(df.norm)] <- 0
  return(df.norm)
}

Get.Prob.Distribution <- function(df){
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