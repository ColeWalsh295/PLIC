#### Multiple imputation analysis

##### Setup imputation
```{r, eval = FALSE, message=FALSE, warning=FALSE, results='hide'}
set.seed(11)
df.subset <- complete.df[, names(complete.df) %like% 'Race|Gender|Major|student.score|ResponseId.CIS|anon_university_id|Lab.type']
variables_levels <- miceadds:::mice_imputation_create_type_vector( colnames(df.subset), value="")

predmat <- mice::make.predictorMatrix(data = df.subset)
method <- mice::make.method(data = df.subset)

levels_id <- list()
levels_id[["students.score.pre"]] <- c('ResponseId.CIS', 'anon_university_id')
levels_id[["students.score.post"]] <- c('ResponseId.CIS', 'anon_university_id')

imp1 <- mice::mice(df.subset, maxit = 10, m = 5, method = method,
                   predictorMatrix = predmat, levels_id = levels_id, 
                   variables_levels=variables_levels, printFlag = FALSE)
```

##### Make p1 imputed figure
```{r, eval = FALSE}
predictions <- lapply(1:5, function(i) {
  m <- lmer(student.score.post ~ student.score.pre + Lab.type * 
              (Gender + Race.ethnicity.AmInd + Race.ethnicity.NatHawaii + 
                 Race.ethnicity.Other + Race.ethnicity.Black +
                 Race.ethnicity.Hispanic + Race.ethnicity.Asian + 
                 Race.ethnicity.White + Race.ethnicity.Unknown) + 
              Major + (1 | anon_university_id.CIS/ResponseId.CIS), data = complete(imp1, action = i))
  ggpredict(m, "Lab.type", ci.lvl = 0.67)
})
preds.lab <- pool_predictions(predictions)

p1.imp <- ggplot(data.frame(preds.lab), aes(x = factor(x), y = predicted, 
                                            color = factor(x))) +
  geom_point(size = 2) +
  geom_errorbar(aes(ymin = conf.low, ymax = conf.high), size = 1, width = 0,
                position = position_dodge(width = 0.5)) +
  scale_x_discrete(labels = c('Concepts-based', 'Mixed', 'Skills-based')) +
  scale_color_manual(values = c('#e69f00', '#009e74', '#0071b2')) +
  labs(x = 'Lab type', y = 'Expected E-CLASS\nposttest scores') +
  theme(axis.text.x = element_text(angle = 40, vjust = 1, hjust = 1),
        legend.position = 'none')
```

##### Make p2 imputed figure
```{r, eval = FALSE}
predictions <- lapply(1:5, function(i) {
  m <- lmer(student.score.post ~ student.score.pre + Lab.type * 
              (Gender + Race.ethnicity.AmInd + Race.ethnicity.NatHawaii + 
                 Race.ethnicity.Other + Race.ethnicity.Black +
                 Race.ethnicity.Hispanic + Race.ethnicity.Asian + 
                 Race.ethnicity.White + Race.ethnicity.Unknown) + 
              Major + (1 | anon_university_id.CIS/ResponseId.CIS), data = complete(imp1, action = i))
  ggpredict(m, c("Lab.type", "Gender"), ci.lvl = 0.67)
})
preds.gender <- pool_predictions(predictions)

p2.imp <- ggplot(data.frame(preds.gender), aes(x = factor(group), y = predicted,
                                               color = factor(x), 
                                               group = factor(x))) +
  geom_point(size = 2, position = position_dodge(width = 0.5)) +
  geom_errorbar(aes(ymin = conf.low, ymax = conf.high), size = 1, width = 0,
                position = position_dodge(width = 0.5)) +
  scale_color_manual(values = c('#e69f00', '#009e74', '#0071b2')) +
  labs(x = 'Gender', y = 'Expected E-CLASS\nposttest scores') +
  theme(axis.text.x = element_text(angle = 40, vjust = 1, hjust = 1),
        legend.position = 'none') +
  scale_x_discrete(labels = c('Man', 'Non-binary', 'Unknown', 'Woman'))
```

##### Make p3 imputed figure
```{r, eval = FALSE}
predictions <- lapply(1:5, function(i) {
  m <- lmer(student.score.post ~ student.score.pre + Lab.type * 
              (Gender + Race.ethnicity.AmInd + Race.ethnicity.NatHawaii + 
                 Race.ethnicity.Other + Race.ethnicity.Black +
                 Race.ethnicity.Hispanic + Race.ethnicity.Asian + 
                 Race.ethnicity.White + Race.ethnicity.Unknown) + 
              Major + (1 | anon_university_id.CIS/ResponseId.CIS), data = complete(imp1, action = i))
  ggpredict(m, c("Lab.type", "Race.ethnicity.Other"), ci.lvl = 0.67)
})
preds.race.other <- pool_predictions(predictions)

preds.race <- data.frame(preds.race.other) %>%
  filter(group == 1) %>%
  mutate(group = 'Race.ethnicity.Other')

for(race in c(new.race.cols[2:length(new.race.cols)])){
  predictions <- lapply(1:5, function(i) {
    m <- lmer(student.score.post ~ student.score.pre + Lab.type * 
                (Gender + Race.ethnicity.AmInd + Race.ethnicity.NatHawaii + 
                   Race.ethnicity.Other + Race.ethnicity.Black +
                   Race.ethnicity.Hispanic + Race.ethnicity.Asian +
                   Race.ethnicity.White + Race.ethnicity.Unknown) + 
                Major + (1 | anon_university_id.CIS/ResponseId.CIS), 
              data = complete(imp1, action = i))
    ggpredict(m, c("Lab.type", race), ci.lvl = 0.67)
  })
  # ...bind results in one dataframe...
  preds.race <- rbind(preds.race, 
                      data.frame(pool_predictions(predictions)) %>% 
                        filter(group == 1) %>%
                        mutate(group = race))
}

p3.imp <- ggplot(data.frame(preds.race), aes(x = factor(group), y = predicted, 
                                             color = factor(x), group = factor(x))) +
  geom_point(size = 2, position = position_dodge(width = 0.5)) +
  geom_errorbar(aes(ymin = conf.low, ymax = conf.high), size = 1, width = 0,
                position = position_dodge(width = 0.5)) +
  scale_color_manual(values = c('#e69f00', '#009e74', '#0071b2')) +
  labs(x = 'Race/ethnicity', y = 'Expected E-CLASS\nposttest scores') +
  theme(axis.text.x = element_text(angle = 40, vjust = 1, hjust = 1),
        legend.position = 'none') +
  scale_x_discrete(labels = c('American Indian', 'Asian', 'Black', 'Hispanic', 
                              'Native Hawaiian', 'Other', 'Unknown', 'White'))
```

##### Combine imputed marginal effects plots
```{r, eval = FALSE}
png('Figures/E-CLASS_Labtype_Demos_imputed.png', width = 586, height = 363)
grobs = cbind(ggplotGrob(p1.imp), ggplotGrob(p2.imp), ggplotGrob(p3.imp), 
              size = "first")
grid.arrange(leg, arrangeGrob(grobs), heights = c(1, 10))
dev.off()
```