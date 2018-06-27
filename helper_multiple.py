import community
import networkx as nx
import collections
import math


def Json_list_to_single_Json(JsonResult_list, keep_rate):
    csv_file = open('static/data/multiLine_no_missing_1.csv', 'w')
    characters = collections.defaultdict(list) # only for test, delete later

    # first round: get all character names
    character_vocab = set()
    for i, JsonResult in enumerate(JsonResult_list): # for each paper
        network_data = JsonResult['co_occurrence_network']
        partition, communities = community_detection(network_data)
        print('partition------')
        print(partition)
        print('edges-------')
        print(network_data['edges'] )
        print('nodes....')
        print(network_data['nodes'])
        for community_id in list(sorted(communities.keys())): # for each community in a paper
            print(community_id)
            print(list(sorted(communities[community_id])))
            for entity in list(sorted(communities[community_id])): # for each entity in a community
                character_vocab.add(entity)
                #characters[entity].append(i) # record paper_id that the entity appears in
        for edge in network_data['edges'] :
            characters[network_data['nodes'][edge['source']]['name']].append(edge['cooccurrences'])
            characters[network_data['nodes'][edge['target']]['name']].append(edge['cooccurrences'])



    # second round: calculate community and entity weight

    character_weights = {}

    for i, JsonResult in enumerate(JsonResult_list): # for each paper
        network_data = JsonResult['co_occurrence_network']
        partition, communities = community_detection(network_data)
        weighted_communities = []  # {community_id: {community_weight: w, community_entities:[{entity:score}]}}
        for community_id in communities.keys(): # for each community in a paper
            community_entities = []
            community_weight = []
            for entity in communities[community_id]:  # for each entity in a community
                entity_score = sum(characters[entity]) / 15
                #entity_score = sum(characters[entity])
                if entity_score>00:
                    community_entities.append({'entity': entity, 'entity_score': entity_score})
                    community_weight.append(entity_score)

                    # for storing entity weights
                    character_weights[entity] = entity_score


            # save community weight into
            if community_entities:
                most_important_entity= sorted(community_entities, key=lambda x: (x['entity_score'], x['entity']),reverse=True)[0]
                weighted_communities.append({'community_weight': max(community_weight) if community_weight else 0,
                                                      'community_entities':community_entities,
                                                      'most_important_entity':most_important_entity })

        JsonResult_list[i]['weighted_communities'] = weighted_communities
        print('weighted communities')
        print(i)
        print(weighted_communities)






    # third round: generate data
    storyline_data = []
    rectangle_data = []
    count = 0
    for JsonResult in JsonResult_list:
        network_data = JsonResult['co_occurrence_network']
        partition, communities = community_detection(network_data)
        x = 0
        paper_title = '(' + JsonResult['firstAuthor'] + ' - ' + str(JsonResult['year']) + ')'
        # single_paper = {'quarter': 'p_' + str(count) }
        single_paper = {'quarter': paper_title.encode('utf-8')}

        for entity in sorted(character_vocab):
            if entity in character_weights:
                single_paper[entity] = 'null'

        weighted_communities = JsonResult['weighted_communities']
        for weighted_community in sorted(weighted_communities, key=lambda x: (x['community_weight'],x['most_important_entity']), reverse=True):

            # rectangle = {'value':x, 'label':'p_' + str(count) , 'weight': 18}
            rectangle = {'value': x, 'label': paper_title.encode('utf-8'), 'weight': 18}
            for entity_score in  sorted(weighted_community['community_entities'] , key=lambda x: (x['entity_score'],x['entity']), reverse=True):

            #for entity in list(sorted(communities[community_id])):
                print('entity_score')
                print(entity_score)
                entity = entity_score['entity']
                single_paper[entity] = x
                x += 10

            rectangle['height'] = x -  rectangle['value'] - 35
            #rectangle['value'] += rectangle['height']
            rectangle_data.append(rectangle)
            x += 30
        count += 1
        storyline_data.append(single_paper)
        print('storyline data')
        print(storyline_data)



    # write head
    csv_file.write('quarter')
    for entity in sorted(character_vocab):
        if entity in character_weights:
            csv_file.write(',' + entity.encode('utf-8'))
    csv_file.write('\n')

    for single_paper in storyline_data:
        csv_file.write(single_paper['quarter'])
        for entity in sorted(character_vocab):
            if entity in character_weights:
                csv_file.write(',' + str(single_paper[entity]))
        csv_file.write('\n')

    csv_file.close()


    for single_paper in storyline_data:
        print(single_paper)




    #tsv_file.write('Hello\n')
    for entity in characters:
        print(entity)
        print(characters[entity])


    for rect in rectangle_data:
        print(rect)





    final_result = ''
    return rectangle_data, character_weights


def community_detection(network_data):

    # pre-process node names
    import re

    for i, node in enumerate(network_data['nodes']):
        print('escape!')
        print(node['name'])
        network_data['nodes'][i]['name'] = re.sub('[^a-zA-Z0-9]+', ' ', node['name']).encode('utf-8')
        print(network_data['nodes'][i]['name'])


    # read data into a networkx graph object
    nodes_vocab = {node['id']:node['name'] for node in network_data['nodes']}
    nodes = [node['name'] for node in network_data['nodes']]
    edges = [(nodes_vocab[edge['source']], nodes_vocab[edge['target']], edge['cooccurrences']) for edge in network_data['edges']]
    g = nx.Graph()
    g.add_weighted_edges_from(edges)
    partition = community.best_partition(g)
    print('in partition')
    print(partition) # {entity_name: community_id}

    communities = collections.defaultdict(list)
    for entity in partition.keys():
        communities[partition[entity]].append(entity)
    print('in communities')
    print(communities)# {community_id: [entity_name]}

    return partition, communities


def generate_summarization(JsonResult_list, keep_rate, comparative_bias):
    '''
    :param JsonResult_list:  a list of data, each about all information of a paper
    :param keep_rate: the portion to be preserved in the summarization, controls how many top-n entities to be used for summarization
    :return:
    '''
    # record entity occurrences
    characters = collections.defaultdict(list)  # only for test, delete later
    for i, JsonResult in enumerate(JsonResult_list):  # for each paper
        network_data = JsonResult['co_occurrence_network']
        partition, communities = community_detection(network_data)
        for community_id in list(sorted(communities.keys())):  # for each community in a paper
            for entity in communities[community_id]:  # for each entity in a community
                characters[entity.encode('utf-8')].append(i)  # record paper_id that the entity appears in

    # get global entity scores
    character_weights = {}
    for entity in characters.keys():
        character_weights[entity.encode('utf-8')] = len(characters[entity.encode('utf-8')])




    print('why not working')
    print(character_weights)



    summary_collection = {}
    # for each paper, get top-n entity
    for i, JsonResult in enumerate(JsonResult_list):  # for each paper
        paper_title = '(' + JsonResult['firstAuthor'] + ' - ' + str(JsonResult['year']) + ')'

        local_entity_scores = {}
        for entity in  JsonResult['characters']:
            print(entity)
            if entity['name'].encode('utf-8') in character_weights:
                local_entity_scores[entity['name'].encode('utf-8')] = character_weights[entity['name'].encode('utf-8')]

        # get top-n entities based on keep_rate
        N = keep_rate
        top_N_entities = sorted(local_entity_scores, key=local_entity_scores.get, reverse=True)

        top_N_sentences_with_scores = [] #{'sentence': sentence, 'score': score}

        summary_per_paper = []

        already_summarized_entities = {}

        for s_id in sorted(JsonResult['sentence_id_text_dict'].keys()):
            contain_entities = []
            sentence = JsonResult['sentence_id_text_dict'][s_id]
            for compound_entity in JsonResult['characters']:
                if compound_entity['name'].encode('utf-8') in top_N_entities and s_id in compound_entity['sentence_occurrences']:
                    contain_entities.append(compound_entity['name'].encode('utf-8'))
            if len(contain_entities) >= 2:
                if tuple(sorted(contain_entities)) not in already_summarized_entities:
                    already_summarized_entities[ tuple(sorted(contain_entities))] = 1
                    total_score = sum([local_entity_scores[entity.encode('utf-8')] for entity in contain_entities])

                    comparative_score = JsonResult['yes_no_comparative'][int(s_id)]
                    print('is comparative')
                    print(comparative_score)

                    total_score += int(comparative_score)*comparative_bias
                    summary_per_paper.append({'entities':contain_entities, 'sentence': sentence, 'score':total_score, 's_id': -int(s_id)})


                    print('the sentence')
                    print(sentence)



        summary_per_paper = sorted(summary_per_paper , key=lambda x: (x['score'],x['s_id']), reverse=True)[:N]

        summary_collection[i] = {'paper_title':paper_title, 'summary_per_paper':summary_per_paper }


    print('now is the summary-------------')

    summary = []
    for paper_id in summary_collection.keys():
        print('paper-{}----------------------------'.format(summary_collection[paper_id]['paper_title']))
        paper_title = summary_collection[paper_id]['paper_title']
        paper_summary = []
        for sentence in summary_collection[paper_id]['summary_per_paper']:

            print('sentence_id:{} | entities:{}| score:{} '.format(-int(sentence['s_id']),(',').join(sentence['entities']), sentence['score']))
            print('sentence:{}'.format(sentence['sentence']))

            paper_summary.append({
                's_id': -int(sentence['s_id']),
                'score': sentence['score'],
                'entities' : (' | ').join(sentence['entities']).encode('utf-8'),
                'sentence' : sentence['sentence'].encode('utf-8')

            })



        summary.append({'article':paper_title.encode('utf-8'), 'summary': paper_summary })
    return summary


def generate_summarization_BasicSum(JsonResult_list, keep_rate, comparative_bias):
    '''
    :param JsonResult_list:  a list of data, each about all information of a paper
    :param keep_rate: the portion to be preserved in the summarization, controls how many top-n entities to be used for summarization
    :return:
    '''
    # record entity occurrences
    characters = collections.defaultdict(list)  # only for test, delete later
    for i, JsonResult in enumerate(JsonResult_list):  # for each paper
        network_data = JsonResult['co_occurrence_network']
        partition, communities = community_detection(network_data)
        for community_id in list(sorted(communities.keys())):  # for each community in a paper
            for entity in communities[community_id]:  # for each entity in a community
                characters[entity.encode('utf-8')].append(i)  # record paper_id that the entity appears in

    # get global entity scores
    character_weights = {}
    for entity in characters.keys():
        character_weights[entity.encode('utf-8')] = len(characters[entity.encode('utf-8')])

    summary_collection = {}
    # for each paper, get top-n entity
    for i, JsonResult in enumerate(JsonResult_list):  # for each paper
        paper_title = '(' + JsonResult['firstAuthor'] + ' - ' + str(JsonResult['year']) + ')'

        local_entity_scores = {}
        for entity in  JsonResult['characters']:
            if entity['name'].encode('utf-8') in character_weights:
                local_entity_scores[entity['name'].encode('utf-8')] = character_weights[entity['name'].encode('utf-8')]

        # get top-n entities based on keep_rate
        N = keep_rate
        top_N_entities = sorted(local_entity_scores, key=local_entity_scores.get, reverse=True)

        candidate_sentences = []


        for s_id in sorted(JsonResult['sentence_id_text_dict'].keys()):
            contain_entities = []
            sentence = JsonResult['sentence_id_text_dict'][s_id]
            for compound_entity in JsonResult['characters']:
                if compound_entity['name'].encode('utf-8') in top_N_entities and s_id in compound_entity['sentence_occurrences']:
                    contain_entities.append(compound_entity['name'].encode('utf-8'))

            average_score = float(sum([local_entity_scores[entity.encode('utf-8')] for entity in contain_entities])) / len(contain_entities) if len(contain_entities)>0 else 0
            total_score = sum([local_entity_scores[entity.encode('utf-8')] for entity in contain_entities])

            total_score = average_score + total_score
            comparative_score = JsonResult['yes_no_comparative'][int(s_id)]
            total_score += int(comparative_score)

            candidate_sentences.append({'entities':contain_entities, 'sentence': sentence, 'score':total_score, 's_id': -int(s_id),'IsComparartive':int(comparative_score)})

        summary_per_paper = []
        for k in range(N):
            candidate_sentences = sorted(candidate_sentences, key=lambda x: (x['score'], x['s_id']), reverse=True)
            print('the candidate sentences')
            print(candidate_sentences)
            if candidate_sentences:
                selected_sentence = candidate_sentences[0]
                copy_local_entity_scores = local_entity_scores.copy()
                summary_per_paper.append({'selected_sentence':selected_sentence, 'local_entity_scores':copy_local_entity_scores})
                print('iterate over N')
                print(copy_local_entity_scores)
                print(selected_sentence)
                candidate_sentences.pop(0)

                selected_entities = selected_sentence['entities']
                local_entity_scores = down_sampling_entities(local_entity_scores, selected_entities)
                print('why candidate sentence not wkring')
                print(candidate_sentences)
                candidate_sentences = calculate_sentence_scores(candidate_sentences, local_entity_scores, JsonResult, comparative_bias)



        summary_collection[i] = {'paper_title':paper_title, 'summary_per_paper':summary_per_paper }


    print('now is the summary-------------')

    summary = []
    for paper_id in summary_collection.keys():
        print('paper-{}----------------------------'.format(summary_collection[paper_id]['paper_title']))
        paper_title = summary_collection[paper_id]['paper_title']
        paper_summary = []
        for sentence_compound in summary_collection[paper_id]['summary_per_paper']:
            sentence = sentence_compound['selected_sentence']
            print('what is wrong')
            print(sentence_compound['selected_sentence'])
            print(sentence_compound['local_entity_scores'])

            print('sentence_id:{} | entities:{}| score:{} '.format(-int(sentence['s_id']),(',').join(sentence['entities']), sentence['score']))
            print('sentence:{}'.format(sentence['sentence']))

            score_components = ''
            for entity in sentence['entities']:
                score_components += entity + '(' + str(sentence_compound['local_entity_scores'][entity.encode('utf-8')]) + '), '
            score_components += 'Comparative:' + str(sentence['IsComparartive'])
            score_components = score_components.encode('utf-8')

            paper_summary.append({
                's_id': -int(sentence['s_id']),
                'score': sentence['score'],
                'entities' : score_components,
                'sentence' : sentence['sentence'].encode('utf-8')

            })



        summary.append({'article':paper_title.encode('utf-8'), 'summary': paper_summary })
    return summary




def down_sampling_entities(local_entity_scores, selected_entities):
    print('before downsampling')
    print(local_entity_scores)

    for entity in selected_entities:
        if entity in local_entity_scores:
            local_entity_scores[entity] = local_entity_scores[entity] * 0.5


    print('after downsampling')
    print(local_entity_scores)
    return local_entity_scores



def calculate_sentence_scores(candidate_sentences, local_entity_scores, JsonResult,comparative_bias):
    for sentence in candidate_sentences:

        average_score = float(sum([local_entity_scores[entity.encode('utf-8')] for entity in sentence['entities'] ])) / len(sentence['entities']) if len(sentence['entities']) > 0 else 0
        total_score = sum([local_entity_scores[entity.encode('utf-8')] for entity in sentence['entities'] ])

        sentence['score'] =  average_score + total_score
        comparative_score = JsonResult['yes_no_comparative'][-int(sentence['s_id'])]
        sentence['score'] += int(comparative_score)


    return candidate_sentences













network_data_1 = {
    'nodes': [{'frequency': 1, 'name': u'Word embedding', 'id': 0}, {'frequency': 35, 'name': u'Twitter Inc.', 'id': 1},
              {'frequency': 13, 'name': u'SemEval', 'id': 2}, {'frequency': 1, 'name': u'Phoenix Suns', 'id': 3},
              {'frequency': 1, 'name': u'Tensor', 'id': 4},
              {'frequency': 3, 'name': u'Recursive neural network', 'id': 5},
              {'frequency': 1, 'name': u'Autoencoder', 'id': 6},
              {'frequency': 1, 'name': u'Combinatory categorial grammar', 'id': 7},
              {'frequency': 1, 'name': u'Rugby union', 'id': 8},
              {'frequency': 6, 'name': u'Support vector machine', 'id': 9},
              {'frequency': 3, 'name': u'LIBSVM', 'id': 10},
              {'frequency': 2, 'name': u'Naive Bayes classifier', 'id': 11},
              {'frequency': 6, 'name': u'Formula One', 'id': 12},
              {'frequency': 2, 'name': u'Natural language processing', 'id': 13},
              {'frequency': 20, 'name': u'Country', 'id': 14}, {'frequency': 7, 'name': u'Word2vec', 'id': 15},
              {'frequency': 2, 'name': u'Macro', 'id': 16}, {'frequency': 1, 'name': u'Randomness', 'id': 17},
              {'frequency': 1, 'name': u'Embedding', 'id': 18}],
    'edges': [{'source': 6, 'target': 7, 'cooccurrences': 1}, {'source': 14, 'target': 18, 'cooccurrences': 1},
              {'source': 15, 'target': 14, 'cooccurrences': 1}, {'source': 16, 'target': 12, 'cooccurrences': 2},
              {'source': 15, 'target': 12, 'cooccurrences': 1}, {'source': 11, 'target': 9, 'cooccurrences': 1},
              {'source': 14, 'target': 12, 'cooccurrences': 1}, {'source': 14, 'target': 15, 'cooccurrences': 6},
              {'source': 0, 'target': 1, 'cooccurrences': 1}, {'source': 2, 'target': 8, 'cooccurrences': 1},
              {'source': 2, 'target': 9, 'cooccurrences': 1}, {'source': 15, 'target': 18, 'cooccurrences': 1},
              {'source': 17, 'target': 15, 'cooccurrences': 1}, {'source': 1, 'target': 8, 'cooccurrences': 1},
              {'source': 4, 'target': 5, 'cooccurrences': 1}, {'source': 17, 'target': 18, 'cooccurrences': 1},
              {'source': 2, 'target': 12, 'cooccurrences': 2}, {'source': 17, 'target': 14, 'cooccurrences': 1},
              {'source': 2, 'target': 16, 'cooccurrences': 1}, {'source': 1, 'target': 2, 'cooccurrences': 7},
              {'source': 13, 'target': 15, 'cooccurrences': 1}, {'source': 9, 'target': 12, 'cooccurrences': 1},
              {'source': 9, 'target': 10, 'cooccurrences': 1}, {'source': 1, 'target': 3, 'cooccurrences': 1},
              {'source': 13, 'target': 14, 'cooccurrences': 1}]}

network_data_2 = {'nodes': [{'frequency': 2, 'name': u'Semantic similarity', 'id': 0}, {'frequency': 12, 'name': u'Text segmentation', 'id': 1}, {'frequency': 4, 'name': u'Natural language processing', 'id': 2}, {'frequency': 3, 'name': u'Information retrieval', 'id': 3}, {'frequency': 3, 'name': u'Hearst Corporation', 'id': 4}, {'frequency': 1, 'name': u'David M. Blei', 'id': 5}, {'frequency': 4, 'name': u'Galley', 'id': 6}, {'frequency': 11, 'name': u'Latent Dirichlet allocation', 'id': 7}, {'frequency': 1, 'name': u'Google', 'id': 8}, {'frequency': 1, 'name': u'n-gram', 'id': 9}, {'frequency': 4, 'name': u'Stargate SG-1', 'id': 10}, {'frequency': 3, 'name': u'SG postcode area', 'id': 11}], 'edges': [{'source': 3, 'target': 1, 'cooccurrences': 1}, {'source': 6, 'target': 7, 'cooccurrences': 2}, {'source': 2, 'target': 1, 'cooccurrences': 1}, {'source': 2, 'target': 3, 'cooccurrences': 3}, {'source': 8, 'target': 9, 'cooccurrences': 1}, {'source': 10, 'target': 11, 'cooccurrences': 1}, {'source': 5, 'target': 7, 'cooccurrences': 1}, {'source': 5, 'target': 6, 'cooccurrences': 1}, {'source': 4, 'target': 1, 'cooccurrences': 1}, {'source': 0, 'target': 1, 'cooccurrences': 1}]}


LDA_1 = {'nodes': [{'frequency': 26, 'name': u'Latent semantic indexing', 'id': 0}, {'frequency': 1, 'name': u'Random projection', 'id': 1}, {'frequency': 30, 'name': u'Integrated circuit', 'id': 2}, {'frequency': 1, 'name': u'Ultraviolet', 'id': 3}, {'frequency': 1, 'name': u'Iowa', 'id': 4}, {'frequency': 1, 'name': u'Artificial intelligence', 'id': 5}, {'frequency': 1, 'name': u'Matrix norm', 'id': 6}, {'frequency': 1, 'name': u'Mathematical proof', 'id': 7}, {'frequency': 3, 'name': u'Wisconsin', 'id': 8}, {'frequency': 5, 'name': u'Lemma', 'id': 9}, {'frequency': 3, 'name': u'Lyndon B. Johnson', 'id': 10}, {'frequency': 1, 'name': u'Euclidean geometry', 'id': 11}, {'frequency': 1, 'name': u'Alan M. Frieze', 'id': 12}], 'edges': [{'source': 2, 'target': 8, 'cooccurrences': 1}, {'source': 2, 'target': 9, 'cooccurrences': 1}, {'source': 0, 'target': 12, 'cooccurrences': 1}, {'source': 10, 'target': 9, 'cooccurrences': 1}, {'source': 2, 'target': 3, 'cooccurrences': 1}, {'source': 2, 'target': 4, 'cooccurrences': 1}, {'source': 2, 'target': 5, 'cooccurrences': 1}, {'source': 2, 'target': 6, 'cooccurrences': 1}, {'source': 2, 'target': 7, 'cooccurrences': 1}, {'source': 5, 'target': 6, 'cooccurrences': 1}, {'source': 11, 'target': 9, 'cooccurrences': 1}, {'source': 0, 'target': 1, 'cooccurrences': 1}, {'source': 4, 'target': 6, 'cooccurrences': 1}, {'source': 4, 'target': 5, 'cooccurrences': 1}]}
LDA_2 = {'nodes': [{'frequency': 13, 'name': u'Latent semantic indexing', 'id': 0}, {'frequency': 11, 'name': u'Expectation\u2013maximization algorithm', 'id': 1}, {'frequency': 9, 'name': u'Singular value decomposition', 'id': 2}, {'frequency': 2, 'name': u'Semantics', 'id': 3}, {'frequency': 14, 'name': u'Latent semantic analysis', 'id': 4}, {'frequency': 32, 'name': u'Probabilistic latent semantic analysis', 'id': 5}, {'frequency': 8, 'name': u'Transmission electron microscopy', 'id': 6}, {'frequency': 1, 'name': u'Gaussian noise', 'id': 7}, {'frequency': 1, 'name': u'Matrix norm', 'id': 8}, {'frequency': 1, 'name': u'Hollywood', 'id': 9}, {'frequency': 3, 'name': u'Digital terrestrial television', 'id': 10}, {'frequency': 3, 'name': u'Rwandan Genocide', 'id': 11}, {'frequency': 2, 'name': u'Kobe', 'id': 12}, {'frequency': 2, 'name': u'Bosnian War', 'id': 13}, {'frequency': 1, 'name': u'Iraq War', 'id': 14}, {'frequency': 1, 'name': u'Iraq', 'id': 15}, {'frequency': 1, 'name': u'Gulf War', 'id': 16}, {'frequency': 4, 'name': u'Emoticon', 'id': 17}, {'frequency': 1, 'name': u"People's Party", 'id': 18}, {'frequency': 1, 'name': u'Foreach loop', 'id': 19}, {'frequency': 1, 'name': u'Differential form', 'id': 20}, {'frequency': 3, 'name': u'R', 'id': 21}, {'frequency': 2, 'name': u'Medicine', 'id': 22}, {'frequency': 2, 'name': u'Chartered Institute for Securities & Investment', 'id': 23}, {'frequency': 1, 'name': u'Institute of technology', 'id': 24}, {'frequency': 1, 'name': u'United States National Library of Medicine', 'id': 25}, {'frequency': 3, 'name': u'Electromagnetism', 'id': 26}], 'edges': [{'source': 6, 'target': 1, 'cooccurrences': 1}, {'source': 6, 'target': 2, 'cooccurrences': 1}, {'source': 2, 'target': 26, 'cooccurrences': 1}, {'source': 13, 'target': 10, 'cooccurrences': 1}, {'source': 21, 'target': 23, 'cooccurrences': 2}, {'source': 21, 'target': 22, 'cooccurrences': 2}, {'source': 21, 'target': 25, 'cooccurrences': 1}, {'source': 13, 'target': 14, 'cooccurrences': 1}, {'source': 23, 'target': 25, 'cooccurrences': 1}, {'source': 23, 'target': 24, 'cooccurrences': 1}, {'source': 14, 'target': 10, 'cooccurrences': 1}, {'source': 7, 'target': 4, 'cooccurrences': 1}, {'source': 0, 'target': 4, 'cooccurrences': 1}, {'source': 0, 'target': 5, 'cooccurrences': 7}, {'source': 0, 'target': 2, 'cooccurrences': 1}, {'source': 0, 'target': 3, 'cooccurrences': 1}, {'source': 0, 'target': 1, 'cooccurrences': 1}, {'source': 22, 'target': 25, 'cooccurrences': 1}, {'source': 2, 'target': 3, 'cooccurrences': 1}, {'source': 4, 'target': 8, 'cooccurrences': 1}, {'source': 22, 'target': 24, 'cooccurrences': 1}, {'source': 5, 'target': 2, 'cooccurrences': 1}, {'source': 5, 'target': 1, 'cooccurrences': 1}, {'source': 5, 'target': 6, 'cooccurrences': 1}, {'source': 5, 'target': 4, 'cooccurrences': 3}, {'source': 4, 'target': 2, 'cooccurrences': 2}, {'source': 20, 'target': 4, 'cooccurrences': 1}, {'source': 17, 'target': 18, 'cooccurrences': 1}, {'source': 22, 'target': 23, 'cooccurrences': 2}, {'source': 12, 'target': 15, 'cooccurrences': 1}, {'source': 12, 'target': 13, 'cooccurrences': 1}, {'source': 24, 'target': 25, 'cooccurrences': 1}, {'source': 15, 'target': 16, 'cooccurrences': 1}, {'source': 21, 'target': 24, 'cooccurrences': 1}, {'source': 0, 'target': 17, 'cooccurrences': 1}, {'source': 5, 'target': 19, 'cooccurrences': 1}, {'source': 6, 'target': 26, 'cooccurrences': 1}, {'source': 9, 'target': 10, 'cooccurrences': 1}, {'source': 11, 'target': 15, 'cooccurrences': 1}, {'source': 11, 'target': 14, 'cooccurrences': 1}, {'source': 11, 'target': 13, 'cooccurrences': 2}, {'source': 11, 'target': 12, 'cooccurrences': 2}, {'source': 12, 'target': 10, 'cooccurrences': 1}, {'source': 11, 'target': 10, 'cooccurrences': 1}, {'source': 12, 'target': 16, 'cooccurrences': 1}, {'source': 11, 'target': 16, 'cooccurrences': 1}, {'source': 12, 'target': 14, 'cooccurrences': 1}, {'source': 7, 'target': 8, 'cooccurrences': 1}]}
LDA_3 = {'nodes': [{'frequency': 11, 'name': u'Expectation\u2013maximization algorithm', 'id': 0}, {'frequency': 45, 'name': u'Expectation propagation', 'id': 1}, {'frequency': 2, 'name': u'Text Retrieval Conference', 'id': 2}, {'frequency': 1, 'name': u'Monte Carlo method', 'id': 3}, {'frequency': 1, 'name': u'Holotype', 'id': 4}], 'edges': [{'source': 2, 'target': 1, 'cooccurrences': 1}, {'source': 4, 'target': 1, 'cooccurrences': 1}, {'source': 1, 'target': 3, 'cooccurrences': 1}, {'source': 0, 'target': 1, 'cooccurrences': 2}]}
LDA_4 = {'nodes': [{'frequency': 6, 'name': u'Empirical Bayes method', 'id': 0}, {'frequency': 8, 'name': u'Expectation\u2013maximization algorithm', 'id': 1}, {'frequency': 1, 'name': u'Ricardo Baeza-Yates', 'id': 2}, {'frequency': 3, 'name': u'Information retrieval', 'id': 3}, {'frequency': 1, 'name': u'Web search engine', 'id': 4}, {'frequency': 13, 'name': u'Latent semantic indexing', 'id': 5}, {'frequency': 9, 'name': u'Bayesian inference', 'id': 6}, {'frequency': 26, 'name': u'Probabilistic latent semantic analysis', 'id': 7}, {'frequency': 21, 'name': u'Dirichlet distribution', 'id': 8}, {'frequency': 1, 'name': u'Gamma function', 'id': 9}, {'frequency': 1, 'name': u'Morris', 'id': 10}, {'frequency': 62, 'name': u'Latent Dirichlet allocation', 'id': 11}, {'frequency': 1, 'name': u"Laplace's method", 'id': 12}, {'frequency': 2, 'name': u'Markov chain Monte Carlo', 'id': 13}, {'frequency': 1, 'name': u'Abramowitz and Stegun', 'id': 14}, {'frequency': 1, 'name': u'Taylor series', 'id': 15}, {'frequency': 3, 'name': u'Memphis', 'id': 16}, {'frequency': 1, 'name': u'Hessian matrix', 'id': 17}, {'frequency': 1, 'name': u"Newton's method", 'id': 18}, {'frequency': 1, 'name': u'Caenorhabditis elegans', 'id': 19}, {'frequency': 3, 'name': u'Associated Press', 'id': 20}, {'frequency': 4, 'name': u'Support vector machine', 'id': 21}, {'frequency': 1, 'name': u'Pierre-Simon Laplace', 'id': 22}, {'frequency': 1, 'name': u'Monte Carlo method', 'id': 23}, {'frequency': 1, 'name': u'Jordan', 'id': 24}, {'frequency': 1, 'name': u'Hidden Markov model', 'id': 25}], 'edges': [{'source': 19, 'target': 20, 'cooccurrences': 1}, {'source': 8, 'target': 11, 'cooccurrences': 4}, {'source': 25, 'target': 11, 'cooccurrences': 1}, {'source': 13, 'target': 11, 'cooccurrences': 1}, {'source': 16, 'target': 17, 'cooccurrences': 1}, {'source': 10, 'target': 0, 'cooccurrences': 1}, {'source': 8, 'target': 1, 'cooccurrences': 1}, {'source': 0, 'target': 6, 'cooccurrences': 3}, {'source': 11, 'target': 6, 'cooccurrences': 1}, {'source': 14, 'target': 15, 'cooccurrences': 1}, {'source': 16, 'target': 18, 'cooccurrences': 1}, {'source': 8, 'target': 9, 'cooccurrences': 1}, {'source': 17, 'target': 8, 'cooccurrences': 1}, {'source': 18, 'target': 8, 'cooccurrences': 1}, {'source': 7, 'target': 11, 'cooccurrences': 4}, {'source': 2, 'target': 3, 'cooccurrences': 1}, {'source': 16, 'target': 8, 'cooccurrences': 1}, {'source': 5, 'target': 3, 'cooccurrences': 1}, {'source': 5, 'target': 7, 'cooccurrences': 3}, {'source': 5, 'target': 6, 'cooccurrences': 1}, {'source': 22, 'target': 23, 'cooccurrences': 1}, {'source': 4, 'target': 3, 'cooccurrences': 1}, {'source': 24, 'target': 11, 'cooccurrences': 1}, {'source': 0, 'target': 1, 'cooccurrences': 2}, {'source': 17, 'target': 18, 'cooccurrences': 1}, {'source': 1, 'target': 11, 'cooccurrences': 3}, {'source': 21, 'target': 11, 'cooccurrences': 2}, {'source': 0, 'target': 11, 'cooccurrences': 2}, {'source': 5, 'target': 11, 'cooccurrences': 2}, {'source': 12, 'target': 13, 'cooccurrences': 1}, {'source': 12, 'target': 11, 'cooccurrences': 1}]}
LDA_5 = {'nodes': [{'frequency': 9, 'name': u'Proceedings of the National Academy of Sciences of the United States of America', 'id': 0}, {'frequency': 2, 'name': u'Bayes factor', 'id': 1}, {'frequency': 4, 'name': u'Markov chain Monte Carlo', 'id': 2}, {'frequency': 8, 'name': u'Latent Dirichlet allocation', 'id': 3}, {'frequency': 9, 'name': u'Dirichlet distribution', 'id': 4}, {'frequency': 5, 'name': u'Markov chain', 'id': 5}, {'frequency': 4, 'name': u'Variational Bayesian methods', 'id': 6}, {'frequency': 14, 'name': u'Gibbs sampling', 'id': 7}, {'frequency': 2, 'name': u'Perplexity', 'id': 8}, {'frequency': 4, 'name': u'Partition coefficient', 'id': 9}, {'frequency': 3, 'name': u'Ecology', 'id': 10}, {'frequency': 1, 'name': u'Biochemical Pharmacology', 'id': 11}, {'frequency': 3, 'name': u'Economics', 'id': 12}, {'frequency': 4, 'name': u'Social science', 'id': 13}, {'frequency': 2, 'name': u'Mathematics', 'id': 14}, {'frequency': 1, 'name': u'Anthropology', 'id': 15}, {'frequency': 2, 'name': u'Psychology', 'id': 16}, {'frequency': 2, 'name': u'Biology', 'id': 17}, {'frequency': 2, 'name': u'Evolution', 'id': 18}, {'frequency': 1, 'name': u'Engineering mathematics', 'id': 19}, {'frequency': 2, 'name': u'Chemistry', 'id': 20}, {'frequency': 3, 'name': u'Applied mathematics', 'id': 21}, {'frequency': 3, 'name': u'Physics', 'id': 22}, {'frequency': 1, 'name': u'Geology', 'id': 23}], 'edges': [{'source': 12, 'target': 0, 'cooccurrences': 1}, {'source': 6, 'target': 7, 'cooccurrences': 3}, {'source': 13, 'target': 18, 'cooccurrences': 1}, {'source': 10, 'target': 20, 'cooccurrences': 1}, {'source': 19, 'target': 20, 'cooccurrences': 1}, {'source': 6, 'target': 3, 'cooccurrences': 1}, {'source': 13, 'target': 0, 'cooccurrences': 1}, {'source': 10, 'target': 22, 'cooccurrences': 1}, {'source': 22, 'target': 12, 'cooccurrences': 1}, {'source': 15, 'target': 16, 'cooccurrences': 1}, {'source': 20, 'target': 12, 'cooccurrences': 1}, {'source': 21, 'target': 22, 'cooccurrences': 2}, {'source': 15, 'target': 13, 'cooccurrences': 1}, {'source': 13, 'target': 14, 'cooccurrences': 2}, {'source': 10, 'target': 0, 'cooccurrences': 1}, {'source': 13, 'target': 16, 'cooccurrences': 1}, {'source': 0, 'target': 7, 'cooccurrences': 1}, {'source': 13, 'target': 22, 'cooccurrences': 1}, {'source': 16, 'target': 18, 'cooccurrences': 1}, {'source': 11, 'target': 0, 'cooccurrences': 1}, {'source': 18, 'target': 20, 'cooccurrences': 1}, {'source': 21, 'target': 13, 'cooccurrences': 1}, {'source': 17, 'target': 10, 'cooccurrences': 2}, {'source': 3, 'target': 7, 'cooccurrences': 1}, {'source': 0, 'target': 1, 'cooccurrences': 1}, {'source': 2, 'target': 3, 'cooccurrences': 1}, {'source': 14, 'target': 22, 'cooccurrences': 1}, {'source': 0, 'target': 3, 'cooccurrences': 1}, {'source': 5, 'target': 2, 'cooccurrences': 1}, {'source': 10, 'target': 21, 'cooccurrences': 1}, {'source': 4, 'target': 3, 'cooccurrences': 2}, {'source': 23, 'target': 13, 'cooccurrences': 1}, {'source': 8, 'target': 9, 'cooccurrences': 1}, {'source': 19, 'target': 21, 'cooccurrences': 1}, {'source': 10, 'target': 16, 'cooccurrences': 1}, {'source': 4, 'target': 5, 'cooccurrences': 1}, {'source': 21, 'target': 20, 'cooccurrences': 1}, {'source': 19, 'target': 12, 'cooccurrences': 1}, {'source': 10, 'target': 18, 'cooccurrences': 2}, {'source': 17, 'target': 18, 'cooccurrences': 2}, {'source': 18, 'target': 13, 'cooccurrences': 1}, {'source': 10, 'target': 14, 'cooccurrences': 2}, {'source': 17, 'target': 14, 'cooccurrences': 1}, {'source': 14, 'target': 0, 'cooccurrences': 1}, {'source': 17, 'target': 16, 'cooccurrences': 1}, {'source': 18, 'target': 21, 'cooccurrences': 1}, {'source': 10, 'target': 11, 'cooccurrences': 1}, {'source': 10, 'target': 12, 'cooccurrences': 1}, {'source': 10, 'target': 13, 'cooccurrences': 3}, {'source': 16, 'target': 23, 'cooccurrences': 1}, {'source': 16, 'target': 22, 'cooccurrences': 1}, {'source': 16, 'target': 21, 'cooccurrences': 1}, {'source': 16, 'target': 20, 'cooccurrences': 1}, {'source': 17, 'target': 13, 'cooccurrences': 2}, {'source': 12, 'target': 13, 'cooccurrences': 1}, {'source': 13, 'target': 20, 'cooccurrences': 1}, {'source': 21, 'target': 12, 'cooccurrences': 1}, {'source': 18, 'target': 22, 'cooccurrences': 1}, {'source': 21, 'target': 14, 'cooccurrences': 1}, {'source': 23, 'target': 18, 'cooccurrences': 1}, {'source': 23, 'target': 14, 'cooccurrences': 1}, {'source': 19, 'target': 22, 'cooccurrences': 1}, {'source': 16, 'target': 13, 'cooccurrences': 1}, {'source': 23, 'target': 22, 'cooccurrences': 1}, {'source': 14, 'target': 20, 'cooccurrences': 1}, {'source': 16, 'target': 14, 'cooccurrences': 1}, {'source': 10, 'target': 23, 'cooccurrences': 1}, {'source': 18, 'target': 14, 'cooccurrences': 1}, {'source': 20, 'target': 22, 'cooccurrences': 2}, {'source': 23, 'target': 21, 'cooccurrences': 1}, {'source': 23, 'target': 20, 'cooccurrences': 1}, {'source': 17, 'target': 20, 'cooccurrences': 1}, {'source': 17, 'target': 21, 'cooccurrences': 1}, {'source': 17, 'target': 22, 'cooccurrences': 1}, {'source': 17, 'target': 23, 'cooccurrences': 1}, {'source': 11, 'target': 13, 'cooccurrences': 1}, {'source': 11, 'target': 12, 'cooccurrences': 1}, {'source': 20, 'target': 21, 'cooccurrences': 1}, {'source': 12, 'target': 14, 'cooccurrences': 1}, {'source': 11, 'target': 14, 'cooccurrences': 1}]}
LDA_6 = {'nodes': [{'frequency': 1, 'name': u'Hierarchy', 'id': 0}, {'frequency': 2, 'name': u'China', 'id': 1}, {'frequency': 1, 'name': u'Restaurant', 'id': 2}, {'frequency': 12, 'name': u'Chinese restaurant process', 'id': 3}, {'frequency': 2, 'name': u'Bayesian inference', 'id': 4}, {'frequency': 1, 'name': u'Normal distribution', 'id': 5}, {'frequency': 1, 'name': u'Hidden Markov model', 'id': 6}, {'frequency': 6, 'name': u'Dirichlet distribution', 'id': 7}, {'frequency': 12, 'name': u'Latent Dirichlet allocation', 'id': 8}, {'frequency': 6, 'name': u'Bayes factor', 'id': 9}, {'frequency': 19, 'name': u'C-reactive protein', 'id': 10}, {'frequency': 9, 'name': u'Gibbs sampling', 'id': 11}, {'frequency': 1, 'name': u"Bayes' theorem", 'id': 12}, {'frequency': 1, 'name': u'k\xb7p perturbation theory', 'id': 13}], 'edges': [{'source': 13, 'target': 9, 'cooccurrences': 1}, {'source': 11, 'target': 10, 'cooccurrences': 2}, {'source': 3, 'target': 4, 'cooccurrences': 1}, {'source': 8, 'target': 10, 'cooccurrences': 4}, {'source': 8, 'target': 9, 'cooccurrences': 1}, {'source': 5, 'target': 6, 'cooccurrences': 1}, {'source': 13, 'target': 10, 'cooccurrences': 1}, {'source': 9, 'target': 10, 'cooccurrences': 5}, {'source': 7, 'target': 8, 'cooccurrences': 1}, {'source': 11, 'target': 9, 'cooccurrences': 1}, {'source': 11, 'target': 8, 'cooccurrences': 1}, {'source': 12, 'target': 10, 'cooccurrences': 1}, {'source': 0, 'target': 1, 'cooccurrences': 1}, {'source': 0, 'target': 2, 'cooccurrences': 1}, {'source': 1, 'target': 2, 'cooccurrences': 1}]}
LDA_7 = {'nodes': [{'frequency': 2, 'name': u'Statistical inference', 'id': 0}, {'frequency': 10, 'name': u'Dirichlet distribution', 'id': 1}, {'frequency': 20, 'name': u'Variational Bayesian methods', 'id': 2}, {'frequency': 1, 'name': u'Algorithm', 'id': 3}, {'frequency': 7, 'name': u'Latent Dirichlet allocation', 'id': 4}, {'frequency': 2, 'name': u'Bayesian network', 'id': 5}, {'frequency': 21, 'name': u'Gibbs sampling', 'id': 6}, {'frequency': 3, 'name': u'Bayesian inference', 'id': 7}, {'frequency': 2, 'name': u'EP', 'id': 8}, {'frequency': 1, 'name': u'Markov chain', 'id': 9}, {'frequency': 1, 'name': u'Approximate inference', 'id': 10}, {'frequency': 12, 'name': u'Normal distribution', 'id': 11}, {'frequency': 2, 'name': u'Taylor series', 'id': 12}, {'frequency': 2, 'name': u"Democratic People's Republic of Korea", 'id': 13}, {'frequency': 11, 'name': u'Visual Basic', 'id': 14}, {'frequency': 1, 'name': u'Hidden Markov model', 'id': 15}, {'frequency': 1, 'name': u'Mixture model', 'id': 16}], 'edges': [{'source': 13, 'target': 6, 'cooccurrences': 2}, {'source': 8, 'target': 6, 'cooccurrences': 1}, {'source': 1, 'target': 5, 'cooccurrences': 1}, {'source': 1, 'target': 4, 'cooccurrences': 2}, {'source': 1, 'target': 3, 'cooccurrences': 1}, {'source': 13, 'target': 14, 'cooccurrences': 2}, {'source': 0, 'target': 2, 'cooccurrences': 2}, {'source': 0, 'target': 3, 'cooccurrences': 1}, {'source': 11, 'target': 1, 'cooccurrences': 1}, {'source': 0, 'target': 1, 'cooccurrences': 1}, {'source': 6, 'target': 14, 'cooccurrences': 3}, {'source': 9, 'target': 6, 'cooccurrences': 1}, {'source': 2, 'target': 3, 'cooccurrences': 1}, {'source': 2, 'target': 4, 'cooccurrences': 2}, {'source': 2, 'target': 6, 'cooccurrences': 5}, {'source': 15, 'target': 4, 'cooccurrences': 1}, {'source': 4, 'target': 6, 'cooccurrences': 1}, {'source': 4, 'target': 5, 'cooccurrences': 2}, {'source': 8, 'target': 2, 'cooccurrences': 2}, {'source': 1, 'target': 10, 'cooccurrences': 1}, {'source': 1, 'target': 16, 'cooccurrences': 1}, {'source': 1, 'target': 15, 'cooccurrences': 1}, {'source': 1, 'target': 2, 'cooccurrences': 1}, {'source': 1, 'target': 7, 'cooccurrences': 1}, {'source': 11, 'target': 12, 'cooccurrences': 1}, {'source': 11, 'target': 14, 'cooccurrences': 1}]}
LDA_8 = {'nodes': [{'frequency': 2, 'name': u'Science', 'id': 0}, {'frequency': 10, 'name': u'Chemical transport model', 'id': 1}, {'frequency': 15, 'name': u'Latent Dirichlet allocation', 'id': 2}, {'frequency': 6, 'name': u'Dirichlet distribution', 'id': 3}, {'frequency': 3, 'name': u'JSTOR', 'id': 4}, {'frequency': 1, 'name': u'Science', 'id': 5}, {'frequency': 12, 'name': u'Cell Transmission Model', 'id': 6}, {'frequency': 8, 'name': u'Linear discriminant analysis', 'id': 7}], 'edges': [{'source': 3, 'target': 2, 'cooccurrences': 4}, {'source': 7, 'target': 6, 'cooccurrences': 5}, {'source': 1, 'target': 2, 'cooccurrences': 2}, {'source': 0, 'target': 4, 'cooccurrences': 1}, {'source': 0, 'target': 1, 'cooccurrences': 1}, {'source': 0, 'target': 2, 'cooccurrences': 1}, {'source': 5, 'target': 6, 'cooccurrences': 1}]}

#community_detection(network_data_2)
#Json_list_to_single_Json([LDA_1,LDA_2,LDA_3,LDA_4,LDA_5,LDA_6,LDA_7,LDA_8], 1)


#generate_summarization([LDA_1,LDA_2,LDA_3,LDA_4,LDA_5,LDA_6,LDA_7,LDA_8], 1)