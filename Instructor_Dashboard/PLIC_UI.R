# Module UI functions
# corresponding server functions use the same function name with 'UI' removed from the end

DownloadClassDataUI <- function(id, label, value){
  # create textbox for class ID input and download button for class data
  
  # Create a namespace function using the provided id
  ns <- NS(id)

  fluidRow(
    column(4, textInput(ns('classID'), label, value)),
    column(4, br(), downloadButton(ns("downloadData"), "Download"))
  )
}

ClassStatisticsOutput <- function(id){
  # create summary statistics boxes
  
  ns <- NS(id)
  
  fluidRow(
    valueBoxOutput(ns("infoNStudents")),
    infoBoxOutput(ns("infoPREScore")),
    infoBoxOutput(ns("infoPOSTScore"))
  )
}

ScalePlotUI <- function(id, Demos = TRUE){
  # create boxplots of students' scores on selected factors
  
  ns <- NS(id)
  
  if(Demos){
    fluidRow(
      column(4, selectInput(ns("scale"), "Scale:", 
                            choices = c('Evaluating Models', 'Evaluating Methods',
                                        'Suggesting Follow-ups', 'Total Score')),
             br(),
             radioButtons(ns("demographic"), 'Separate by:', 
                          choiceNames = c('None', 'Gender', 'URM Status', 'Major', 
                                          'Class Standing'),
                          choiceValues = c('None', 'Gender', 'URM', 'Major', 
                                           'Class_Standing'))
      ),
      column(8, plotlyOutput(ns("plotScale")))
    )
  } else {
    fluidRow(
      column(4, selectInput(ns("scale"), "Scale:", 
                            choices = c('Evaluating Models', 'Evaluating Methods',
                                        'Suggesting Follow-ups', 'Total Score'))),
      column(8, plotlyOutput(ns("plotScale")))
    )
  }
}

QuestionPlotUI <- function(id, Demos = FALSE){
  # create boxplots of students' scores on selected questions
  
  ns <- NS(id)
  
  if(Demos){
    fluidRow(
      column(12, plotlyOutput(ns("plotQuestion")))
    )
  } else {
    fluidRow(
      column(4, selectInput(ns("question"), "Question:", 
                            choices = c('Q1b', 'Q1d', 'Q1e', 'Q2b', 'Q2d', 'Q2e', 
                                        'Q3b', 'Q3d', 'Q3e', 'Q4b'))),
      column(8, plotlyOutput(ns("plotQuestion")))
    )
  }
}

ResponsesPlotUI <- function(id, Demos = TRUE){
  # create bar plots of fraction of students selecting item response choices on selected
  # questions
  
  ns <- NS(id)
  
  if(!Demos){
    fluidRow(
      column(12, plotlyOutput(ns("plotResponses")))
    )
  } else {
    fluidRow(
      column(2, selectInput(ns("question"), "Question:", 
                            choices = c('Q1b', 'Q1d', 'Q1e', 'Q2b', 'Q2d', 'Q2e', 
                                        'Q3b', 'Q3d', 'Q3e', 'Q4b'))),
      column(10, plotlyOutput(ns("plotResponses")))
    )
  }
}
