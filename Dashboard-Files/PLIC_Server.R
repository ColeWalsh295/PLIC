DownloadClassData <- function(input, output, session, data) {
  
  class.CR <- reactive({
    class.CR <- PLIC.CR[PLIC.CR[, 'Class_ID'] == input$classID,]
    return(class.CR)
  })
  
  data.class <- reactive({
    class.FR <- PLIC.FR[PLIC.FR[, 'Class_ID'] == input$classID,]
    data.class <- bind_rows(class.CR(), class.FR)
    return(data.class)
  })
  
  data.out <- reactive({
    data.class.pre <- data.class() %>%
      filter(TimePoint == 'PRE') %>%
      select(-c('TimePoint'))
    data.class.post <- data.class() %>%
      filter(TimePoint == 'POST') %>%
      select(-c('TimePoint'))
    data.out <- merge(data.class.pre, data.class.post, by = c('Student.ID.Anon', 'Class_ID', 'Major',
                                                             'Gender', 'URM_Status', 'Class_Standing'), 
                      all = TRUE, suffixes = c('_PRE', '_POST')) %>%
      select(-c('Student.ID.Anon', 'Class_ID'))
    data.out[is.na(data.out)] <- ''
    data.out <- rbind(Header.df, data.out)
    return(data.out)
  })
  
  output$downloadData <- downloadHandler(
    filename = function (){
      paste("PLIC_", input$classID, ".csv", sep = "")
    },
    content = function(file) {
      write.csv(data.out(), file, row.names = FALSE)
    }
  )
  
  df.return <- reactive({
    df.return <- data()[data()[, 'Class_ID'] == input$classID,]
    return(df.return)
  })
  return(df.return)
}

ClassStatistics <- function(input, output, session, data, Overall = FALSE){
  output$infoNStudents <- renderInfoBox({
    infoBox(HTML("Number of<br>Students"),
            length(unique(data()$Student.ID.Anon)),
            icon = icon("list"), color = "purple", width = 12)
  })
  
  output$infoPREScore = renderInfoBox({
    infoBox(HTML("Average<br>PRE-score"),
            data() %>%
              filter(TimePoint == 'PRE') %>%
              summarize(Avg = round(mean(TotalScores), 2)) %>%
              pull(),
            icon = icon("list"), color = "yellow")
  })
  
  output$infoPOSTScore = renderInfoBox({
    infoBox(HTML("Average<br>POST-score"),
            data() %>%
              filter(TimePoint == 'POST') %>%
              summarize(Avg = round(mean(TotalScores), 2)) %>%
              pull(),
            icon = icon("list"), color = "green")
  })
}

ScalePlot <- function(input, output, session, data, Class.var = NULL){
  Scale <- reactive({
    case_when(input$scale == 'Evaluating Models' ~ 'models',
              input$scale == 'Evaluating Methods' ~ 'methods',
              input$scale == 'Suggesting Follow-ups' ~ 'actions',
              input$scale == 'Total Score' ~ 'TotalScores')
  })
  
  output$plotScale = renderPlot({
    if(!is.null(Class.var)){
      p <- ggplot(data(), aes_string(x = 'TimePoint', y = Scale(), color = Class.var)) +
        geom_boxplot() +
        labs(x = '', y = input$scale, title = "Your students' performance") +
        scale_color_manual(values = c("#0072b2", "#d55e00", "#009e73", "#cc79a7")) +
        shiny_theme
    } else {
      Demographic <- reactive({
        Demographic <- Demographitize(input$demographic)
      })
      if(Demographic() != 'None'){
        data.demo <- reactive({
          data.demo <- data()[data()[, Demographic()] != '',]
          return(data.demo)
        })
        p <- ggplot(data.demo(), aes_string(x = Demographic(), y = Scale(), color = 'TimePoint')) +
          geom_boxplot() +
          labs(x = input$demographic, y = input$scale, 
               title = "Your students' performance") +
          scale_color_manual(values = c("#0072b2", "#d55e00", "#009e73", "#cc79a7")) +
          shiny_theme
      } else {
        p <- ggplot(data(), aes_string(y = Scale(), color = 'TimePoint')) +
          geom_boxplot() +
          labs(x = '', y = input$scale, title = "Your students' performance") +
          scale_color_manual(values = c("#0072b2", "#d55e00", "#009e73", "#cc79a7")) +
          shiny_theme + 
          theme(axis.text.x = element_blank(), axis.ticks.x = element_blank())
      }
    }
    return(p)
  })
  if(is.null(Class.var)){
    return(reactive(input$demographic))
  }
}

QuestionPlot <- function(input, output, session, data, Demo = NULL, Class.var = NULL){
  
  if(!is.null(Demo)){
    Demographic <- reactive({
      Demographic <- Demographitize(Demo())
    })
    Questions.df <- reactive({
      if(Demographic() == 'None'){
        Questions.df <- melt(data()[, c('TimePoint', 'Q1B', 'Q1D', 'Q1E', 'Q2B', 'Q2D', 'Q2E', 'Q3B', 
                                        'Q3D', 'Q3E', 'Q4B')], id.vars = 'TimePoint')     
      } else {
        Questions.df <- melt(data()[, c('TimePoint', Demographic(), 'Q1B', 'Q1D', 'Q1E', 'Q2B', 'Q2D', 
                                        'Q2E', 'Q3B', 'Q3D', 'Q3E', 'Q4B')], 
                             id.vars = c('TimePoint', Demographic()))  
        Questions.df <- Questions.df[Questions.df[, Demographic()] != '',]
      }
      return(Questions.df)
    })
    output$plotQuestion = renderPlot({
      p <- ggplot(Questions.df(), aes(x = variable, y = value, color = TimePoint)) +
        geom_boxplot() +
        labs(x = 'Question', y = 'Score', title = "Your students' performance by question") +
        scale_color_manual(values = c("#0072b2", "#d55e00", "#009e73", "#cc79a7")) +
        shiny_theme
      if(Demographic() != 'None'){
        p <- p + facet_wrap(paste('~', Demographic()))
      }
      return(p)
    })
  } else {
    output$plotQuestion = renderPlot({
      ggplot(data(), aes_string(x = 'TimePoint', y = toupper(input$question), 
                                color = Class.var)) +
        geom_boxplot() +
        labs(x = 'TimePoint', y = 'Score', title = "Compare students' performance by question") +
        scale_color_manual(values = c("#0072b2", "#d55e00", "#009e73", "#cc79a7")) +
        shiny_theme
    })
    return(reactive(input$question))
  }
}

ResponsesPlot <- function(input, output, session, data, Demo = NULL, Question = NULL, 
                          Class.var = NULL){
  if(!is.null(Demo)){
    Demographic <- reactive({
      Demographic <- Demographitize(Demo())
    })
    Responses.df <- reactive({
      if(Demographic() == 'None'){
        Responses.df <- data() %>%
          select(c(grep(paste('^(', input$question, '_[0-9]*$)', sep = ''), names(.))), 'TimePoint') %>% 
          replace(is.na(.), 0) %>%
          group_by(TimePoint) %>%
          summarize_all(funs(mean)) %>%
          melt(.)
      } else {
        Responses.df <- data() %>%
          select(c(grep(paste('^(', input$question, '_[0-9]*$)', sep = ''), names(.))), 'TimePoint', Demographic()) %>% 
          replace(is.na(.), 0) %>%
          group_by_('TimePoint', Demographic()) %>%
          summarize_all(funs(mean)) %>%
          melt(.)
        Responses.df <- Responses.df[Responses.df[, Demographic()] != '',]
      }
      return(Responses.df)
    })
    output$plotResponses = renderPlot({
      p <- ggplot(Responses.df(), aes(x = variable, y = value, fill = TimePoint)) +
        geom_bar(stat = 'identity', position = 'dodge') +
        coord_flip() +
        labs(x = 'Response Choice', y = 'Fraction of Students', 
             title = "Your students' response choices") +
        scale_fill_manual(values = c("#0072b2", "#d55e00", "#009e73", "#cc79a7")) +
        shiny_theme
      if(Demographic() != 'None'){
        p <- p + facet_wrap(paste('~', Demographic()))
      }
      return(p)
    })
  } else {
    Responses.df <- reactive({
      Responses.df <- data() %>%
        select(c(grep(paste('^(', Question(), '_[0-9]*$)', sep = ''), names(.))), Class.var, 
               'TimePoint') %>% 
        replace(is.na(.), 0) %>%
        group_by_('TimePoint', Class.var) %>%
        summarize_all(funs(mean)) %>%
        melt(.)
      return(Responses.df)
    })
    output$plotResponses = renderPlot({
      p <- ggplot(Responses.df(), aes_string(x = 'variable', y = 'value', fill = Class.var)) +
        geom_bar(stat = 'identity', position = 'dodge') +
        coord_flip() +
        labs(x = 'Response Choice', y = 'Fraction of Students', 
             title = "Your students' response choices") +
        scale_fill_manual(values = c("#0072b2", "#d55e00", "#009e73", "#cc79a7")) +
        shiny_theme +
        facet_wrap(~TimePoint)
      return(p)
    })
  }
}

Demographitize <- function(demo){
  Demo <- case_when(demo == 'Gender' ~ 'Gender',
                    demo == 'Major' ~ 'Major',
                    demo == 'URM Status' ~ 'URM_Status',
                    demo == 'Class Standing' ~ 'Class_Standing',
                    TRUE ~ 'None')
  return(Demo)
}