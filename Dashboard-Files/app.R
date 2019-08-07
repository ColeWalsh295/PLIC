library(tidyverse)
library(shiny)
library(shinydashboard)
shiny_theme <- theme_classic(base_size = 18)
library(data.table)
library(lavaan)
library(reshape2)
library(rsconnect)
source('PLIC_DataProcessing.R', local = TRUE)
source('PLIC_UI.R', local = TRUE)
source('PLIC_Server.R', local = TRUE)

# Get Complete dataset, remove free response only responses
Header.df <- fread('Headers.csv')

PLIC.Complete.df <- fread('Complete_Concat_DeIdentified.csv')
PLIC.Complete.df$Student.ID.Anon <- row.names(PLIC.Complete.df)
PLIC.Complete.df <- PrePost.Long(PLIC.Complete.df)

PLIC.FR <- PLIC.Complete.df %>%
  filter(Survey == 'F')
PLIC.CR <- PLIC.Complete.df %>%
  filter(Survey == 'C')

# Fit CFA model
PLIC.model.HYP <- ' models  =~ Q1B + Q2B + Q3B + Q3D
                    methods =~ Q1D + Q2D + Q4B
                    actions =~ Q1E + Q2E + Q3E '

mod.cfa.HYP <- cfa(PLIC.model.HYP, data = PLIC.CR, std.lv = TRUE, estimator = 'ML')

scores.df <- data.frame(lavPredict(mod.cfa.HYP))
PLIC.CR <- cbind(PLIC.CR, scores.df) # Merge factor scores back to the dataframe

PLIC.Merged.df <- fread('Complete_Concat_DeIdentified.csv') %>%
  filter(Survey_x == 'C' & Survey_y == 'C')
PLIC.Merged.df$Student.ID.Anon <- row.names(PLIC.Merged.df)
PLIC.Merged.df <- PrePost.Long(PLIC.Merged.df)
scores.df <- data.frame(lavPredict(mod.cfa.HYP, newdata = PLIC.Merged.df))
PLIC.Merged.df <- cbind(PLIC.Merged.df, scores.df) # Merge factor scores back to the dataframe



### Set up the 'View of your class' tab ###

Your_tab = tabItem(
  tabName = "Your_Class",
  h2("View of your class"),
  
  DownloadClassDataUI('Class.Main.Download', label = 'Your Class ID:', value = 'R_2xOT2Y1NtNiseCk'),
  br(),
  ClassStatisticsOutput('Class.Main.Statistics'),
  br(),
  ScalePlotUI('Class.Main.Scale', Demos = TRUE),
  br(),
  QuestionPlotUI('Class.Main.Question', Demos = TRUE),
  br(),
  ResponsesPlotUI('Class.Main.Responses', Demos = TRUE)
)

Compare_tab = tabItem(
  tabName = "Compare_Classes",
  h2("Compare two of your classes"),

  DownloadClassDataUI('Class1.Download', label = 'Your first Class ID:',
                      value = 'R_2xOT2Y1NtNiseCk'),
  br(),
  ClassStatisticsOutput('Class1.Statistics'),
  DownloadClassDataUI('Class2.Download', label = 'Your second Class ID:',
                      value = 'R_RKRNIWFu1gZuSPf'),
  br(),
  ClassStatisticsOutput('Class2.Statistics'),
  br(),
  ScalePlotUI('Class.Compare.Scale', Demos = FALSE),
  br(),
  QuestionPlotUI('Class.Compare.Question', Demos = FALSE),
  br(),
  ResponsesPlotUI('Class.Compare.Responses', Demos = FALSE)
)

Overall_tab = tabItem(
  tabName = "Compare_Overall",
  h2("Compare your classes to other classes"),
  
  DownloadClassDataUI('Class.You.Download', label = 'Your Class ID:',
                      value = 'R_2xOT2Y1NtNiseCk'),
  br(),
  ClassStatisticsOutput('Class.You.Statistics'),
  br(),
  h4("Other classes"),
  ClassStatisticsOutput('Class.Other.Statistics'),
  br(),
  ScalePlotUI('Overall.Compare.Scale', Demos = FALSE),
  br(),
  QuestionPlotUI('Overall.Compare.Question', Demos = FALSE),
  br(),
  ResponsesPlotUI('Overall.Compare.Responses', Demos = FALSE)
)

server = function(input, output) {
  df <- reactive({
    if(input$matched == 'Matched'){
      df <- PLIC.Merged.df
    } else {
      df <- PLIC.CR
    }
    return(df)
  })
  
  ### Your Class ###
  
  PLIC.Class <- callModule(DownloadClassData, 'Class.Main.Download', data = df)
  callModule(ClassStatistics, 'Class.Main.Statistics', data = PLIC.Class)
  demographic <- reactiveVal()
  demographic <- callModule(ScalePlot, 'Class.Main.Scale', data = PLIC.Class)
  callModule(QuestionPlot, 'Class.Main.Question', data = PLIC.Class, Demo = demographic)
  callModule(ResponsesPlot, 'Class.Main.Responses', data = PLIC.Class, Demo = demographic)
  
  ### Compare Classes ###
  
  PLIC.Class1 <- callModule(DownloadClassData, 'Class1.Download', data = df)
  callModule(ClassStatistics, 'Class1.Statistics', data = PLIC.Class1)
  PLIC.Class2 <- callModule(DownloadClassData, 'Class2.Download', data = df)
  callModule(ClassStatistics, 'Class2.Statistics', data = PLIC.Class2)

  PLIC.Compare <- reactive({
    rbind(PLIC.Class1(), PLIC.Class2())
  })
  callModule(ScalePlot, 'Class.Compare.Scale', data = PLIC.Compare, Class.var = 'Class_ID')
  question.compare <- reactiveVal()
  question.compare <- callModule(QuestionPlot, 'Class.Compare.Question', data = PLIC.Compare,
                                 Class.var = 'Class_ID')
  callModule(ResponsesPlot, 'Class.Compare.Responses', data = PLIC.Compare, 
             Question = question.compare, Class.var = 'Class_ID')
  
  ### Compare to overall PLIC dataset ###
  
  PLIC.Class.You_temp <- callModule(DownloadClassData, 'Class.You.Download', data = df)
  callModule(ClassStatistics, 'Class.You.Statistics', data = PLIC.Class.You_temp)
  
  PLIC.Class.You <- reactive({
    PLIC.Class.You <- PLIC.Class.You_temp() %>%
      mutate(Class = 'Your Class')
    return(PLIC.Class.You)
  })
  PLIC.Class.Other <- reactive({
    PLIC.Class.Other <- df()[df()$Class_ID != PLIC.Class.You_temp()$Class_ID[1],] %>%
      mutate(Class = 'Other Classes')
    return(PLIC.Class.Other)
  })
  callModule(ClassStatistics, 'Class.Other.Statistics', data = PLIC.Class.Other, Overall = TRUE)
  
  PLIC.Overall <- reactive({
    rbind(PLIC.Class.You(), PLIC.Class.Other())
  })
  callModule(ScalePlot, 'Overall.Compare.Scale', data = PLIC.Overall, Class.var = 'Class')
  question.overall <- reactiveVal()
  question.overall <- callModule(QuestionPlot, 'Overall.Compare.Question', data = PLIC.Overall,
                                 Class.var = 'Class')
  callModule(ResponsesPlot, 'Overall.Compare.Responses', data = PLIC.Overall, 
             Question = question.overall, Class.var = 'Class')
}

# Set up the Header of the dashboard
dhead = dashboardHeader(title = "PLIC Dashboard")

# Set up the sidebar which links to two pages
dside = dashboardSidebar(sidebarMenu(
  radioButtons('matched', 'Type of Data:', choices = c('Matched', 'All Valid')),
  menuItem("View your class", tabName = "Your_Class", icon = icon("dashboard")),
  menuItem(HTML("Compare two of<br>your classes"), tabName = "Compare_Classes", icon = icon("dashboard")),
  menuItem(HTML("Compare your class<br>to other classes"), tabName = "Compare_Overall", 
           icon = icon("dashboard"))
))

dbody = dashboardBody(
  tags$head(
    tags$link(rel = "stylesheet", type = "text/css",
              href = "Cornell.css")
  ),
  tabItems(Your_tab, Compare_tab, Overall_tab)
)

# Combining header, sidebar, and body
ui = dashboardPage(dhead, dside, dbody)

# Generating a local instance of your dashboard
shinyApp(ui, server)






