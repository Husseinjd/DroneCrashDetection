
from sklearn import svm
from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.neighbors import KNeighborsClassifier  
from sklearn import metrics
import os
import sys
module_path = os.path.abspath(os.path.join('..'))
if module_path not in sys.path:
    sys.path.append(module_path)
from granger.grangercausality_reg import GrangerCausalityTest
from utils.utils import *
from scipy import stats
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB


class GrangerCausalityDiscrete(GrangerCausalityTest):
    """Granger Causality Test Based on Classification Models
    """
    def __init__(self,x=None,y=None,pd_frame=None,maxlag=None,alpha=0.05,names=['x','y'],class_method='dt'):
            #init super()
            super().__init__(x,y,pd_frame,maxlag,alpha,names)


    def fit_classifier(self,signalname,data,target,classifier,cv,scoring='accuracy'):
        """This method fits data based of a classification model specified
        
        Arguments:
            signalname {signal to process} -- used for verbosity
            data {DataFrame/Numpy Array} -- Features used for prediction
            target {list/numpyarray} -- targets for predictions (discrete)
            classifier {str} -- the classifier to use [svm,dt(decision tree),knn,lr(logistic)]
        
        Keyword Arguments:
            cv {int} -- number of folds to use 
            scoring {str} -- scoring metric (default: {'accuarcy'})
        
        Returns:
            [tuple] -- [(model,scores[list of scores for each fold])]
        """
        if classifier == 'all':
            l = ['nb','dt','knn','lr']
            scores_list = []
            mean_scores = []
            clf_list = []
            for cls in l:
                print('Fitting '+cls)
                clf,scores = self.fit_classifier(signalname,data,target,classifier=cls,cv=cv,scoring=scoring)
                scores_list.append(scores)
                clf_list.append(clf)
                mean_scores.append(np.mean(scores))
            #check which is the best classifier
            #here we can use McNemar’s test  or 5×2 Cross-Validation to check which classifier is the best
            #choosing between 4 classifiers can be time consuming for now we will choose the one
            #with the highest mean accuracy score
            idx = np.argmax(np.array(mean_scores))
            max_score_classifier = l[idx]
            return clf_list[idx],scores_list[idx]
        elif classifier == 'nb':
            clf = GaussianNB()
        elif classifier == 'dt':
            clf = DecisionTreeClassifier(random_state=1)
        elif classifier == 'knn':
            clf = KNeighborsClassifier(n_neighbors=7) 
        elif classifier == 'lr':
            clf = LogisticRegression()

        scores = cross_val_score(clf,data,target, cv=cv,scoring=scoring)
        return clf,scores


    def test(self,x,y,reduced_dataset,full_dataset,target,check_stationary=True,classifier='dt',verbose=True,cv=7):
        
        if check_stationary:
            _,is_stationary_x = self.stationary_test(x)
            if is_stationary_x:
                _,is_stationary_y = self.stationary_test(y)
                if is_stationary_y:
                    #Cross validation 
                    #Model and return results
                    #--------------------------------
                    #Reduced Model
                    if verbose:
                        print('Fitting reduced model')
                    clfreduced ,self.scores_reduced= self.fit_classifier(self.names[0],reduced_dataset,target,classifier=classifier,cv=cv)
                    #----------------------------------
                    #Full Model
                    if verbose:  
                        print('Fitting full model')
                    clffull, self.scores_full = self.fit_classifier(self.names[1],full_dataset,target,classifier=classifier,cv=cv)

                else:
                    print('Non-Stationary Data')
                    return -1
            else:
                print('Non-Stationary Data')
                return -1
        
        else:   #ignoring stationarity test
                #Reduced Model
                if verbose:
                    print('Fitting reduced model')
                clfreduced ,self.scores_reduced = self.fit_classifier(self.names[0],reduced_dataset,target,classifier=classifier,cv=cv)
                #----------------------------------
                #Full Model \
                if verbose:
                    print('Fitting full model')
                clffull, self.scores_full = self.fit_classifier(self.names[1],full_dataset,target,classifier=classifier,cv=cv)
        
        
        #Student-T test between the accuracy values
        if verbose:
            print('Performing T test')
        tstat , pvalue = stats.ttest_ind(self.scores_reduced,self.scores_full)
        self.mean_reduced =  np.mean(self.scores_reduced)
        self.mean_full = np.mean(self.scores_full)
        self.pvalue = pvalue
        if verbose:
            if pvalue < self.alpha:
                print('Mean Reduced Model [ {} ] Score :{}'.format(self.names[0],np.mean(self.scores_reduced)))
                print('Mean Full Model [ {} ] Score {}'.format(self.names[1],np.mean(self.scores_full)))
                print('Siginficant Result: pvalue =' ,pvalue)
            else:
                print('Mean Reduced Model [ {} ] Score :{}'.format(self.names[0],np.mean(self.scores_reduced)))
                print('Mean Full Model [ {} ] Score {}'.format(self.names[1],np.mean(self.scores_full)))
                print('No Siginficance: pvalue =' ,pvalue)
        return tstat,pvalue
