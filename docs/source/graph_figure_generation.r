library(dagitty)
library(ggdag)
library(tibble)
library(stringr)

setwd('E:/Dev/Polyglot/PolyglotDB/docs/source/_static/img')



dag <- dagify("0.9" ~ "0.8",
              "0.8" ~ "0.7",
              "0.7" ~ "0.6",
              "0.6" ~ "0.5",
              "0.5" ~ "0.4",
              "0.4" ~ "0.3",
              "0.3" ~ "0.2",
              "0.2" ~ "0.1",
              "0.3" ~ "0.1",
              "0.5" ~ "0.3",
              "0.9" ~ "0.5",
       "0.9" ~ "0.1"
       )

t <- data.frame(tidy_dagitty(dag, layout='linear'))
t$edge_label =c('P', 'P.AA1', 'POLYGLOT', 'AA1', 'L', 'L.IY0', 'IY0', 'G', 'G.L.AA2.T', 'L', 'AA2', 'T', '')
ggplot(t, aes(x = x, y = y, xend = xend, yend = yend)) +geom_dag_edges_arc(aes(label=edge_label), vjust=-1) +geom_dag_node() +geom_dag_text() +theme_dag() +scale_dag()
ggsave('annotation_graph.png',width=8,height = 6,units='in', dpi=300)


dag <- dagify("T" ~ "AA2",
              "AA2" ~ "L2",
              "L2" ~ "G",
              "G" ~ "IY0",
              "IY0" ~ "L1",
              "L1" ~ "AA1",
              "AA1" ~ "P"
)

t3 <- data.frame(tidy_dagitty(dag, layout='linear'))
ggplot(t3, aes(x = x, y = y, xend = xend, yend = yend)) +geom_dag_edges() +geom_dag_node() +geom_dag_text() +theme_dag() +scale_dag()

dag <- dagify("T" ~ "AA2",
              "AA2" ~ "L2",
              "L2" ~ "G",
              "G" ~ "IY0",
              "IY0" ~ "L1",
              "L1" ~ "AA1",
              "AA1" ~ "P",
              "P.AA1" ~ "P" + "AA1",
              'L.IY0' ~ "L1" + "IY0",
              "G.L.AA2.T" ~ "G" + "L2" + "AA2" + "T",
              "G.L.AA2.T" ~ "L.IY0",
              "L.IY0" ~ "P.AA1",
              "POLYGLOT" ~ "P.AA1" + "L.IY0" + "G.L.AA2.T",
              labels = c("T"="begin=0.8\nend=0.9")
)

t2 <- data.frame(tidy_dagitty(dag, layout='linear'))
syllables = c('P.AA1', 'L.IY0', 'G.L.AA2.T')
t2$start_level <- 'phone'
t2[t2$name %in% syllables,]$start_level <- 'syllable'
t2[t2$name == 'POLYGLOT',]$start_level <- 'word'

t2$end_level <- NA
t2[!is.na(t2$to),]$end_level <- 'phone'
t2[t2$to %in% syllables& !is.na(t2$to),]$end_level <- 'syllable'
t2[t2$to == 'POLYGLOT'& !is.na(t2$to),]$end_level <- 'word'

t2[t2$start_level == 'syllable',]$y = 1
t2[t2$end_level == 'syllable' & !is.na(t2$end_level),]$yend = 1
t2[t2$start_level == 'word',]$y = 2
t2[t2$end_level == 'word' & !is.na(t2$end_level),]$yend = 2
t2[t2$name == 'P',]$x = 1
t2[t2$name == 'AA1',]$x = 2
t2[t2$name == 'L1',]$x = 3
t2[t2$name == 'IY0',]$x = 4
t2[t2$name == 'G',]$x = 5
t2[t2$name == 'L2',]$x = 6
t2[t2$name == 'AA2',]$x = 7
t2[t2$name == 'T',]$x = 8

t2[t2$to == 'P' & !is.na(t2$to),]$xend = 1
t2[t2$to == 'AA1' & !is.na(t2$to),]$xend = 2
t2[t2$to == 'L1' & !is.na(t2$to),]$xend = 3
t2[t2$to == 'IY0' & !is.na(t2$to),]$xend = 4
t2[t2$to == 'G' & !is.na(t2$to),]$xend = 5
t2[t2$to == 'L2' & !is.na(t2$to),]$xend = 6
t2[t2$to == 'AA2' & !is.na(t2$to),]$xend = 7
t2[t2$to == 'T' & !is.na(t2$to),]$xend = 8


t2[t2$name == 'P.AA1',]$x = 1.5
t2[t2$name == 'L.IY0',]$x = 3.5
t2[t2$name == 'G.L.AA2.T',]$x = 6.5

t2[t2$to == 'P.AA1'& !is.na(t2$to),]$xend = 1.5
t2[t2$to == 'L.IY0'& !is.na(t2$to),]$xend = 3.5
t2[t2$to == 'G.L.AA2.T'& !is.na(t2$to),]$xend = 6.5

t2[t2$name == 'POLYGLOT',]$x = 4.5

t2[t2$to == 'POLYGLOT' & !is.na(t2$to),]$xend = 4.5

t2$actual_label <- t2$name

t2[t2$actual_label %in% c('L1', 'L2'),]$actual_label <- 'L'

t2$arc_type <- 'solid'
t2[t2$start_level == t2$end_level & !is.na(t2$end_level),]$arc_type <- 'dashed'

ggplot(t2, aes(x = x, y = y, xend = xend, yend = yend, color=start_level)) +geom_dag_edges(aes(edge_linetype=arc_type)) +geom_dag_node(show.legend = FALSE) +geom_dag_text(aes(label=actual_label), size=3, color='black') +theme_dag() +scale_dag()
ggsave('neo4j_annotations.png',width=8,height = 6,units='in', dpi=300)

dag <- dagify("CORPUS" ~ "Utterance" + "Pitch" + "Formants" + "Speaker" + "Discourse",
              "Utterance" ~ "Word" + "Intonation" + "Utterance type",
              "Word" ~ "Syllable" + "Word type",
              "Syllable" ~ "Phone" + "Syllable type",
              "Phone" ~ "Closure" + "Burst" + "Phone type",
              labels = c("Closure"="begin\nend",
                         "Intonation"="tune\nproblematic",
                         "Word"="label\nbegin\nend",
                         "Word type"="label\ntranscription\nfrequency",
                         "Speaker"="name\ngender\nage",
                         "Discourse"="name\nconsonant_file_path\nvowel_file_path\nlow_freq_file_path"
                         )
)
t4 <- data.frame(tidy_dagitty(dag, layout = 'igraph', algorithm = 'kk'))
t4$node_type <- 'annotation'
t4[str_detect(t4$name, 'type'),]$node_type <- 'annotation type'
t4[t4$name %in% c('Burst', 'Closure', 'Intonation'),]$node_type <- 'subannotation'
t4[t4$name %in% c('Speaker', 'Discourse'),]$node_type <- 'spoken'
t4[t4$name %in% c('Pitch', 'Formants'),]$node_type <- 'acoustics'
t4[t4$name %in% c('CORPUS'),]$node_type <- 'corpus'

ggplot(t4, aes(x = x, y = y, xend = xend, yend = yend, color=node_type)) +geom_dag_edges() +geom_dag_node(show.legend = FALSE) +geom_dag_text(size=3, color='black') +theme_dag() +scale_dag() + geom_dag_label_repel(aes(label=label), size=3, color='black')
ggsave('hierarchy.png',width=10,height = 6,units='in', dpi=300)
