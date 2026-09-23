"""
Priority Predictor
Supports both old (feature engineering) and new (pipeline) pkl structures.
"""

import pickle
import re
import numpy as np

class PriorityPredictor:
    def __init__(self):
        self.pipeline = None  # new-style
        self.model    = None  # old-style
        self.urgent_keywords = [
            'urgent','emergency','immediately','asap','critical','dangerous',
            'hazardous','severe','serious','now','today','deadline','fire',
            'flood','blood','injury','collapse','accident','help'
        ]
        self.high_keywords   = ['important','broken','not working','failing',
                                 'deadline','tomorrow','exam','payment']
        self.priorities      = ['low','medium','high','urgent']

    def predict_priority(self, complaint_text, category=None):
        """Predict priority — works with both pipeline and feature-based pkls."""
        text = re.sub(r'[^a-zA-Z\s]', ' ', (complaint_text or '').lower()).strip()

        # ── New-style pkl (pipeline) ───────────────────────────────
        if hasattr(self, 'pipeline') and self.pipeline is not None:
            proba   = self.pipeline.predict_proba([text])[0]
            classes = self.pipeline.classes_
            top_idx = proba.argsort()[::-1]
            priority = classes[top_idx[0]]
            REASONING = {
                'urgent': 'Immediate safety/critical deadline risk — same-day action required.',
                'high':   'Significant impact on studies or daily life — resolve within 24-48 hours.',
                'medium': 'Moderate inconvenience — resolve within 3-5 working days.',
                'low':    'Minor suggestion — address at next available opportunity.',
            }
            return {
                'priority':   priority,
                'confidence': float(proba[top_idx[0]]),
                'reasoning':  REASONING.get(priority, ''),
                'all_scores': {classes[i]: float(proba[i]) for i in range(len(classes))}
            }

        # ── Old-style pkl (rule/feature based) ────────────────────
        urgent_count = sum(1 for w in self.urgent_keywords if w in text)
        high_count   = sum(1 for w in self.high_keywords   if w in text)
        exclamations = complaint_text.count('!')
        capitals     = sum(1 for c in (complaint_text or '') if c.isupper()) / max(len(complaint_text or ''), 1)

        if urgent_count >= 2 or exclamations >= 2 or capitals > 0.3:
            priority, conf = 'urgent', 0.80
        elif urgent_count == 1 or high_count >= 2:
            priority, conf = 'high',   0.75
        elif high_count == 1:
            priority, conf = 'medium', 0.70
        else:
            priority, conf = 'low',    0.65

        REASONING = {
            'urgent': 'Immediate safety/critical deadline risk — same-day action required.',
            'high':   'Significant impact on studies or daily life — resolve within 24-48 hours.',
            'medium': 'Moderate inconvenience — resolve within 3-5 working days.',
            'low':    'Minor suggestion — address at next available opportunity.',
        }
        return {
            'priority':   priority,
            'confidence': conf,
            'reasoning':  REASONING.get(priority, ''),
        }

    def save(self, filepath='ml_models/priority_predictor.pkl'):
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"Priority predictor saved to {filepath}")

    @staticmethod
    def load(filepath='ml_models/priority_predictor.pkl'):
        with open(filepath, 'rb') as f:
            return pickle.load(f)
