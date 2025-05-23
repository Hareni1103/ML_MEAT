# -*- coding: utf-8 -*-
"""Untitled27.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1VlU88OoYyw6ocDJ-RKxan-lzszm-PCPX
"""

import pandas as pd
import streamlit as st
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import numpy as np
from io import BytesIO
import joblib

st.title("Fine-tuned Product Classifier")
st.write("Upload labeled training file and new input + rules files. Model will be trained and used for accurate predictions.")

# Load model
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

sbert_model = load_model()

# Upload labeled training file
train_file = st.file_uploader("Upload Labeled Training File (.xlsx)", type=["xlsx"])

# Upload files for prediction
input_file = st.file_uploader("Upload New Input File (.xlsx)", type=["xlsx"])
rules_file = st.file_uploader("Upload Rules File (.xlsx)", type=["xlsx"])

if train_file and input_file and rules_file:
    # Load files
    train_df = pd.read_excel(train_file)
    input_df = pd.read_excel(input_file)
    rules_df = pd.read_excel(rules_file)

    # Preprocessing
    train_df['Best Received External Description'] = train_df['Best Received External Description'].astype(str).str.upper()
    train_df['Consolidated nan descript'] = train_df['Consolidated nan descript'].astype(str).str.upper()
    input_df['Best Received External Description'] = input_df['Best Received External Description'].astype(str).str.upper()
    rules_df['Exclude Retailer description'] = rules_df['Exclude Retailer description'].astype(str).str.upper()

    # Encode training descriptions
    X_train = sbert_model.encode(train_df['Best Received External Description'].tolist())
    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(train_df['Consolidated nan descript'])

    # Train classifier
    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, y_train)

    # Exclude check
    exclude_keywords = rules_df['Exclude Retailer description'].dropna().unique().tolist()

    predictions = []
    confidences = []

    for desc in input_df['Best Received External Description']:
        if any(ex_kw in desc for ex_kw in exclude_keywords):
            predictions.append("Exclude")
            confidences.append(100.0)
        else:
            vec = sbert_model.encode([desc])
            probas = clf.predict_proba(vec)[0]
            max_idx = np.argmax(probas)
            predicted_label = label_encoder.inverse_transform([max_idx])[0]
            confidence = round(probas[max_idx] * 100, 2)
            predictions.append(predicted_label)
            confidences.append(confidence)

    input_df['Predicted Consolidated nan descript'] = predictions
    input_df['Confidence (%)'] = confidences

    st.subheader("Predicted Results")
    st.dataframe(input_df[['Best Received External Description', 'Predicted Consolidated nan descript', 'Confidence (%)']])

    # Download predictions
    output = BytesIO()
    input_df.to_excel(output, index=False, engine='openpyxl')
    st.download_button(
        label="Download Results as Excel",
        data=output.getvalue(),
        file_name="fine_tuned_predictions.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )