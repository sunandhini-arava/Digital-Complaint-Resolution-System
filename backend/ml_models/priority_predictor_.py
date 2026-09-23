"""
Priority Prediction Model
Automatically assigns priority levels: low, medium, high, urgent
Based on complaint text analysis
"""

import re
import pickle
from textblob import TextBlob

class PriorityPredictor:
    def __init__(self):
        # Keywords indicating urgency
        self.urgent_keywords = [
            'emergency', 'urgent', 'critical', 'danger', 'dangerous',
            'broken', 'leak', 'fire', 'safety', 'accident', 'injury',
            'immediately', 'asap', 'severe', 'serious', 'crisis'
        ]
        
        self.high_keywords = [
            'important', 'major', 'significant', 'problem', 'issue',
            'not working', 'malfunction', 'damage', 'fault', 'defect'
        ]
        
        self.time_sensitive = [
            'deadline', 'exam', 'today', 'tomorrow', 'soon', 'urgent',
            'interview', 'placement', 'submission'
        ]
        
        # Category-based default priorities
        self.category_priority = {
            'academic': 'medium',
            'infrastructure': 'medium',
            'administrative': 'medium',
            'technical': 'medium',
            'hostel': 'medium',
            'transport': 'medium',
            'other': 'low'
        }
    
    def extract_features(self, text):
        """Extract relevant features from text"""
        text_lower = text.lower()
        
        features = {
            'length': len(text),
            'word_count': len(text.split()),
            'urgent_word_count': sum(1 for word in self.urgent_keywords if word in text_lower),
            'high_word_count': sum(1 for word in self.high_keywords if word in text_lower),
            'time_sensitive_count': sum(1 for word in self.time_sensitive if word in text_lower),
            'exclamation_marks': text.count('!'),
            'question_marks': text.count('?'),
            'capital_ratio': sum(1 for c in text if c.isupper()) / len(text) if len(text) > 0 else 0,
            'has_urgent_words': any(word in text_lower for word in self.urgent_keywords),
            'has_high_words': any(word in text_lower for word in self.high_keywords),
            'has_time_sensitive': any(word in text_lower for word in self.time_sensitive)
        }
        
        return features
    
    def analyze_sentiment(self, text):
        """Analyze sentiment to gauge urgency"""
        try:
            blob = TextBlob(text)
            sentiment = blob.sentiment.polarity
            
            # Very negative sentiment might indicate urgency
            if sentiment < -0.5:
                return 'negative_urgent'
            elif sentiment < -0.2:
                return 'negative'
            elif sentiment > 0.2:
                return 'positive'
            else:
                return 'neutral'
        except:
            return 'neutral'
    
    def predict_priority(self, complaint_text, category=None):
        """Predict priority level"""
        features = self.extract_features(complaint_text)
        sentiment = self.analyze_sentiment(complaint_text)
        
        # Calculate priority score (0-100)
        score = 0
        
        # Urgent keywords (+40 points)
        if features['urgent_word_count'] > 0:
            score += 40 + (features['urgent_word_count'] * 10)
        
        # High priority keywords (+20 points)
        if features['high_word_count'] > 0:
            score += 20 + (features['high_word_count'] * 5)
        
        # Time sensitive (+15 points)
        if features['time_sensitive_count'] > 0:
            score += 15 + (features['time_sensitive_count'] * 5)
        
        # Exclamation marks (+5 each, max 20)
        score += min(features['exclamation_marks'] * 5, 20)
        
        # High capital ratio indicates shouting/urgency (+15)
        if features['capital_ratio'] > 0.3:
            score += 15
        
        # Negative sentiment (+10-20)
        if sentiment == 'negative_urgent':
            score += 20
        elif sentiment == 'negative':
            score += 10
        
        # Long detailed complaint might be important (+10)
        if features['word_count'] > 100:
            score += 10
        
        # Category-based adjustment
        if category:
            if category in ['infrastructure', 'hostel', 'technical']:
                score += 5  # Slightly higher priority for these
        
        # Determine priority level based on score
        if score >= 60:
            priority = 'urgent'
            confidence = min(score / 100, 0.95)
        elif score >= 35:
            priority = 'high'
            confidence = min(score / 100, 0.85)
        elif score >= 15:
            priority = 'medium'
            confidence = min(score / 100, 0.75)
        else:
            priority = 'low'
            confidence = min(score / 100 + 0.5, 0.70)
        
        return {
            'priority': priority,
            'confidence': float(confidence),
            'score': score,
            'reasoning': self._generate_reasoning(features, sentiment, score)
        }
    
    def _generate_reasoning(self, features, sentiment, score):
        """Generate human-readable reasoning for the prediction"""
        reasons = []
        
        if features['urgent_word_count'] > 0:
            reasons.append(f"Contains {features['urgent_word_count']} urgent keyword(s)")
        
        if features['time_sensitive_count'] > 0:
            reasons.append("Time-sensitive issue mentioned")
        
        if features['exclamation_marks'] > 2:
            reasons.append("Multiple exclamation marks indicate urgency")
        
        if features['capital_ratio'] > 0.3:
            reasons.append("High use of capital letters")
        
        if sentiment == 'negative_urgent':
            reasons.append("Very negative sentiment detected")
        
        if features['word_count'] > 100:
            reasons.append("Detailed description provided")
        
        if not reasons:
            reasons.append("Standard complaint characteristics")
        
        return reasons
    
    def save(self, filepath='ml_models/priority_predictor.pkl'):
        """Save the model"""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"Priority predictor saved to {filepath}")
    
    @staticmethod
    def load(filepath='ml_models/priority_predictor.pkl'):
        """Load a saved model"""
        with open(filepath, 'rb') as f:
            return pickle.load(f)


if __name__ == "__main__":
    # Create and save predictor
    predictor = PriorityPredictor()
    predictor.save()
    
    # Test predictions
    print("="*60)
    print("TESTING PRIORITY PREDICTIONS")
    print("="*60)
    
    test_cases = [
        ("URGENT! Fire alarm not working in hostel. This is a SERIOUS safety issue!", "infrastructure"),
        ("The WiFi is a bit slow in the library", "technical"),
        ("Assignment submission deadline is tomorrow and portal is not working!", "technical"),
        ("Would like to suggest improving the canteen menu", "other"),
        ("EMERGENCY: Broken stairs near Block C - someone might get injured!!!", "infrastructure"),
        ("Professor explained the topic well but I still have some doubts", "academic"),
    ]
    
    for text, category in test_cases:
        result = predictor.predict_priority(text, category)
        print(f"\nComplaint: {text[:80]}...")
        print(f"Category: {category}")
        print(f"Priority: {result['priority'].upper()} (confidence: {result['confidence']:.2%})")
        print(f"Score: {result['score']}")
        print(f"Reasoning: {', '.join(result['reasoning'])}")
        print("-" * 60)
