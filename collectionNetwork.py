# -*- coding: utf-8 -*-
import itertools
from settings import APP_STATIC
import json
def generate_network (paper_scene_list):
    # 1. sort the paper and its scenes by year and month
    paper_scene_list.sort(key=lambda x: (x['year'], x['month']))
    print('after sort')
    print(paper_scene_list)

    # 2. get all nodes
    nodes_dict = {}
    edges_dict = {}
    paper_dict = {}
    curr_entity_id = 0
    curr_paper_id = 0
    id_list = []

    for paper in paper_scene_list: # for each paper
        for index, scene in enumerate(paper['sentence_scenes']): # for each scene
            if len(scene) > 1:  # if there are at least 2 entities in a sentence
                for entity in scene:
                    entity = str(entity)
                    if entity not in nodes_dict:
                        entity_info = {}
                        entity_info['nodeName'] = entity
                        entity_info['id'] = curr_entity_id
                        entity_info['group'] = curr_paper_id
                        entity_info['frequency'] = 1
                        nodes_dict[entity] = entity_info
                        id_list.append(curr_entity_id)
                        curr_entity_id += 1
                    else:
                        nodes_dict[entity]['frequency'] += 1
                # generate all pairs of entities of the scene
                all_pairs = list(itertools.combinations(range(len(scene)), 2))  # get all possible index pairs for the characters in teh scene
                for pair in all_pairs:
                    key1 = scene[pair[0]]
                    key1 = str(key1)
                    key1 = key1.encode("utf-8")
                    print(key1)
                    key2 = scene[pair[1]]
                    key2 = str(key2)
                    key2 = key2.encode("utf-8")
                    print(key2)
                    source = nodes_dict[key1]['id']
                    target = nodes_dict[key2]['id']
                    sentence = paper['sentence_scenes_info'][index]['text']
                    title = paper['title']
                    sentence_info = {}
                    sentence_info['sentence'] = sentence
                    sentence_info['title'] = title
                    key = str(source) + '_' + str(target)  # source_target

                    if key in edges_dict:
                        edges_dict[key]['value'] += 1
                        edges_dict[key]['weight'] += 1
                        edges_dict[key]['sentences'].append(sentence_info)
                        edges_dict[key]['pure_titles'].append(title) #used for path mouseover test relating to all relevant paper titles

                    else:
                        pair_entry = {}  # 0=source, 1=target, 2=source_target, 3=frequency
                        pair_entry['source'] = source  # source
                        pair_entry['target'] = target  # target
                        pair_entry['value'] = 1
                        pair_entry['weight'] = 1
                        sentences = []
                        sentences.append(sentence_info)
                        pair_entry['sentences'] = sentences
                        pure_titles = []
                        pure_titles.append(title)
                        pair_entry['pure_titles'] = pure_titles
                        edges_dict[key] = pair_entry
        paper_info = {}
        paper_info['id'] = curr_paper_id
        paper_info['title'] = paper['title']
        paper_dict[curr_paper_id] = paper_info
        curr_paper_id += 1





    nodes = nodes_dict.values()
    edges = edges_dict.values()
    papers = paper_dict.values()
    # sort the nodes based on their ids (d3 force layout only track id based on the order of nodes appear, not by id you give)
    from operator import itemgetter
    nodes = sorted(nodes, key=itemgetter('id'))
    print('the nodes =')
    print(nodes)
    print('the edge dict = ')
    print(edges_dict)
    network_data = {}
    network_data['nodes'] = nodes
    network_data['links'] = edges
    network_data['papers'] = papers
    network_data['id_list'] = id_list


    file_name = 'whole_network'
    with open(APP_STATIC + '/data/' + file_name + '.json', 'w') as fp:
        json.dump(network_data, fp)

    return network_data
