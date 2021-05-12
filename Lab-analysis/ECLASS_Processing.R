Read.Score <- function(file){
  dt <- fread(file)
  
  # columns with students responses end in a (student Qs) or b (expert Qs)
  answers.cols <- names(dt)[grep('(a|b)$', names(dt))]
  
  # correct answers marked as 5, incorrect as 1, and neutral as 0
  dt[, (answers.cols) := lapply(.SD, function(x) case_when(x == 5 ~ 1,
                                                           x == 1 ~ -1,
                                                           TRUE ~ 0)),
     .SDcols = answers.cols]
  df <- dt[, -c('q40a', 'q40b')] # q40 was a filter question, no part of scoring
  
  # sum student/expert scores
  df$student.score <- rowSums(df %>% select(grep("a$", names(.))))
  df$expert.score <- rowSums(df %>% select(grep("b$", names(.))))
  
  return(df)
}

Collapse.vars.ECLASS <- function(df){
  df <- df %>%
    mutate(Lab.type = case_when(
    Q33.CIS == 'Reinforce physics concepts.' ~ 'Concepts-based',
    Q33.CIS == 'Both about equally.' ~ 'Mixed',
    Q33.CIS == 'Develop lab skills.' ~ 'Skills-based',
    TRUE ~ NA_character_
  ), 
  Course.level = case_when(
    Q18.CIS == 'Beyond the first year lab' ~ 'BFY',
    (Q27.CIS == 'Calculus-based') | (Q27.CIS == 'Algebra-based') ~ 'FY',
    TRUE ~ NA_character_
  ))
  
  # replace declared major with intended major in cases where students switch
  df[is.na(df$Q48.post) | (df$Q48.post == 0), 
     'Q48.post'] <- df[is.na(df$Q48.post) | (df$Q48.post == 0), 'Q47.post']
  
  df <- df %>%
    mutate(Major = case_when(
      Q48.post == 1 ~ 'Physics',
      Q48.post == 2 ~ 'Chemistry',
      Q48.post == 3 ~ 'Biochemistry',
      Q48.post == 4 ~ 'Biology',
      Q48.post == 5 ~ 'Engineering',
      Q48.post == 6 ~ 'Engineering Physics',
      Q48.post == 7 ~ 'Astronomy',
      Q48.post == 8 ~ 'Astrophysics',
      Q48.post == 9 ~ 'Geology/geophysics',
      Q48.post == 10 ~ 'Math/applied math',
      Q48.post == 11 ~ 'Computer science',
      Q48.post == 12 ~ 'Physiology',
      Q48.post == 13 ~ 'Other science',
      Q48.post == 14 ~ 'Non-science',
      Q48.post == 15 ~ 'Open/undeclared',
      TRUE ~ 'Unknown'
    ),
    Gender = case_when(
      Q54.post == 1 ~ 'Woman',
      Q54.post == 2 ~ 'Man',
      Q54.post == 3 ~ 'Non-binary',
      TRUE ~ 'Unknown'
    )) %>%
    mutate(Major = case_when(
      (Major == 'Physics') | (Major == 'Engineering Physics') | 
        (Major == 'Astronomy') | 
        (Major == 'Astrophysics') ~ 'Physics',
      (Major == 'Chemistry') | (Major == 'Biochemistry') | (Major == 'Biology') | 
        (Major == 'Physiology') ~ 'Chem.LifeSci',
      Major == 'Engineering' ~ 'Engineering',
      (Major == 'Math/applied math') | (Major == 'Computer science') ~ 'Math.CS',
      (Major == 'Geology/geophysics') | (Major == 'Other science') ~ 'Other science',
      Major == 'Non-science' ~ 'NonSci',
      Major == 'Open/undeclared' ~ 'Undeclared',
      Major == 'Unknown' ~ 'Unknown',
      TRUE ~ NA_character_
    )) %>% # set reference levels for factors...important for regressions
    mutate(Major = relevel(as.factor(Major), ref = 'Physics'),
           Gender = relevel(as.factor(Gender), ref = 'Man'),
           Lab.type = relevel(as.factor(Lab.type), ref = 'Concepts-based'))
  
  # rename race columns
  new.race.cols <- c('Race.ethnicity.Other', 'Race.ethnicity.Black', 
                     'Race.ethnicity.Hispanic', 'Race.ethnicity.Asian', 
                     'Race.ethnicity.White', 'Race.ethnicity.unknown',
                     'Race.ethnicity.AmInd', 'Race.ethnicity.NatHawaii')
  setnames(df, old = c('Q52_7.post', 'Q52_3.post', 'Q52_4.post', 
                       'Q52_2.post', 'Q52_6.post', 'race_unknown.post', 
                       'Q52_5.post', 'Q52_1.post'), 
           new = new.race.cols)
  
  df[new.race.cols][is.na(df[new.race.cols])] <- 0
  
  df <- df %>%
    mutate(Race.ethnicity.unknown = case_when(
      Race.ethnicity.unknown == 1 ~ 1,
      Race.ethnicity.Other == 0 & Race.ethnicity.Black == 0 & 
        Race.ethnicity.Hispanic == 0 & Race.ethnicity.Asian == 0 & 
        Race.ethnicity.White == 0 & Race.ethnicity.AmInd == 0 & 
        Race.ethnicity.NatHawaii == 0 ~ 1,
      TRUE ~ 0
    ))
}

rename.vars <- function(df.ECLASS, df.PLIC){
  
  names(df.ECLASS)[names(df.ECLASS) == 'ResponseId.CIS'] <- 'Class_ID'
  names(df.ECLASS)[names(df.ECLASS) == 'student.score.pre'] <- 'PreScores'
  names(df.ECLASS)[names(df.ECLASS) == 'student.score.post'] <- 'PostScores'
  names(df.ECLASS)[names(df.ECLASS) == 'Q15.CIS'] <- 'Institution_type'
  names(df.ECLASS)[names(df.ECLASS) == 'anon_university_id.CIS'] <- 
    'anon_institution_id'
  names(df.ECLASS)[names(df.ECLASS) %like% 'Q34|Q35|Q36|Q37|Q38'] <- 
    names(df.PLIC)[names(df.PLIC) %like% 'Q28|Q29|Q31|Q32|Q33']
  
  return(df.ECLASS)
}

recode.CIS <- function(df){
  df[, names(df) %like% "Q28|Q29|Q31|Q32|Q33"] <- 
    data.frame(lapply(df[, names(df) %like% "Q28|Q29|Q31|Q32|Q33"], 
                      function(x) droplevels(factor(as.vector(x), 
                                                    levels = c('Never', 'Rarely', 
                                                               'Sometimes', 'Often', 
                                                               'Always'), 
                                                    ordered = TRUE))))
  
  df[, names(df) %like% "Q28|Q29|Q31|Q32|Q33"] <- 
    data.frame(lapply(df[, names(df) %like% "Q28|Q29|Q31|Q32|Q33"], 
                      function(x) as.numeric(x)))
  return(df)
}