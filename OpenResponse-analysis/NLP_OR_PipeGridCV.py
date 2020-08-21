import sys
from time import time
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from nltk import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer
# from spacy.en import English
from itertools import combinations
from scipy import sparse
from sklearn.multiclass import OneVsRestClassifier
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn import metrics
from sklearn.naive_bayes import MultinomialNB
from sklearn.naive_bayes import BernoulliNB
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import NearestNeighbors
from sklearn.linear_model import SGDClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
import matplotlib.pyplot as plt

class LemmaTokenizer(object):
    def __init__(self):
        self.wnl = WordNetLemmatizer()
    def __call__(self, doc):
        Tokenizer = RegexpTokenizer(r'\w+|%|\+|\-')
        return [self.wnl.lemmatize(t) for t in Tokenizer.tokenize(doc)]

class SparseInteractions(BaseEstimator, TransformerMixin):

    def __init__(self, degree=2, feature_name_separator="_"):

        self.degree = degree
        self.feature_name_separator = feature_name_separator

    def fit(self, X, y=None):

        return self

    def transform(self, X):
        if not sparse.isspmatrix_csc(X):
            X = sparse.csc_matrix(X)
        if hasattr(X, "columns"):
            self.orig_col_names = X.columns
        else:
            self.orig_col_names = np.array([str(i) for i in range(X.shape[1])])
        spi = self._create_sparse_interactions(X)

        return spi

    def get_feature_names(self):

        return self.feature_names

    def _create_sparse_interactions(self, X):

        out_mat = []
        self.feature_names = self.orig_col_names.tolist()

        for sub_degree in range(2, self.degree + 1):
            for col_ixs in combinations(range(X.shape[1]), sub_degree):

                # add name for new column

                name = self.feature_name_separator.join(self.orig_col_names[list(col_ixs)])
                self.feature_names.append(name)

                # get column multiplications value

                out = X[:, col_ixs[0]]
                for j in col_ixs[1:]:
                    out = out.multiply(X[:, j])
                out_mat.append(out)

        return sparse.hstack([X] + out_mat)

def PLIC_OR_coding(file, CV):

    Time0 = time()

    plt.style.use('ggplot')
    np.random.seed(11)

    df = pd.read_excel(file, skiprows = [1])
    df = df.dropna(how = 'all', axis = 1)
    df = df.sample(frac = 1, random_state = 11).reset_index(drop = True) # reorder rows

    Scoring = 'roc_auc' # train using area under roc curve

    Pipe = Pipeline([
                #('CVect', HashingVectorizer(non_negative = True, stop_words = 'english', tokenizer = LemmaTokenizer(), ngram_range = (1, 2), n_features = 1000)),
                ('CVect', CountVectorizer(stop_words = 'english', tokenizer = LemmaTokenizer(), ngram_range = (1, 2), min_df = 0)),
                ('TFIDF', TfidfTransformer(use_idf = True, sublinear_tf = True, norm = 'l2')),
                #('Int', SparseInteractions(degree = 2, interaction_only = True)),
                #('MultiNBClass', MultinomialNB())
                #('BerNBClass', BernoulliNB())
                #('GaussNBClass', GaussianNB())
                ('LogClass', OneVsRestClassifier(LogisticRegression(solver = 'newton-cg', class_weight = 'balanced', random_state = 11, multi_class = 'multinomial')))
                #('XGBClass', XGBClassifier())
                #('SGDClass', OneVsRestClassifier(SGDClassifier(class_weight = 'balanced', random_state = 11, loss = 'log')))
                #('TreeClass', OneVsRestClassifier(DecisionTreeClassifier()))
                # ('MLPClass', OneVsRestClassifier(MLPClassifier(random_state = 11, hidden_layer_sizes = (10,))))
                ])

    Params = {
            'CVect__max_df': (0.5, 0.65, 0.8, 0.95),
            #'CVect__min_df': (0, 0.005),
            #'CVect__max_features': (800, 1000),
            #'CVect__ngram_range': ((1, 1), (1, 2)),  # unigrams or bigrams
            #'CVect__tokenizer': (None, LemmaTokenizer()),
            #'TFIDF__use_idf': (True, False),
            #'TFIDF__sublinear_tf': (True, False),
            #'TFIDF__norm': ('l1', 'l2'),
            #'MultiNBClass__alpha': (0.05, 0.25, 0.5, 0.75, 1)
            #'BerNBClass__alpha': (0.05, 0.25, 0.5, 0.75, 1),
            #'LogClass__estimator__C': np.arange(0.05, 1.05, 0.05),
            #'LogClass__estimator__fit_intercept': (False, True),
            #'LogClass__estimator__multi_class': ('ovr', 'multinomial')
            #'SGDClass__loss': ('log'),
            #'SGDClass__estimator__alpha': (0.00001, 0.000001),
            #'SGDClass__estimator__penalty': ('none', 'elasticnet', 'l2'),
            #'SGDClass__estimator__fit_intercept': (True, False),
            #'SGDClass__estimator__n_iter': (10, 50, 80)
            #'MLPClass__estimator__hidden_layer_sizes': ((100,), (40, 40))
            #'MLPClass__estimator__activation': ('identity', 'logistic', 'tanh', 'relu'),
            #'MLPClass__estimator__solver': ('lbfgs', 'sgd', 'adam'),
            #'MLPClass__estimator__alpha': (0.0001, 0.00001, 0.000001),
            #'MLPClass__estimator__tol': (0.0001, 0.00001, 0.000001)
            }

    Grid_Search = GridSearchCV(Pipe, Params, n_jobs = 1, verbose = 1, cv = CV, scoring = Scoring)
    # Grid_Search = RandomizedSearchCV(Pipe, Params, n_jobs=1, verbose=1, cv = 5, n_iter = 200, scoring = Scoring, random_state = 11)

    SumSeries = df.sum(numeric_only = True)
    Labels_To_Drop = list(SumSeries[SumSeries < CV].index) # if a code is used fewer times than the number of folds, drop the code
    df = df.drop(labels = Labels_To_Drop, axis = 1)

    Questions = ['Q1b', 'Q1d', 'Q1e', 'Q2b', 'Q2d', 'Q2e', 'Q3b']

    ScoreSeries = pd.Series()
    dfPar = pd.DataFrame()
    for Question in Questions:
        Qcols = [col for col in df.columns if Question in col]
        dfQ = df.loc[:, Qcols]
        dfQ = dfQ.dropna(subset = [Question]).reset_index()
        dfQ = dfQ.fillna(0)

        X = dfQ.loc[:, Question]
        Scores = []
        y = dfQ.drop(labels = [Question], axis = 1).apply(pd.to_numeric, errors = 'coerce').drop(labels = ['index'], axis = 1).fillna(1)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 100, random_state = 11)

        ### this chunk of code predicts all y values (i.e., codes) once ###
        # Grid_Search.fit(X_train, y_train)
        # print(Grid_Search.best_score_)
        # print(Grid_Search.best_estimator_.get_params())
        #
        # y_pred = Grid_Search.predict(X_test)
        # for col in y_test.columns:
        #     print(col)
        #     print(metrics.confusion_matrix(y_test[:, col], y_pred[:, col]))

        ### this does one code at a time ###
        for col in y_train.columns:
            Grid_Search.fit(X_train, y_train.loc[:, col])

            Scores.append(Grid_Search.best_score_)
            BestParameters = (Grid_Search.best_estimator_.get_params())

            for Parameter in sorted(Params.keys()):
                try:
                    dfPar.loc[col, Parameter] = BestParameters[Parameter]
                except ValueError:
                    dfPar.loc[col, Parameter] = sum(BestParameters[Parameter])

            y_pred = Grid_Search.predict(X_test)

            print(col)
            print((metrics.confusion_matrix(y_test.loc[:, col], y_pred))/100)

        NewScoresSeries = pd.Series(Scores, index = y_test.columns)
        ScoreSeries = ScoreSeries.append(NewScoresSeries)

    print('Run Time = ' + str(time() - Time0))
