library(plyr)
library(MASS)
library(readr)
library(tidyverse)
library(ryouready)
library(nnet)
library(ggthemes)
library(reshape2)
library(ggstatsplot)
library(MRCV)
library(DescTools)
library(plotly)
library(lmerTest)
library(survival)
library(survminer)
library(gridExtra)
library(ggpubr)
library(colorRamps)
library(docstring)
if(file.exists('PLIC_DataProcessing.R'))
  source('PLIC_DataProcessing.R')
theme_set(theme_classic(base_size = 12))
palette.4 <- c('#9F0162', '#009F81', '#008DF9', '#FF6E3A')

make.master.PLIC <- function(file.path){

  files = list.files(file.path, recursive = TRUE, full.names = TRUE)
  
  read.classID.csv <- function(file){
    # function to read file and assign class ID based on file name
    df <- read.csv(file, header = T, skip = 1)
    
    if(nrow(df) > 0){
      split.filename <- strsplit(file, '/')[[1]]
      file.end <- split.filename[length(split.filename)]
      
      split.file.end <- strsplit(file.end, '_')[[1]]
      class.ID <- split.file.end[length(split.file.end) - 1]
      time <- split.file.end[length(split.file.end) - 3]
      
      df$Time <- time
      df$Class.ID <- paste('R_', class.ID, sep = '')
    }
    
    return(df)
  }
  
  # header row with column names
  header = read.csv(files[1], header = F, nrows = 1, as.is = T)
  df = ldply(files, read.classID.csv) %>%
    `colnames<-`(c(header, 'Time', 'Class.ID')) %>%
    filter(V5 == 1) %>% # finished
    filter((Qt1_3 > 30) | (Qt2_3 > 30) | (Qt3_3 > 30) | (Qt4_3 > 30) | (`Q338_Page Submit` > 30) | (`Q351_Page Submit` > 30)) #timing
  df <- df[df[, 'Unnamed: 7'] == 1,] # consent
  
  # collapse gender/race/ethncity/major variables
  df <- Collapse.vars(df, matched = FALSE)
  
  # 4 conditions, 2x2; Likert means the student received Likert items on the first
  # three pages, None means they did not. 1/2 refers to which group the student saw 
  # first
  
  # merge CIS data
  CIS.df <- read.csv('C:/Users/Cole/Documents/DATA/PLIC_DATA/Course_Information_Survey_filled.csv')[-1,] %>%
    select(V1, Q4, Q6, Q7, Q19, Q27) %>%
    `colnames<-`(c('Class.ID', 'School', 'Course.Number', 'Course.Level', 
                   'Institution.cat', 'Lab.type'))
  
  df <- merge(df, CIS.df, by = 'Class.ID', all.x = TRUE)

  # rename a couple courses to be consistent
  df <- df %>%
    mutate(Course.Number = case_when(
      Course.Number == "PHY 121 Section 0001" | 
        Course.Number == "PHY 121 Section 0002" ~ "PHY 121",
      TRUE ~ Course.Number))
  
  df <- df %>%
    mutate(Class.standing = case_when(
      Q6a == 1 ~ 'Freshman',
      Q6a == 2 ~ 'Sophomore',
      Q6a == 3 ~ 'Junior',
      Q6a == 4 ~ 'Senior',
      Q6a == 5 ~ 'Grad',
      Q6a == 8 ~ 'Other',
      TRUE ~ 'Unknown'
    ),
    Course.Level = case_when(
      Course.Level == 6 ~ 'High School',
      Course.Level == 1 ~ 'Intro (alebgra)',
      Course.Level == 2 ~ 'Intro (calculus)',
      Course.Level == 3 ~ 'Sophomore',
      Course.Level == 4 ~ 'Junior',
      Course.Level == 5 ~ 'Senior',
      Course.Level == 7 ~ 'Graduate'
    ))
  write.csv(df, 'AB_analysis_data.csv', row.names = FALSE)
}

recode.compare <- function(df, simple = FALSE){
  if(simple){
    df <- df %>%
      mutate(Comparison = case_when(
        Comparison == 1 ~ '1',
        Comparison == 2 ~ '2',
        Comparison == 3 ~ 'B',
        Comparison == 4 ~ 'N',
        TRUE ~ NA_character_
      ))
  } else {
    df <- df %>%
      mutate(Comparison = case_when(
        Comparison == 1 ~ 'Group 1',
        Comparison == 2 ~ 'Group 2',
        Comparison == 3 ~ 'Both groups',
        Comparison == 4 ~ 'Neither group',
        TRUE ~ NA_character_
      ))
  }
  return(df)
}

get.Likert.compare <- function(df, Likert.comparison.items, All = FALSE, 
                               compare = FALSE, condition = NULL){
  
  Likert.compare.summary <- function(df, Group1, Group2, Question, summary = TRUE, 
                                     Compare = NULL, Condition = NULL){
    cols.vec <- c(Group1, Group2)
    names.vec <- c('Group.1', 'Group.2')
    if(!is.null(Compare)){
      cols.vec <- c(cols.vec, Compare)
      names.vec <- c(names.vec, 'Comparison')
    }
    if(!is.null(Condition)){
      cols.vec <- c(cols.vec, Condition)
      names.vec <- c(names.vec, 'Condition')
    }
    df.temp <- df[, cols.vec]
    colnames(df.temp) <- names.vec
    
    df.temp$Group.1 <- as.numeric(df.temp$Group.1)
    df.temp$Group.2 <- as.numeric(df.temp$Group.2)
    
    if(summary){
      df.summary <- group_by_all(df.temp) %>%
        summarize(N = n())
    } else {
      df.summary <- df.temp
    }
    
    df.summary[, 'Aspect'] <- Question
    return(df.summary)
  }
  
  if(!compare){
    df <- 
      rbind.fill(lapply(Likert.comparison.items,  
                        function(x) Likert.compare.summary(df = df,
                                                           Group1 = x[[1]], 
                                                           Group2 = x[[2]],
                                                           Question = x[[4]],
                                                           Condition = condition)))
  } else {
    df <- 
      rbind.fill(lapply(Likert.comparison.items,  
                        function(x) Likert.compare.summary(df = df,
                                                           Group1 = x[[1]], 
                                                           Group2 = x[[2]],
                                                           Compare = x[[3]], 
                                                           Question = x[[4]],
                                                           Condition = condition)))
  }

  if(All){
    df.total <- df %>%
      group_by(Group.1, Group.2, Comparison) %>%
      summarize(N = sum(N)) %>%
      mutate(Aspect = 'All')
    return(df.total)
  } else {
    return(df)
  }
  
}
  
beachball.plot <- function(df, Likert.comparison.items, Which = 'All', 
                           scale = FALSE, max.rad = 0.4, compare.palette = palette.4){
  
  make.pie <- function(df, g1, g2, scale = scale){
    df.pie <- df %>%
      filter(Group.1 == g1 & Group.2 == g2)
    if(dim(df.pie)[1] == 0){
      p <- ggplot(df, aes(x = Group.1, y = Group.2, fill = Comparison)) +
        geom_blank() +
        theme_void()
    } else {
      p <- ggplot(df.pie, 
                  aes(x = '', y = N, fill = Comparison)) +
        geom_bar(width = 1, stat = 'identity') +
        scale_fill_manual(values = compare.palette) +
        coord_polar('y', start = 0) +
        theme_void() +
        theme(legend.position = 'none')
    }
    
    if(scale){
      total <- sum(df.pie$N)
      return(list(g1, g2, p, total))
    } else {
      return(list(g1, g2, p))
    }
  }
  
  add.pie <- function(p, p.new, x, y, area.ratio = 1, max.rad = max.rad){
    radius <- max.rad * sqrt(area.ratio)
    p <- p +
      annotation_custom(ggplotGrob(p.new), xmin = (x - radius), xmax = (x + radius),
                        ymin = (y - radius), ymax = (y + radius))
    return(p)
  }
  
  get_legend <- function(myggplot){
    # from http://www.sthda.com/english/wiki/wiki.php?id_contents=7930
    tmp <- ggplot_gtable(ggplot_build(myggplot))
    leg <- which(sapply(tmp$grobs, function(x) x$name) == "guide-box")
    legend <- tmp$grobs[[leg]]
    return(legend)
  }
  
  if(Which == 'All'){
    df.Likert.compare <- get.Likert.compare(df, Likert.comparison.items, All = TRUE,
                                            compare = TRUE)
  } else if(length(Which) > 1){
    Likert.comparison.items <- 
      Likert.comparison.items[which(sapply(Likert.comparison.items, `[[`, 4) %in% 
                                      Which)]
    df.Likert.compare <- get.Likert.compare(df, Likert.comparison.items, All = TRUE, 
                                            compare = TRUE)
  } else {
    df.Likert.compare <- get.Likert.compare(df, Likert.comparison.items, 
                                            All = FALSE, compare = TRUE) %>%
      filter(Aspect == Which)
  }
  df.Likert.compare <- df.Likert.compare %>%
    filter(!is.na(Group.1) & !is.na(Group.2) & (Comparison != ''))
  
  max.N <- df.Likert.compare %>%
    group_by(Group.1, Group.2) %>%
    summarize(N = sum(N)) %>%
    ungroup() %>%
    summarize(max(N)) %>%
    pull()
  
  df.Likert.compare$N <- df.Likert.compare$N/max.N
  df.Likert.compare <- recode.compare(df.Likert.compare)
  names(compare.palette) <- levels(as.factor(df.Likert.compare$Comparison))
  
  p <- ggplot(df.Likert.compare, aes(x = Group.1, y = Group.2, fill = Comparison)) +
    geom_blank()
  
  p.list <- apply(expand.grid(1:4, 1:4), 1, 
                  function(x) make.pie(df.Likert.compare, x['Var1'][[1]], 
                                       x['Var2'][[1]], scale = scale))
  
  for(l in p.list){
    if(scale){
      p <- add.pie(p, l[[3]], l[[1]], l[[2]], l[[4]], max.rad)
    } else {
      p <- add.pie(p, l[[3]], l[[1]], l[[2]], max.rad = max.rad)
    }
  }
  
  leg <- ggpubr::get_legend(ggplot(df.Likert.compare, 
                                   aes(x = '', y = N, fill = Comparison)) +
                              geom_bar(width = 1, stat = 'identity') +
                              scale_fill_manual(values = compare.palette) +
                              theme(legend.position = 'top'))
  
  p <- p +
    xlim(0.75, 4.25) +
    ylim(0.75, 4.25) +
    labs(x = 'Group 1', y = 'Group 2')
  
  fig <- grid.arrange(as_ggplot(leg), arrangeGrob(p), nrow = 2, heights = c(1, 10))
  return(fig)
}

quilt.plot <- function(df, Likert.comparison.items, palette = heat.colors, 
                       legend = FALSE, margin = c(2, 8, 0, 4), 
                       type = 'hatched', scale = 'min', 
                       panels = c('Group.1', 'Group.2', 'Comparison'), Condition = NULL,
                       panel.labels = NULL, legend.extremes = NULL){
  #' Make Quilt plot
  #' 
  #' Create a quilt plot of Likert items and Comparison items with grouping by
  #' two separate conditions
  #' 
  #' @param df Dataframe in wide form --- one row per student
  #' @param Likert.comparison.items List of lists. Each sublist should contain 
  #' (in order) column names for a Group 1 Likert item, a Group 2 Likert item,
  #' a corresponding Comparison item, and a name for this group of items 
  #' (4 strings per sublist).
  #' @param Condition Name of column denoting which condition a student belonged to
  #' @param palette A continuous colour palette for mapping. Can be any color map
  #' from grDevices or color Ramps. See https://www.nceas.ucsb.edu/sites/default/files/2020-04/colorPaletteCheatsheet.pdf
  #' for availiable color maps.
  #' @param legend Binary; whether to include a legend in the plot
  #' @param margin Amount of space to leave in the margin around the plot. Four element 
  #' vector with spaces around the plot at the (bottom, left, top, right). Increase
  #' numbers in corresponding element to increase space for labels
  #' @param type Type of plot to make. Acceptable values: 'aggregate', hatched', 
  #' 'difference', 'side-by-side'. Aggregate plots do not differentiate students along any
  #' condition. Side-by-side plots can only be made when plotting Comparison panel
  #' alone.
  #' @param scale Range of color bar to plot values. Acceptable values: 'min' to use
  #' the minimum and maximum values in the dataset as bounds providing full saturation.
  #' 'full' uses the maximum range the values could hypothetically take on. Or the user
  #' can provide a vector of length 2 specifying the lower and upper bound, respectively.
  #' @param panels Vector of which panels to plot. Default is all panels.
  #' @param panel.labels Character or vector of labels to plot above panels.
  #' @param legend.extremes Only used with difference plots. Character strings to plot at
  #' opposite ends of the scale bar.
  #' 
  #' Prints a plot object
  
  frac.selected <- function(df, by, condition){
    if(!is.null(condition)){
      df <- df %>%
        filter(!is.na(get(by))) %>%
        group_by(get(by), get(condition), Aspect) %>%
        summarize(N = sum(N)) %>%
        ungroup(.) %>%
        `colnames<-`(c('Selection', 'Condition', 'Aspect', 'N')) %>%
        group_by(Condition, Aspect) %>%
        mutate(frac = N/sum(N),
               Item = by)
    } else {
      df <- df %>%
        filter(!is.na(get(by))) %>%
        group_by(get(by), Aspect) %>%
        summarize(N = sum(N)) %>%
        ungroup(.) %>%
        `colnames<-`(c('Selection', 'Aspect', 'N')) %>%
        group_by(Aspect) %>%
        mutate(frac = N/sum(N),
               Item = by)
    }
    return(df)
  }
  
  if(type == 'aggregate'){
    print('Aggregated plots cannot take a condition. Setting Condition to NULL.')
    Condition <- NULL
  }
  
  df <- get.Likert.compare(df, Likert.comparison.items, compare = TRUE, 
                           condition = Condition)

  df <- rbind.fill(lapply(c('Group.1', 'Group.2', 'Comparison'), 
                          function (x) frac.selected(df, x, 
                                                     condition = Condition))) %>%
    mutate(x = 5 * (as.integer(factor(Item, levels = c('Group.1', 'Group.2', 
                                                       'Comparison'))) - 1) + 
             as.integer(Selection),
           y = as.integer(as.factor(Aspect)),
           Selection = case_when(
             Item == 'Comparison' & Selection == 1 ~ '1',
             Item == 'Comparison' & Selection == 2 ~ '2',
             Item == 'Comparison' & Selection == 3 ~ 'B',
             Item == 'Comparison' & Selection == 4 ~ 'N',
             TRUE ~ as.character(Selection)))
  
  if(!is.null(Condition)){
    df$Condition <- factor(df$Condition)
    conditions <- levels(df$Condition)
  }
  
  ncols <- 1000
  pal <- palette(ncols)
  n.panels <- length(panels)
  
   if(type == 'difference'){
    df <- inner_join(df %>%
                       filter(Condition == conditions[1]), 
                     df %>%
                       filter(Condition == conditions[2]),
                     by = c('Selection','Aspect', 'Item', 'x', 'y'), 
                     suffix = c('.1', '.2')) %>%
      mutate(diff = frac.2 - frac.1)
    if(length(scale) == 2){
      min.scale <- scale[1]
      max.scale <- scale[2]
    } else if(length(scale) == 1){
      min.scale <- ifelse(scale == 'full', -1, min(df$diff))
      max.scale <- ifelse(scale == 'full', 1, max(df$diff))
    } else {
      stop('Invalid scale argument')
    }
   } else {
     if(type == 'side-by-side'){
       if((n.panels != 1) | (panels[1] != 'Comparison')){
         print('Too many panels for side-by-side plot; only plotting comparison items')
         panels <- 'Comparison'
       }
       n.panels <- 2
       if(is.null(panel.labels)){
         panel.labels <- c(conditions[1], conditions[2])
       }
     }
     if(length(scale) == 2){
       min.scale <- scale[1]
       max.scale <- scale[2]
     } else if(length(scale) == 1){
       min.scale <- ifelse(scale == 'full', 0, min(df$frac))
       max.scale <- ifelse(scale == 'full', 1, max(df$frac))
     } else {
       stop('Invalid scale argument')
     }
   }
  
  if(n.panels < 3){
    df <- df %>%
      filter(Item %in% panels)
    vec <- c(1, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14)
    if(type == 'side-by-side'){
      df <- df %>%
        mutate(x = x + ifelse(Condition == conditions[1], 0, 4))
    }
    new.vec <- vec[1:length(unique(df$x))]
    df$x <- new.vec[match(df$x, sort(unique(df$x)))]
  }
  
  a <- ncols/(max.scale - min.scale) - 0.5
  b <- (min.scale * ncols)/(min.scale - max.scale) + 0.5
  
  max.x <- max(df$x)
  max.y <- max(df$y)
  par(mar = margin)

  if(legend){
    plot(1, xlim = c(1, max.x + 1), ylim = c(1, max.y + 8), type = "n",
         bty = "n", xaxt = "n", yaxt = "n", xlab = "", ylab = "")
    if(type == 'hatched'){
      text(x = seq(2 * n.panels + 0.1, max.x + 1, l = 5), y = max.y + 7, 
           labels = round(seq(floor(min.scale * 100)/100, ceiling(max.scale * 100)/100, 
                              l = 5), 2))
      rasterImage(as.raster(matrix(pal, nrow = 1)), 2 * n.panels + 0.1, max.y + 4, 
                  max.x + 1, max.y + 6)
      polygon(1 + c(0, n.panels - 0.1, n.panels - 0.1), max.y + 4 + c(0, 0, 3), 
              col = gray(0.75))
      polygon(1 + c(0, n.panels - 0.1, 0), max.y + 4 + c(0, 3, 3), col = gray(0.25))
      text(x = n.panels + 0.9, y = max.y + 4.5, labels = conditions[1], pos = 2, 
           col = gray(0))
      text(x = 1, y = max.y + 6.25, labels = conditions[2], pos = 4, col = gray(1))
      text(x = (2 * n.panels + max.x + 1)/2, y = max.y + 8, 
           labels = 'Fraction of students')
    } else {
      text(x = seq(1, max.x + 1, l = 5), y = max.y + 7, 
           labels = round(seq(floor(min.scale * 100)/100, ceiling(max.scale * 100)/100, 
                              l = 5), 2))
      rasterImage(as.raster(matrix(pal, nrow = 1)), 1, max.y + 4, max.x + 1, max.y + 6)
      text(x = (max.x + 2)/2, y = max.y + 8, 
           labels = ifelse(type == 'difference', 'Difference in fraction of students', 
                           'Fraction of students'))
      if(type == 'difference'){
        par(xpd = TRUE)
        text(x = 1, y = max.y + 5,
             labels = ifelse(is.null(legend.extremes), paste(conditions[1], '\nlarger',
                                                             sep = ''),
                             legend.extremes[1]), pos = 2)
        text(x = max.x + 1, y = max.y + 5,
             labels = ifelse(is.null(legend.extremes), paste(conditions[2], '\nlarger',
                                                             sep = ''),
                             legend.extremes[2]), pos = 4)
      } 
    }
  } else {
    plot(1, xlim = c(1, max.x + 1), ylim = c(1, max.y + 3), type = "n", 
         bty = "n", xaxt = "n", yaxt = "n", xlab = "", ylab = "")
  }
  
  if(type == 'hatched'){
    for(i in 1:nrow(df)) {
      if(df$Condition[i] == conditions[1]) polygon(df$x[i] + c(0, 1, 1), 
                                                   df$y[i] + c(0, 0, 1), 
                                                   col = pal[round(a * df$frac[i] + b)])
      if(df$Condition[i] == conditions[2]) polygon(df$x[i] + c(0, 1, 0), 
                                                   df$y[i] + c(0, 1, 1), 
                                                   col = pal[round(a * df$frac[i] + b)])
    }
  } else if(type == 'difference'){
    for(i in 1:nrow(df)) {
      polygon(df$x[i] + c(0, 0, 1, 1), df$y[i] + c(0, 1, 1, 0), 
              col = pal[round(a * df$diff[i] + b)])
    }
  } else {
    for(i in 1:nrow(df)) {
      polygon(df$x[i] + c(0, 0, 1, 1), df$y[i] + c(0, 1, 1, 0), 
              col = pal[round(a * df$frac[i] + b)])
    }
  }
  
  axis(1, at = sort(unique(df$x)) + 0.5, 
       labels = df[!duplicated(df$x), c('x', 'Selection')] %>%
         arrange(x) %>%
         .$Selection, lty = 0)
  text(x = par('usr')[1], y = 1:max.y + 0.5, labels = df[!duplicated(df$y), 
                                                         c('y', 'Aspect')] %>%
         arrange(y) %>%
         .$Aspect, xpd = NA, srt = 0, adj = 1)
  text(x = 3, y = max.y + 2.5, labels = panel.labels[1])
  if(n.panels > 1){
    text(x = 8, y = max.y + 2.5, labels = panel.labels[2])
    if(n.panels > 2){
      text(x = 13, y = max.y + 2.5, labels = panel.labels[3])
    }
  }
}
