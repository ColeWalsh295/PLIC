library(dplyr)
library(infotheo)
library(docstring)

MI.vec.to.bits <- function (vec.1, vec.2) {
  
#' Calculates mutual information
#' 
#' Calculates mutual information between two random vectors (or data.frames) using the entropy of the
#' empirical probability distribution
#' 
#' @param vec.1 vector/factor denoting a random variable or a data.frame denoting a random 
#' vector where columns contain variables/features and rows contain outcomes/samples.
#' @param vec.2 another random variable or random vector (vector/factor or data.frame).
#' 
#' returns a single number I(X; Y), the mutual information between random variables (in 
#' units of bits)
  
  MI <- round(natstobits(mutinformation(vec.1, vec.2)), 3)
  return(MI)
}

MI.CI <- function(df.items, vec.scores, reps = 1000, CI.Low = 0.025, CI.High = 0.975,
                  vector = FALSE, samples = 1000) {
  
#' Calculates mutual information with confidennce intervals
#' 
#' Calculates mutual information (and bootstrapped confidence intervals) between item 
#' response choices in a data.frame and a separate vector of factor scores
#' 
#' @param df.items data.frame of item response choices. Mutual information is calculated
#' separately for each item response choice
#' @param vec.scores vector of factor scores used in mutual information calculation for 
#' all features
#' @param reps number of bootstrap replicates
#' @param CI.Low low end of the bootstrap confidence interval
#' @param CI.High high end of the bootstrap confidence interval
#' 
#' returns data.frame containing mutual information between different item response
#' choices and factor score
  
  df.MI <- sapply(df.items, MI.vec.to.bits, vec.2 = vec.scores) %>%
    data.frame(.) %>%
    `colnames<-`(c("MI")) %>%
    mutate(Item = sapply(colnames(df.items), function(x) toupper(x)),
           Prop.Sel = round(colMeans(df.items), 3),
           Question = sapply(Item, function(x) toupper(substr(x, 1, 3)))) %>%
    select(Item, Question, Prop.Sel, MI) %>%
    arrange(desc(MI))
  
  df <- cbind(df.items, vec.scores)
  df.boot <- replicate(reps, df[sample(1:nrow(df), replace = T),], simplify = F)
  if(!vector){
    MI.boot <- sapply(df.boot, function(x) apply(x, 2, MI.vec.to.bits, vec.2 = x[, ncol(x)]))
  } else {
    MI.boot <- sapply(df.boot, function(x) apply(x, 2, MI.vec.to.bits, 
                                                 vec.2 = x[, (ncol(x) - 2):ncol(x)]))
  }
  
  MI.CI <- apply(MI.boot, 1, quantile, probs = c(CI.Low, CI.High))
  MI.CI <- data.frame(t(MI.CI))
  MI.CI$Item <- toupper(row.names(MI.CI))
  
  df.CI <- left_join(df.MI, MI.CI, 'Item')
  colnames(df.CI)[(ncol(df.CI) - 1):ncol(df.CI)] <- c('CI.Low', 'CI.High')
  return(df.CI)
}