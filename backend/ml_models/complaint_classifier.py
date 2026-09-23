"""
Complaint Auto-Classification Model
Supports both old (vectorizer+model) and new (pipeline) pkl structures.
"""

import pickle
import re
import numpy as np

class ComplaintClassifier:
    def __init__(self):
        self.pipeline   = None   # new-style (sklearn Pipeline)
        self.vectorizer = None   # old-style fallback
        self.model      = None   # old-style fallback
        self.categories = ['academic','infrastructure','administrative',
                           'technical','hostel','transport','other']

    def preprocess_text(self, text):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', ' ', text)
        return re.sub(r'\s+', ' ', text).strip()

    def predict(self, complaint_text):
        """Predict category — works with both pipeline and vectorizer+model pkls."""
        text = self.preprocess_text(complaint_text)

        # ── New-style pkl (has pipeline attribute) ────────────────
        if hasattr(self, 'pipeline') and self.pipeline is not None:
            proba   = self.pipeline.predict_proba([text])[0]
            classes = self.pipeline.classes_
            top_idx = proba.argsort()[::-1]
            return {
                'category':   classes[top_idx[0]],
                'confidence': float(proba[top_idx[0]]),
                'top_3': [
                    {'category': classes[i], 'confidence': float(proba[i])}
                    for i in top_idx[:3]
                ]
            }

        # ── Old-style pkl (has vectorizer + model) ────────────────
        if hasattr(self, 'vectorizer') and self.vectorizer is not None:
            X = self.vectorizer.transform([text])
            category = self.model.predict(X)[0]
            probabilities = self.model.predict_proba(X)[0]
            top_3_idx = probabilities.argsort()[-3:][::-1]
            return {
                'category':   category,
                'confidence': float(probabilities.max()),
                'top_3': [
                    {'category': self.model.classes_[i], 'confidence': float(probabilities[i])}
                    for i in top_3_idx
                ]
            }

        # ── Fallback ──────────────────────────────────────────────
        return {'category': 'other', 'confidence': 0.0, 'top_3': []}

    def save(self, filepath='ml_models/classifier.pkl'):
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"Classifier saved to {filepath}")

    @staticmethod
    def load(filepath='ml_models/classifier.pkl'):
        with open(filepath, 'rb') as f:
            return pickle.load(f)
