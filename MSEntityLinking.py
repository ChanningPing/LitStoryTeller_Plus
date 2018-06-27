# -*- coding: utf-8 -*-
'''
use Microsoft Entity Link API to extract entities from scientific papers.
'''
import httplib, urllib, base64

headers = {
    # Request headers
    'Content-Type': 'text/plain',
    'Ocp-Apim-Subscription-Key': 'c9a1e1d8990847fea3fbc2c9e8b80c6e',
}

params = urllib.urlencode({
    # Request parameters
    #'selection': '{string}',
    #'offset': '{string}',
})


def entityOffsets(text):
    try:
        #print('text=' + text)
        conn = httplib.HTTPSConnection('westus.api.cognitive.microsoft.com')
        conn.request("POST", "/entitylinking/v1.0/link?%s" % params, text, headers)
        response = conn.getresponse()
        data = response.read()
        #print(data)
        return data
        #print(data)
        conn.close()


    except Exception as e:
        print("[Errno {0}] {1}".format(e.errno, e.strerror))
        print("error:" + e.message)
        return "error-001:invalid-characters"




text = "In natural language processing,latent Dirichlet allocation (LDA) is a generative statistical model that allows sets of observations to be explained by unobserved groups that explain why some parts of the data are similar"
entityOffsets(text)