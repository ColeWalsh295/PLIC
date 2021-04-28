# future version should adopt changes made to the Bio-MAPS dashboard to improve functionality

library(tidyverse)
library(shiny)
library(shinyjs)
library(shinyalert)
library(shinydashboard)
shiny_theme <- theme_classic(base_size = 16)
library(data.table)
library(lavaan)
library(reshape2)
library(rsconnect)
library(plotly)
source('PLIC_DataProcessing.R', local = TRUE)
source('PLIC_UI.R', local = TRUE)
source('PLIC_Server.R', local = TRUE)

Header.df <- read_csv('Headers.csv')

PLIC.Complete.df <- fread('Complete_Concat_CourseInfo_Identified.csv')
PLIC.Complete.df$Student.ID.Anon <- row.names(PLIC.Complete.df)
PLIC.Complete.df <- PrePost.Long(PLIC.Complete.df)

# separate open-response (FR) and closed-response surveys
PLIC.FR <- PLIC.Complete.df %>%
  filter(Survey == 'F')
PLIC.CR <- PLIC.Complete.df %>%
  filter(Survey == 'C')

PLIC.Merged.df <- fread('Complete_Concat_CourseInfo_Identified.csv') %>%
  filter(Survey_PRE == 'C' & Survey_POST == 'C') # separate data.frame for matched surveys
PLIC.Merged.df$Student.ID.Anon <- row.names(PLIC.Merged.df)
PLIC.Merged.df <- PrePost.Long(PLIC.Merged.df)

### UI code ##############################################################################

### Your class tab ###

Your_tab = tabItem(
  tabName = "Your_Class",
  h2("View of your class"),
  
  DownloadClassDataUI('Class.Main.Download', label = 'Your Class ID:', 
                      value = 'R_'),
  br(),
  ClassStatisticsOutput('Class.Main.Statistics'),
  br(),
  ScalePlotUI('Class.Main.Scale', Demos = TRUE),
  br(),
  QuestionPlotUI('Class.Main.Question', Demos = TRUE),
  br(),
  ResponsesPlotUI('Class.Main.Responses', Demos = TRUE)
)

### Compare two of your classes tab ###

Compare_tab = tabItem(
  tabName = "Compare_Classes",
  h2("Compare two of your classes"),

  DownloadClassDataUI('Class1.Download', label = 'Your first Class ID:',
                      value = 'R_'),
  br(),
  ClassStatisticsOutput('Class1.Statistics'),
  DownloadClassDataUI('Class2.Download', label = 'Your second Class ID:',
                      value = 'R_'),
  br(),
  ClassStatisticsOutput('Class2.Statistics'),
  br(),
  ScalePlotUI('Class.Compare.Scale', Demos = FALSE),
  br(),
  QuestionPlotUI('Class.Compare.Question', Demos = FALSE),
  br(),
  ResponsesPlotUI('Class.Compare.Responses', Demos = FALSE)
)

### Compare your class to national dataset tab ###

Overall_tab = tabItem(
  tabName = "Compare_Overall",
  h2("Compare your classes to other classes"),
  
  DownloadClassDataUI('Class.You.Download', label = 'Your Class ID:',
                      value = 'R_'),
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

### Server code ##########################################################################

server = function(input, output) {
  df <- reactive({
    # depending on user input, get matched dataset or full dataset
    # could replace need for two data.frames by adding column denoting matched to PLIC.CR
    if(input$matched == 'Matched'){
      df <- PLIC.Merged.df
    } else {
      df <- PLIC.CR
    }
    return(df)
  })
  
  Data.Include <- reactive({
    # make matching reactive
    Data.Include <- input$matched
    return(Data.Include)
  })
  
  ### Your Class tab ###
  
  CID <- NULL # set initial CID as null, update with input to retain CID between tabs
  PLIC.Class <- callModule(DownloadClassData, 'Class.Main.Download', data = df, 
                           ClassID = CID)
  # Shiny update 1.5.0 introduced moduleServer, which can be used in lieu of 
  # callModule for maintainability
  callModule(ClassStatistics, 'Class.Main.Statistics', data = PLIC.Class)
  # set demographic as reactive to update two plots on this tab simultaneously 
  # with demographic input
  demographic <- reactiveVal()
  demographic <- callModule(ScalePlot, 'Class.Main.Scale', data = PLIC.Class)
  callModule(QuestionPlot, 'Class.Main.Question', data = PLIC.Class, 
             Demo = demographic)
  callModule(ResponsesPlot, 'Class.Main.Responses', data = PLIC.Class, 
             Demo = demographic)
  
  ### Compare Classes tab ###
  
  PLIC.Class1 <- callModule(DownloadClassData, 'Class1.Download', data = df, 
                            ClassID = CID)
  callModule(ClassStatistics, 'Class1.Statistics', data = PLIC.Class1)
  PLIC.Class2 <- callModule(DownloadClassData, 'Class2.Download', data = df)
  callModule(ClassStatistics, 'Class2.Statistics', data = PLIC.Class2)

  PLIC.Compare <- reactive({
    rbind(PLIC.Class1(), PLIC.Class2())
  })
  callModule(ScalePlot, 'Class.Compare.Scale', data = PLIC.Compare, 
             Class.var = 'Class_ID')
  question.compare <- reactiveVal()
  question.compare <- callModule(QuestionPlot, 'Class.Compare.Question', 
                                 data = PLIC.Compare,
                                 Class.var = 'Class_ID')
  callModule(ResponsesPlot, 'Class.Compare.Responses', data = PLIC.Compare, 
             Question = question.compare, Class.var = 'Class_ID')
  
  ### Compare your class to national dataset tab ###
  
  PLIC.Class.You_temp <- callModule(DownloadClassData, 'Class.You.Download', 
                                    data = df, ClassID = CID)
  CID <- reactive({
    # update CID with input from each tab...this reactive variable ensures that text input
    # on one tab carries over to subsequent tabs so instructors don't have to re-type IDs
    if(input$tabs == 'Your_Class'){
      CID <- PLIC.Class()[1, 'Class_ID']
    } else if(input$tabs == 'Compare_Classes'){
      CID <- PLIC.Class1()[1, 'Class_ID']
    } else {
      CID <- PLIC.Class.You_temp()[1, 'Class_ID']
    }
    return(CID)
  })
  callModule(ClassStatistics, 'Class.You.Statistics', data = PLIC.Class.You_temp)
  
  PLIC.Class.You <- reactive({
    PLIC.Class.You <- PLIC.Class.You_temp() %>%
      mutate(Class = 'Your Class') # add a column separating YOUR class from other classes
    return(PLIC.Class.You)
  })
  PLIC.Class.Other <- reactive({
    PLIC.Class.Other <- df()[df()$Class_ID != PLIC.Class.You_temp()$Class_ID[1],] %>%
      mutate(Class = 'Other Classes')
    return(PLIC.Class.Other)
  })
  callModule(ClassStatistics, 'Class.Other.Statistics', data = PLIC.Class.Other, 
             Overall = TRUE)
  
  PLIC.Overall <- reactive({
    rbind(PLIC.Class.You(), PLIC.Class.Other())
  })
  callModule(ScalePlot, 'Overall.Compare.Scale', data = PLIC.Overall, Class.var = 'Class')
  question.overall <- reactiveVal()
  question.overall <- callModule(QuestionPlot, 'Overall.Compare.Question', 
                                 data = PLIC.Overall,
                                 Class.var = 'Class')
  callModule(ResponsesPlot, 'Overall.Compare.Responses', data = PLIC.Overall, 
             Question = question.overall, Class.var = 'Class')
}

##########################################################################################

dhead = dashboardHeader(title = "PLIC Dashboard")

dside = dashboardSidebar(sidebarMenu(
  id = 'tabs',
  radioButtons('matched', 'Type of Data:', choices = c('Matched', 'All Valid')),
  menuItem("View your class", tabName = "Your_Class", icon = icon("dashboard")),
  menuItem(HTML("Compare two of<br>your classes"), tabName = "Compare_Classes", 
           icon = icon("dashboard")),
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

ui = tagList(useShinyjs(), useShinyalert(), dashboardPage(dhead, dside, dbody))

shinyApp(ui, server)






