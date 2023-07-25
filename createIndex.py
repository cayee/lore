import json

import boto3
from langchain.embeddings import BedrockEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore import InMemoryDocstore
from transformers import Tool
import numpy as np

bedrock = boto3.client(
    service_name="bedrock",
    region_name="us-west-2",
    endpoint_url="https://prod.us-west-2.frontend.bedrock.aws.dev",
    #endpoint_url="https://bedrock.us-east-1.amazonaws.com",
)

texts = [
    "Born in an ancient, sorcerous catastrophe, Zyra is the wrath of nature given form—an alluring hybrid of plant and human, kindling new life with every step. She views the many mortals of Valoran as little more than prey for her seeded progeny, and thinks nothing of slaying them with flurries of deadly spines. Though her true purpose has not been revealed, Zyra wanders the world, indulging her most primal urges to colonize, and strangle all other life from it.",
    "As the embodiment of mischief, imagination, and change, Zoe acts as the cosmic messenger of Targon, heralding major events that reshape worlds. Her mere presence warps the arcane mathematics governing realities, sometimes causing cataclysms without conscious effort or malice. This perhaps explains the breezy nonchalance with which Zoe approaches her duties, giving her plenty of time to focus on playing games, tricking mortals, or otherwise amusing herself. An encounter with Zoe can be joyous and life affirming, but it is always more than it appears and often extremely dangerous.",
    "Zac is the product of a toxic spill that ran through a chemtech seam and pooled in an isolated cavern deep in Zaun’s Sump. Despite such humble origins, Zac has grown from primordial ooze into a thinking being who dwells in the city’s pipes, occasionally emerging to help those who cannot help themselves or to rebuild the broken infrastructure of Zaun.",
    "A fiend with a thirst for mortal blood, Vladimir has influenced the affairs of Noxus since the empire’s earliest days. In addition to unnaturally extending his life, his mastery of hemomancy allows him to control the minds and bodies of others as easily as his own. In the flamboyant salons of the Noxian aristocracy, this enabled him to build a fanatical cult of personality around himself—while in the lowest back alleys, it allows him to bleed his enemies dry.",
    "Once ruler of a long-lost kingdom, Viego perished over a thousand years ago when his attempt to bring his wife back from the dead triggered the magical catastrophe known as the Ruination. Transformed into a powerful, unliving wraith tortured by an obsessive longing for his centuries-dead queen, Viego now stands as the Ruined King, controlling the deadly Harrowings as he scours Runeterra for anything that might one day restore her, and destroying all in his path as the Black Mist pours endlessly from his cruel, broken heart."
]

def get_embedding(body, modelId, accept, contentType):
    response = bedrock.invoke_model(body=body, modelId=modelId, accept=accept, contentType=contentType)
    response_body = json.loads(response.get('body').read())
    embedding = response_body.get('embedding')
    return embedding

modelId = 'amazon.titan-e1t-medium'
accept = 'application/json'
contentType = 'application/json'

"""
embeddings = []
for text in texts:
    body = json.dumps({"inputText": text})
    embedding = get_embedding(body, modelId, accept, contentType)
    embeddings.append(embedding)
#embeddings = np.array(embeddings)
"""
#textEmb = [(t, e) for t, e in zip(texts, embeddings)]
be = BedrockEmbeddings()
be.client = bedrock
be.embed_documents(texts)
#import faiss
#faiss = FAISS(None, faiss.IndexFlatL2(768), InMemoryDocstore(), {})
#faiss.add_embeddings(textEmb)
docsearch = FAISS.from_texts(texts, be)
docsearch.save_local('index_faiss')
