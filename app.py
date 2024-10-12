# app.py

from json import dumps, loads
from flask import Flask, render_template, request, jsonify
import pandas as pd
from pymongo import MongoClient 
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from bson.objectid import ObjectId
import config

app = Flask(__name__)

uri = config.mongo['uri']

# Create a new client and connect to the server
client = MongoClient(uri)

# Define a TF-IDF Vectorizer. Remove all English stop words such as 'the', 'a'
tfidf = TfidfVectorizer(stop_words='english')

#Cosine similarity based on threshold
def get_recommendations(input_text, indices, cosine_sim, data, threshold=0.06):
    # Get the index of the article that matches the input
    idx = indices[input_text]

    # Get the pairwise similarity scores of all articles with that particular article
    sim_scores = list(enumerate(cosine_sim[idx]))

    # Log the similarity scores
    print("Similarity Scores:", sim_scores)

    # Filter articles with similarity scores greater than or equal to the threshold
    sim_scores_filtered = [(i, score) for i, score in sim_scores if score > threshold]

    # If there are recommendations with a similarity score of 1.0, remove them
    if len(sim_scores_filtered) > 1 and sim_scores_filtered[0][1] == 1.0:
        sim_scores_filtered = sim_scores_filtered[1:]

    # Sort the articles based on the similarity scores
    sim_scores_filtered = sorted(sim_scores_filtered, key=lambda x: x[1], reverse=True)

    # Get the indices of the similar articles
    article_indices = [i for i, _ in sim_scores_filtered]

    # Return the descriptions of the similar articles
    return data['description'].iloc[article_indices].tolist()


#get all the liked post from the collection
@app.route('/getlikerecom', methods=['GET'])
def getlikerecom():
        #get all posts
        #getting data from the database     
        db = client.Recom 
        collection = db.PostsData
        data = pd.DataFrame(list(collection.find()))#Get all records from database and convert to a dataframe
        # Construct the required TF-IDF matrix by fitting and transforming the data
        tfidf_matrix = tfidf.fit_transform(data['description'])#description is the column name in DB
        cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix,True)
        metadata = data.reset_index()
        indices = pd.Series(metadata.index, index=metadata['description']).drop_duplicates()
        #uses get_recommendation function and calculates cosine similarity
    
        # Get userId from the URL parameters
        user_id = request.args.get('userId') 
        #getting data from the database    
        db = client.Recom
        collection = db.PostsData
        #get all the like posts 
        like = {"like": {'$elemMatch':{"userId":ObjectId(user_id)}}}
        #like = {"like": {"$exists": True, "$not": {"$size": 0}}}
        #  description_input=collection.find_one({'_id':ObjectId(post_id)},{'_id':0,'description':1})

        # Create a dictionary to store descriptions for each user ID
        #descriptions_by_user_id = {}
        # Fetch documents
        documents = collection.find(like) 
        print(documents)
        allrecommarr=[]
        for doc in documents:
            print("\n\nFor loop")
            print(doc)
            print(doc["description"])#finding recommendations from entire DB from like descriptions
            recommendations = get_recommendations(doc["description"], indices, cosine_sim, data)
            print("recommendations:")
            print(recommendations)
            allrecommarr+=recommendations
        #return list(loads(dumps(documents)))
        #return ""
        # Iterate over the documents
  
    
        return jsonify(list(set(allrecommarr)))#to remove the duplicate results
        
####python -m flask --app app.py run


#from pymongo.mongo_client import MongoClient

@app.route('/test_mongo_con', methods=['GET'])
def test_mongo_con():

# Create a new client and connect to the server
#    client = MongoClient(uri)

# Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        return("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        return(e)

if __name__ == '__main__':
    app.run()

