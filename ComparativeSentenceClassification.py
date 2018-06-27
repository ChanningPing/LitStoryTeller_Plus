# -*- coding: utf-8 -*-
from __future__ import division
from settings import APP_STATIC
import sys
import string
import csv
import json
import nltk
import pickle
from string import maketrans
from collections import defaultdict
from nltk.stem.snowball import SnowballStemmer
from sklearn.naive_bayes import MultinomialNB
import numpy as np
from sklearn.model_selection import cross_val_score

#global variables setting
reload(sys)
sys.setdefaultencoding('utf8')
stemmer = SnowballStemmer("english")

window_size = 4
TAU = 0.1
min_confidence = 0.6
frequent_patterns = []
rule_dict = {}
keyword_dict = {'advantag': 1, 'after': 1, 'ahead': 1, 'all': 1, 'altern': 1, 'altogeth': 1, 'beat': 1, 'befor': 1,
                'behind': 1, 'both': 1, 'choic': 1, 'choos': 1, 'compar': 1, 'compet': 1, 'defeat': 1, 'differ': 1,
                'domin': 1, 'doubl': 1,
                'either': 1, 'equal': 1, 'equival': 1, 'exceed': 1, 'favor': 1, 'first': 1, 'fraction': 1,
                'half': 1, 'ident': 1, 'improv': 1,
                'inferior': 1, 'last': 1, 'lead': 1, 'least': 1, 'less': 1, 'like': 1, 'match': 1,
                'most': 1, 'near': 1, 'nobodi': 1,
                'none': 1, 'nonpareil': 1, 'onli': 1, 'outclass': 1, 'outdist': 1, 'outdo': 1, 'outfox': 1,
                'outmatch': 1, 'outperform': 1,
                'outsel': 1, 'outstrip': 1, 'outwit': 1, 'peerless': 1, 'prefer': 1, 'recommend': 1, 'rival': 1,
                'same': 1, 'second': 1,
                'similar': 1, 'superior': 1, 'thrice': 1, 'togeth': 1, 'top': 1, 'twice': 1, 'unlik': 1,
                'unmatch': 1, 'unriv': 1, 'versus': 1, 'vs': 1, 'win': 1,
                 #newly added
                'fail': 1, 'gain':1, 'over':1, 'contrast':1 }
comparative_phrases = ['number one', 'on par with', 'one of few', 'up against']

def get_sequence (tagged_tuples, idx, window_size):
    '''
    :param taggled_tuples: a sentence tagged with POS tags ( a list of <word, tag>)
    :param idx: the index of the keyword
    :param window_size: the size of surrounding words of the keyword
    :return: a sequence of window_size
    '''
    start = idx - window_size if idx - window_size >= 0  else 0  # start index of sequence
    end = idx + window_size + 1 if (idx + window_size + 1) <= len(tagged_tuples) else len(
        tagged_tuples)  # end index of sequence
    left_sub_tuples = [i[1] for i in tagged_tuples[start: idx]]  # tags before keyword in the sequence
    right_sub_tuples = [i[1] for i in tagged_tuples[idx + 1: end]]  # tags after keyword in the sequence
    keyword = []
    keyword.append(tagged_tuples[idx][1] + '_' + str(stemmer.stem(tagged_tuples[idx][0])))  # make keyword as a list
    sequence = left_sub_tuples + keyword + right_sub_tuples  # concatenate together
    return sequence



def sentence_to_sequences(sentence, label, window_size):
    '''
    :param sentence: a natural sentence
    :param window_size: how many words from the central keyword to form the squence
    :return: a list of sequences (a sentence could contain multiple keywords, thus multiple sequences)
    '''

    # 1. remove punctuations
    print(sentence)
    replace_punctuation = string.maketrans(string.punctuation, ' ' * len(string.punctuation))
    sentence = str(sentence)
    sentence = sentence.translate(replace_punctuation)
    # 2. POS tag the sentence
    tagged_tuples = nltk.pos_tag(nltk.word_tokenize(sentence.lower()))
    print(tagged_tuples)
    # 3. define the sequence object
    sequences = []
    # 4. 4 conditions that satisfy the comparative candidate rule
    # rule-1: if the sentence contains standard comparative, keep it
    for idx, item in enumerate(tagged_tuples):
        if item[1] == 'JJR' or item[1] == 'RBR' or item[1] == 'JJS' or item[1] == 'RBS':
            sequence_object = []
            sequence = get_sequence(tagged_tuples, idx, window_size)
            sequence_object.append(label)
            sequence_object.append(sequence)
            sequences.append(sequence_object)


    # rule-2: if the sentence contains as {} as,keep it, here we increase window size by 1 to accomodate the as...as as context
    indices = [i for i, item in enumerate(tagged_tuples) if item[0] == 'as' and item[1] == 'RB']
    for index in indices:
        if (index + 1) < len(tagged_tuples):
            if tagged_tuples[index + 1][1] == 'JJ' or tagged_tuples[index + 1][1] == 'RB':
                if (index + 2) < len(tagged_tuples):
                    if  tagged_tuples[index + 2][0] == 'as' and tagged_tuples[index + 2][1] == 'IN':
                        sequence_object = []
                        sequence = get_sequence(tagged_tuples, index + 1, window_size + 1)
                        sequence_object.append(label)
                        sequence_object.append(sequence)
                        sequences.append(sequence_object)

    # rule-3: if the sentence contains certain keyword, keep it
    for idx, item in enumerate(tagged_tuples):
        #print('is this wrong?'+item[0])
        if stemmer.stem(item[0]) in keyword_dict:
            sequence_object = []
            sequence = get_sequence(tagged_tuples, idx, window_size)
            sequence_object.append(label)
            sequence_object.append(sequence)
            sequences.append(sequence_object)

    # rule-4: if the sentence contains phrases, use this as a feature
    for phrase in comparative_phrases:
        if phrase in sentence:
            sequence_object = []
            offset = len(phrase)/2
            middle = sentence.index(phrase)
            sequence = get_sequence(tagged_tuples, middle, window_size + offset)
            sequence = get_sequence(tagged_tuples, idx, window_size)
            sequence_object.append(label)
            sequence_object.append(sequence)
            sequences.append(sequence_object)
            # print("candidate based on \'" + phrase + "\'")
    #print(sentence)
    #print(sequence_object['sequences'])
    #print(sequences)
    return sequences

def PrefixSpanCSR(sequences,seq_labels,TAU,min_confidence):
    '''
    This method is a slight modification of this implementation of PrefixSpan in Python:
    https://github.com/chuanconggao/PrefixSpan-py
    The original paper is here:
    Han, J., Pei, J., Mortazavi-Asl, B., Pinto, H., Chen, Q., Dayal, U., & Hsu, M. C. (2001, April). Prefixspan: Mining sequential patterns efficiently by prefix-projected pattern growth. In proceedings of the 17th international conference on data engineering (pp. 215-224).

    :param sequences: a set of sequences derived in sentence_to_sequences()
    :param seq_labels: a set of labels derived in sentence_to_sequences()
    :param TAU: the hyperparameter used in (Jindal & Liu, 2006) paper, used to give different items different min_sup
    :param min_confidence:the hyperparameter used in (Jindal & Liu, 2006) paper
    :return:
    '''
    results = []
    def mine_rec(patt, mdb):
        numYES = 0
        numNO = 0
        for coordinate in mdb:
            if seq_labels[coordinate[0]] == '1':
                numYES += 1
            else:
                numNO += 1
        # the pattern, the frequency of the pattern, the number of YES labels, the number of NO labels
        results.append((patt, len(mdb), numYES, numNO))
        occurs = defaultdict(list)
        for (i, startpos) in mdb:
            seq = sequences[i]
            for j in xrange(startpos, len(seq)):
                l = occurs[seq[j]]
                if len(l) == 0 or l[-1][0] != i:
                    l.append((i, j + 1))

        for (c, newmdb) in occurs.iteritems():
            # the following if-statement is pruning, we stop this since we will prune in final stage using both sup and conf
            # if len(newmdb) >= minsup:
            mine_rec(patt + [c], newmdb)

    mine_rec([], [(i, 0) for i in xrange(len(sequences))])

    #filtering  the patterns by min_sup and min_confidence
    count = 0
    CSR_rules=[]
    #print('length of total number of sequences='+str(len(sequences)))
    for result in results: #[0]the rule; [1]the frequency of the rule; [2]number of positive labels of this rule [3] number of negative labels of this rule
        positive_sup = result[2]
        negative_sup = result[3]
        min_sup = result[1] * TAU
        positive_confidence = result[2] / result[1]
        negative_confidence = result[3] / result[1]
        #print('the rule is')
        #print(result[0])
        #print('frequency='+str(result[1])+',positive number='+str(result[2])+',negative number='+str(result[3]))
        #print('positive sup='+str(positive_sup))
        #generate positive and negative rules respectively
        if positive_sup >= min_sup and positive_confidence >= min_confidence and result[0]: #positive rules
            rule = []
            rule.append(result[0])
            rule.append(result[1])
            rule.append(positive_sup)
            rule.append(positive_confidence)
            rule.append('1')
            rule.append(count)
            print(result[0])
            print('max index=' + str(count))
            count += 1
            CSR_rules.append(rule)
        if negative_sup >= min_sup and negative_confidence >= min_confidence and result[0]: #negative rules
            rule = []
            rule.append(result[0])
            rule.append(result[1])
            rule.append(negative_sup)
            rule.append(negative_confidence)
            rule.append('0')
            rule.append(count)
            print(result[0])
            print('max index=' + str(count))
            count += 1
            CSR_rules.append(rule)

    return CSR_rules


def get_features(sentence, CSR_Rules):
    '''
    :param sentence: include label, sentence and a list of sequences (of a sentence)
    :return: a list of values of features mapping to the elements of frequent_patterns
    '''

    features = [0] * len(CSR_Rules)
    # check if any sequence match any rule
    for sequence in sentence['sequences']:
        sequence_string = ('_').join(word for word in sequence[1])
        for idx, rule in enumerate(CSR_Rules):
            rule_string = ('_').join(word for word in rule[0])
            if rule_string in sequence_string or sequence_string in rule_string:
                index = rule[5]
                features[index] = 1
    # check if the whole sentence contains any rule
    tagged_tuples = nltk.pos_tag(nltk.word_tokenize(sentence['sentence'].lower()))
    sentence_string = ('_').join(word[1] for word in tagged_tuples)
    for idx, rule in enumerate(CSR_Rules):
        rule_string = ('_').join(word for word in rule[0])
        if rule_string in sentence_string or sentence_string in rule_string:
            index = rule[5]
            #print('index='+str(index))
            #print('feature length=' + str(len(features)))
            features[index] = 1


    return features


def train_comparative(file_name):
    '''
    :param file_name: name of a local file of labelled comparative sentences, in csv format, <tag, sentence>
    :return: a classifier (written to local) with precision and recall
    '''
    # 1. read training corpus line by line, and generate sequences for each sentence
    sentences = [] # a list of sentence objects, each has {label, sentence}
    all_sequences = []
    with open(file_name) as f:  # read labels and sentences from file
        rows = [line.split(',') for line in f]  # create a list of lists
        for row in rows:  # row[0]: label; row[1]:sentence
            sentence = {}
            sentence['label'] = row[0]
            sentence['sentence'] = row[1]
            sequences = sentence_to_sequences(sentence['sentence'], sentence['label'], window_size)
            sentence['sequences'] = sequences
            sentences.append(sentence)
            if len(sequences)>0:
                all_sequences = all_sequences + sequences
    #all_sequences = list(set(all_sequences))
    #print(all_sequences)

    # 2. write all sequences into file for later PrefixSpan sequence pattern mining
    file_name = APP_STATIC + '/nlp/CSR/all_sequences.csv'
    file = open(file_name, 'w')
    for sequence in all_sequences:
        file.write("%s\n" % sequence)

    #separate the two columns into 2 lists
    labels = [row[0] for row in all_sequences]
    sequences = [row[1] for row in all_sequences]

    #print(labels)
    #print(sequences)

    # 3.find sequence patterns with PrefixSpan, <rule, frequency, sup, confidence, label, ID>
    CSR_Rules= PrefixSpanCSR(sequences, labels, TAU,min_confidence)
    # save the patterns to file
    file_name = APP_STATIC + '/nlp/CSR/CSR_rules.csv'


    # 4. build features of each sentence
    # read the rules into a dictionary for quick lookup
    '''
     for rule in CSR_Rules:
            if rule[0]:#only saves the non-empty rules
                key = ('_').join(word for word in rule[0])
                rule_dict[key] = rule[1:6]
    '''


   # with open(file_name, 'wb') as dump:
        #dump.write(json.dumps(CSR_Rules))
    for rule in CSR_Rules:
        print(rule)
        if not rule[0]:
            CSR_Rules.remove(rule)
            break
    with open(file_name, 'wb') as f:
        pickle.dump(CSR_Rules, f)

    feature_matrix = []
    for idx, sentence in enumerate(sentences):
        features = get_features(sentence, CSR_Rules)#sentence include: label, sentence,sequences
        #print('in training phase, length of the features' + str(len(features)))
        print(sentence)
        features.append(sentence['label'])
        print(features)
        feature_matrix.append(features)
    #print(rule_dict)
    #print(feature_matrix)
    # 5. train the Bayes classifier
    # train the Naive Bayes classifier

    clf = MultinomialNB()
    #from sklearn import svm
    #clf = svm.SVC()
    #from sklearn.linear_model import LogisticRegression
    #clf = LogisticRegression(fit_intercept = False, C = 1e9)
    data = np.array(feature_matrix)
    data_X = data[:, 0: len(CSR_Rules)].astype(np.float)
    data_Y = data[:, len(CSR_Rules)]
    y_pred = clf.fit(data_X, data_Y).predict(data_X)
    #print(y_pred)
    print("Number of mislabeled points out of a total %d points : %d" % (data_X.shape[0], (data_Y != y_pred).sum()))

    # cross-validation
    scores = cross_val_score(clf, data_X, data_Y, cv=5)
    print('cross validation score...' + str(scores))
    print("Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))

    # save the model to disk
    file_name = APP_STATIC + '/nlp/CSR/classifier.sav'
    pickle.dump(clf, open(file_name, 'wb'))




def read_classifier(classifier_file_name):
    '''

    :param classifier_file_name:
    :return:
    '''
    # load the model from disk
    loaded_Bayes_classifier = pickle.load(open(classifier_file_name, 'rb'))
    #result = loaded_Bayes_classifier.score(X_test, Y_test)
    print(loaded_Bayes_classifier)
    return loaded_Bayes_classifier

def read_rule_dict(file_name):
    '''
    :param file_name: the name of the CSR rule dictioanry file
    :return:return the CSR dict
    '''
    #read_rule_dictionary = {}
    with open(file_name, 'rb') as f:
        read_rule_dictionary = pickle.load(f)
    print('sucessfully read the dict:')
    print(read_rule_dictionary)


    return read_rule_dictionary

def predict_initiation(classfier_file_name, rule_dict_file_name):
    # 1. read the rule dict
    read_rule_dictionary = read_rule_dict(rule_dict_file_name)

    # 2. read the classifier
    loaded_Bayes_classifier = read_classifier(classfier_file_name)
    predict_initiation_tools = {}
    predict_initiation_tools['dict'] = read_rule_dictionary
    predict_initiation_tools['classifier'] = loaded_Bayes_classifier
    return predict_initiation_tools



def predict_comparative(sentence,read_rule_dictionary, loaded_Bayes_classifier ):
    '''
    :param sentence:
    :param classfier_file_name:
    :param rule_dict_file_name:
    :return:
    '''


    # 3. generate the sequence
    sequences = sentence_to_sequences(sentence, 0, window_size)
    #print(sequences)

    # 4. generate the features
    sentence_object = {}
    sentence_object['label'] = 0
    sentence_object['sequences'] = sequences
    sentence_object['sentence'] = sentence
    #print('sentence object=')
    #print(sentence_object)
    features = get_features(sentence_object,read_rule_dictionary)
    ##print('in predict, length of the features'+str(len(features)))

    # 5. predict
    #print('[sentence]='+sentence)
    #print('[dict]=')
    #print(read_rule_dictionary)
    #print('sequences')
    #print(sequences)
    #print('features')
    #print(features)
    #print('after reload the classifier, the predicted result=')
    features = X = np.array(features)
    features = features.reshape(1, -1)
    class_result = loaded_Bayes_classifier.predict(features)
    class_label = class_result[0]
    #print(class_label)
    return class_label





def main():
    #train process
    file_name = APP_STATIC + '/nlp/corpus/ComparativeTrainCorpus.txt'
    #train_comparative(file_name)

    #predict process
    #rule_dict_file_name = APP_STATIC + '/nlp/CSR/CSR_rules.csv'
    #classifier_file_name = APP_STATIC + '/nlp/CSR/classifier.sav'
    #sentence = 'Our model shows an improvement of about a significant improvement over previous state-of-the-art in both MAP and MRR when training on TRAIN and TRAIN-ALL'



    #predict_comparative(sentence, classifier_file_name, rule_dict_file_name)




main()
