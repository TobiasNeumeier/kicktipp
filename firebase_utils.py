import os

import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd

root_dir = os.path.dirname(os.path.abspath(__file__))
service_account_path = os.path.join(root_dir, 'service_account_key.json')

# Initialize Firebase Admin SDK
cred = credentials.Certificate(service_account_path)
firebase_admin.initialize_app(cred)
db = firestore.client()


def write_dataframe_to_firestore(df, collection_name):
    """
    Write a pandas DataFrame to Firestore.

    :param df: pandas DataFrame to write.
    :param collection_name: Firestore collection name.
    """
    
    collection_ref = db.collection(collection_name)
    for index, row in df.iterrows():
        doc_ref = collection_ref.document(str(index))
        doc_ref.set(row.to_dict())


def read_dataframe_from_firestore(collection_name):
    """
    Read a Firestore collection into a pandas DataFrame.

    :param collection_name: Firestore collection name.
    :return: pandas DataFrame with the data.
    """
    collection_ref = db.collection(collection_name)
    docs = collection_ref.stream()
    data = []
    for doc in docs:
        data.append(doc.to_dict())
    return pd.DataFrame(data)
