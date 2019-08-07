DownloadClassDataUI <- function(id, label, value){
  # Create a namespace function using the provided id
  ns <- NS(id)

  fluidRow(
    column(4, textInput(ns('classID'), label, value)),
    column(4, br(), downloadButton(ns("downloadData"), "Download"))
  )
}

ClassStatisticsOutput <- function(id){
  ns <- NS(id)
  
  fluidRow(
    valueBoxOutput(ns("infoNStudents")),
    infoBoxOutput(ns("infoPREScore")),
    infoBoxOutput(ns("infoPOSTScore"))
  )
}

ScalePlotUI <- function(id, Demos = TRUE){
  ns <- NS(id)
  
  if(Demos){
    fluidRow(
      column(4, selectInput(ns("scale"), "Scale:", 
                            choices = c('Evaluating Models', 'Evaluating Methods',
                                        'Suggesting Follow-ups', 'Total Score')),
             br(),
             radioButtons(ns("demographic"), 'Separate by:', 
                          choices = c('None', 'Gender', 'URM Status', 'Major', 'Class Standing'))
      ),
      column(8, plotOutput(ns("plotScale")))
    )
  } else {
    fluidRow(
      column(4, selectInput(ns("scale"), "Scale:", 
                            choices = c('Evaluating Models', 'Evaluating Methods',
                                        'Suggesting Follow-ups', 'Total Score'))),
      column(8, plotOutput(ns("plotScale")))
    )
  }
}

QuestionPlotUI <- function(id, Demos = FALSE){
  ns <- NS(id)
  
  if(Demos){
    fluidRow(
      column(12, plotOutput(ns("plotQuestion")))
    )
  } else {
    fluidRow(
      column(4, selectInput(ns("question"), "Question:", 
                            choices = c('Q1b', 'Q1d', 'Q1e', 'Q2b', 'Q2d', 'Q2e', 
                                        'Q3b', 'Q3d', 'Q3e', 'Q4b'))),
      column(8, plotOutput(ns("plotQuestion")))
    )
  }
}

ResponsesPlotUI <- function(id, Demos = TRUE){
  ns <- NS(id)
  
  if(!Demos){
    fluidRow(
      column(12, plotOutput(ns("plotResponses")))
    )
  } else {
    fluidRow(
      column(2, selectInput(ns("question"), "Question:", 
                            choices = c('Q1b', 'Q1d', 'Q1e', 'Q2b', 'Q2d', 'Q2e', 
                                        'Q3b', 'Q3d', 'Q3e', 'Q4b'))),
      column(10, plotOutput(ns("plotResponses")))
    )
  }
}
