"""
Sentiment Analysis Model
Analyzes the emotional tone of complaints
Helps identify frustrated users and urgent matters
"""

import pickle
from textblob import TextBlob
import re

class SentimentAnalyzer:
    def __init__(self):
        self.negative_intensifiers = [
            'very', 'extremely', 'absolutely', 'completely', 'totally',
            'utterly', 'highly', 'severely', 'badly', 'terribly'
        ]
        
        self.frustration_indicators = [
            'frustrated', 'annoyed', 'angry', 'disappointed', 'upset',
            'irritated', 'fed up', 'sick of', 'tired of', 'enough'
        ]
    
    def analyze(self, text):
        """Comprehensive sentiment analysis"""
        try:
            # TextBlob sentiment
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Additional analysis
            text_lower = text.lower()
            
            # Count intensifiers
            intensifier_count = sum(1 for word in self.negative_intensifiers if word in text_lower)
            frustration_count = sum(1 for phrase in self.frustration_indicators if phrase in text_lower)
            
            # Exclamation marks
            exclamation_count = text.count('!')
            
            # Capital letters ratio
            capital_ratio = sum(1 for c in text if c.isupper()) / len(text) if len(text) > 0 else 0
            
            # Adjust polarity based on additional factors
            adjusted_polarity = polarity
            
            if frustration_count > 0:
                adjusted_polarity -= 0.3 * frustration_count
            
            if intensifier_count > 0 and polarity < 0:
                adjusted_polarity -= 0.1 * intensifier_count
            
            if exclamation_count > 2:
                adjusted_polarity -= 0.1
            
            if capital_ratio > 0.3:
                adjusted_polarity -= 0.15
            
            # Clamp to valid range
            adjusted_polarity = max(-1, min(1, adjusted_polarity))
            
            # Determine sentiment category
            if adjusted_polarity >= 0.3:
                sentiment = 'positive'
                emoji = '😊'
            elif adjusted_polarity >= 0.1:
                sentiment = 'slightly_positive'
                emoji = '🙂'
            elif adjusted_polarity >= -0.1:
                sentiment = 'neutral'
                emoji = '😐'
            elif adjusted_polarity >= -0.3:
                sentiment = 'slightly_negative'
                emoji = '😕'
            elif adjusted_polarity >= -0.6:
                sentiment = 'negative'
                emoji = '😞'
            else:
                sentiment = 'very_negative'
                emoji = '😡'
            
            # Determine urgency based on sentiment
            if sentiment in ['very_negative', 'negative']:
                urgency = 'high'
            elif sentiment == 'slightly_negative':
                urgency = 'medium'
            else:
                urgency = 'normal'
            
            # User emotion state
            if frustration_count > 0 or sentiment == 'very_negative':
                emotion = 'frustrated'
            elif sentiment in ['negative', 'slightly_negative']:
                emotion = 'dissatisfied'
            elif sentiment == 'neutral':
                emotion = 'calm'
            else:
                emotion = 'satisfied'
            
            return {
                'sentiment': sentiment,
                'polarity': float(adjusted_polarity),
                'original_polarity': float(polarity),
                'subjectivity': float(subjectivity),
                'urgency_indicator': urgency,
                'emotion': emotion,
                'emoji': emoji,
                'metrics': {
                    'frustration_indicators': frustration_count,
                    'intensifiers': intensifier_count,
                    'exclamation_marks': exclamation_count,
                    'capital_ratio': float(capital_ratio)
                },
                'recommendation': self._generate_recommendation(sentiment, urgency, emotion)
            }
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            return {
                'sentiment': 'neutral',
                'polarity': 0.0,
                'urgency_indicator': 'normal',
                'emotion': 'calm',
                'emoji': '😐',
                'recommendation': 'Process as normal complaint'
            }
    
    def _generate_recommendation(self, sentiment, urgency, emotion):
        """Generate action recommendations based on sentiment"""
        if sentiment == 'very_negative':
            return "⚠️ High priority: User is very frustrated. Immediate response recommended."
        elif sentiment == 'negative':
            return "⚡ Priority handling: User is dissatisfied. Quick resolution suggested."
        elif sentiment == 'slightly_negative':
            return "👀 Monitor closely: User has concerns. Timely response needed."
        elif sentiment == 'neutral':
            return "✅ Standard processing: Handle as per normal workflow."
        else:
            return "😊 Positive feedback: May be a suggestion rather than complaint."
    
    def batch_analyze(self, texts):
        """Analyze multiple texts at once"""
        return [self.analyze(text) for text in texts]
    
    def get_satisfaction_score(self, text):
        """Get a 0-100 satisfaction score"""
        result = self.analyze(text)
        # Convert -1 to 1 polarity to 0-100 score
        score = (result['polarity'] + 1) * 50
        return round(score, 1)
    
    def save(self, filepath='ml_models/sentiment_analyzer.pkl'):
        """Save the analyzer"""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"Sentiment analyzer saved to {filepath}")
    
    @staticmethod
    def load(filepath='ml_models/sentiment_analyzer.pkl'):
        """Load a saved analyzer"""
        with open(filepath, 'rb') as f:
            return pickle.load(f)


if __name__ == "__main__":
    # Create and save analyzer
    analyzer = SentimentAnalyzer()
    analyzer.save()
    
    # Test cases
    print("="*70)
    print("TESTING SENTIMENT ANALYSIS")
    print("="*70)
    
    test_cases = [
        "I am EXTREMELY frustrated! This is the THIRD time I'm complaining about the same issue!!!",
        "The new library facilities are wonderful and very helpful for studying",
        "The WiFi keeps disconnecting. It's quite annoying.",
        "I would like to request an extension for the assignment deadline",
        "URGENT! Very disappointed with the administration's response. This is unacceptable!",
        "Thank you for resolving my previous complaint quickly",
        "The food quality is okay but could be better",
    ]
    
    for text in test_cases:
        result = analyzer.analyze(text)
        satisfaction = analyzer.get_satisfaction_score(text)
        
        print(f"\nText: {text}")
        print(f"Sentiment: {result['sentiment']} {result['emoji']}")
        print(f"Polarity: {result['polarity']:.2f} (Original: {result['original_polarity']:.2f})")
        print(f"Emotion: {result['emotion']}")
        print(f"Urgency: {result['urgency_indicator']}")
        print(f"Satisfaction Score: {satisfaction}/100")
        print(f"Metrics: {result['metrics']}")
        print(f"Recommendation: {result['recommendation']}")
        print("-" * 70)
