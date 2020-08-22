# Module server functions
# corresponding UI functions use the same function name with 'UI' appended to the end

DownloadClassData <- function(input, output, session, data, Type) {
  # retrieves relevant class data based on user input and provides downloadable data to
  # write to .csv

  class.CR <- reactive({
    class.CR <- PLIC.CR[PLIC.CR[, 'Class_ID'] == input$classID,]
    return(class.CR)
  })
  
  data.class <- reactive({
    class.FR <- PLIC.FR[PLIC.FR[, 'Class_ID'] == input$classID,]
    data.class <- bind_rows(class.CR(), class.FR)
    return(data.class)
  })
  
  observe({
    toggleState("downloadData", condition = class.CR()[1, 'Download_Available'])
    # if the data would be identififable if made available, we do not provide it
    # we have received approval to provide identifiable data, so this can be observe({})
    # will be removed in the next update
    if(Type() == 'Matched'){
      if(!class.CR()[1, 'Matched_Available']){
        shinyalert("Oops!", "There are too few students in the matched dataset.", type = "error")
      } else {
        DisableRadio(class.CR, 'Match')
      }
    } else if((Type() == 'All Valid')) {
      if(!class.CR()[1, 'Valid_Available']) {
        shinyalert("Oops!", "There are too few students the overall dataset.", type = "error")
      } else {
        DisableRadio(class.CR, 'Valid')
      }
    }
    })
  
  data.out <- reactive({
    # we put things in long form for plotting, but we put things in wide form to give to
    # instructors
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
    data.out <- data.out %>%
      # demographics only provided if not indentifiable...will be removed in a future version
      mutate(Gender = ifelse(Gender_Available_Download_PRE | Gender_Available_Download_POST, 
                             Gender, NA_character_),
             URM_Status = ifelse(URM_Available_Download_PRE | URM_Available_Download_POST, 
                                 URM_Status, NA_character_),
             Major = ifelse(Major_Available_Download_PRE | Major_Available_Download_POST, 
                            Major, NA_character_),
             Class_Standing = ifelse(Class_Standing_Available_Download_PRE | 
                                       Class_Standing_Available_Download_POST, Class_Standing, NA_character_)) %>%
      select(names(Header.df))
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
    # user input determines if they get matched data or all valid surveys
    if(((Type() == 'Matched') & (class.CR()[1, 'Matched_Available'])) | 
       ((Type() == 'All Valid') & (class.CR()[1, 'Valid_Available']))){
      df.return <- data()[data()[, 'Class_ID'] == input$classID,]
    } else {
      df.return <- data()[0, ]
      df.return[1, ] <- NA
    }
    return(df.return)
  })
  return(df.return)
}

ClassStatistics <- function(input, output, session, data, Overall = FALSE){
  # computes and returns summary statistics for a set of data
  
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
  # plot box plots of students' scores on different dimensions
  
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
    return(reactive(input$demographic)) # return demographic variable to use in later plots
  }
}

QuestionPlot <- function(input, output, session, data, Demo = NULL, Class.var = NULL){
  # make box plots of students' scores on each question
  
  if(!is.null(Demo)){
    Demographic <- reactive({
      Demographic <- Demographitize(Demo())
    })
    Questions.df <- reactive({
      if(Demographic() == 'None'){
        Questions.df <- melt(data()[, c('TimePoint', 'Q1B', 'Q1D', 'Q1E', 'Q2B', 'Q2D', 
                                        'Q2E', 'Q3B', 'Q3D', 'Q3E', 'Q4B')], 
                             id.vars = 'TimePoint')     
      } else {
        Questions.df <- melt(data()[, c('TimePoint', Demographic(), 'Q1B', 'Q1D', 'Q1E', 
                                        'Q2B', 'Q2D', 'Q2E', 'Q3B', 'Q3D', 'Q3E', 'Q4B')], 
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
        labs(x = 'TimePoint', y = 'Score', 
             title = "Compare students' performance by question") +
        scale_color_manual(values = c("#0072b2", "#d55e00", "#009e73", "#cc79a7")) +
        shiny_theme
    })
    return(reactive(input$question))
  }
}

ResponsesPlot <- function(input, output, session, data, Demo = NULL, Question = NULL, 
                          Class.var = NULL){
  # make bar plots of fraction of students selecting each item response choice
  
  if(!is.null(Demo)){
    Demographic <- reactive({
      Demographic <- Demographitize(Demo())
    })
    Responses.df <- reactive({
      if(Demographic() == 'None'){
        Responses.df <- data() %>%
          select(c(grep(paste('^(', input$question, '_[0-9]*$)', sep = ''), names(.))), 
                 'TimePoint') %>% 
          replace(is.na(.), 0) %>%
          group_by(TimePoint) %>%
          summarize_all(funs(mean)) %>%
          melt(.)
      } else {
        Responses.df <- data() %>%
          select(c(grep(paste('^(', input$question, '_[0-9]*$)', sep = ''), names(.))), 
                 'TimePoint', Demographic()) %>% 
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
        select(c(grep(paste('^(', Question(), '_[0-9]*$)', sep = ''), names(.))), 
               Class.var, 
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
  # rename demographic variables to be more readable
  
  Demo <- case_when(demo == 'Gender' ~ 'Gender',
                    demo == 'Major' ~ 'Major',
                    demo == 'URM' ~ 'URM_Status',
                    demo == 'Class_Standing' ~ 'Class_Standing',
                    TRUE ~ 'None')
  return(Demo)
}

DisableRadio <- function(df, Type){
  # legacy; remove in future versions
  # disable particular radio buttons
  
  for(Option in c('Gender', 'URM', 'Major', 'Class_Standing')){
    if(!df()[1, paste(Option, '_Available_', Type, sep = '')]){
      shinyjs::runjs(paste("$('[type = radio][value = ", Option, "]').parent().parent().css('opacity', 0.4)", sep = ''))
      shinyjs::runjs(paste("$('[type = radio][value = ", Option, "]').prop('disabled', true)", sep = ''))
    } else {
      shinyjs::runjs(paste("$('[type = radio][value = ", Option, "]').parent().parent().css('opacity', 1)", sep = ''))
      shinyjs::runjs(paste("$('[type = radio][value = ", Option, "]').prop('disabled', false)", sep = ''))
      }
  }
  return(0)  
}