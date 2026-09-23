"""
Complaint Auto-Classification Model
Automatically categorizes complaints into: academic, infrastructure, administrative, 
technical, hostel, transport, other
"""

import pickle
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import numpy as np

class ComplaintClassifier:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),  # Use both unigrams and bigrams
            stop_words='english'
        )
        self.model = MultinomialNB(alpha=0.1)
        self.categories = ['academic', 'infrastructure', 'administrative', 
                          'technical', 'hostel', 'transport', 'other']
    
    def preprocess_text(self, text):
        """Clean and preprocess text"""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)  # Remove special chars
        text = re.sub(r'\s+', ' ', text)  # Remove extra spaces
        return text.strip()
    
    def train(self, complaints, categories):
        """Train the classifier"""
        # Preprocess
        processed_complaints = [self.preprocess_text(c) for c in complaints]
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            processed_complaints, categories, test_size=0.2, random_state=42
        )
        
        # Vectorize
        X_train_vec = self.vectorizer.fit_transform(X_train)
        X_test_vec = self.vectorizer.transform(X_test)
        
        # Train
        self.model.fit(X_train_vec, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_vec)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"Model Accuracy: {accuracy * 100:.2f}%")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        return accuracy
    
    def predict(self, complaint_text):
        """Predict category for a complaint"""
        processed = self.preprocess_text(complaint_text)
        X = self.vectorizer.transform([processed])
        
        # Get prediction and probabilities
        category = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        confidence = probabilities.max()
        
        # Get top 3 predictions
        top_3_indices = probabilities.argsort()[-3:][::-1]
        top_3_predictions = [
            {
                'category': self.model.classes_[i],
                'confidence': float(probabilities[i])
            }
            for i in top_3_indices
        ]
        
        return {
            'category': category,
            'confidence': float(confidence),
            'top_3': top_3_predictions
        }
    
    def save(self, filepath='ml_models/classifier.pkl'):
        """Save the trained model"""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"Model saved to {filepath}")
    
    @staticmethod
    def load(filepath='ml_models/classifier.pkl'):
        """Load a trained model"""
        with open(filepath, 'rb') as f:
            return pickle.load(f)


if __name__ == "__main__":
    # Example training data
    training_data = [
        # Academic
        ("Professor is always late to class and doesn't cover syllabus", "academic"),
        ("Need help with understanding the calculus concepts", "academic"),
        ("Assignment deadline should be extended due to exams", "academic"),
        ("Question paper was too difficult compared to what was taught", "academic"),
        ("Teacher doesn't respond to emails regarding doubts", "academic"),
        
        # Infrastructure
        ("Broken fan in classroom 301", "infrastructure"),
        ("Leaking pipe in hostel bathroom", "infrastructure"),
        ("Air conditioning not working in library", "infrastructure"),
        ("Damaged desks in computer lab", "infrastructure"),
        ("Poor lighting in corridor near admin block", "infrastructure"),
        
        # Administrative
        ("Transcript request taking too long to process", "administrative"),
        ("Fee receipt not generated after payment", "administrative"),
        ("Unable to access student portal for registration", "administrative"),
        ("Need NOC for passport application", "administrative"),
        ("Delay in scholarship disbursement", "administrative"),
        
        # Technical
        ("WiFi not working in hostel", "technical"),
        ("Computer lab systems are very slow", "technical"),
        ("Cannot access online learning portal", "technical"),
        ("Printer in library is not functioning", "technical"),
        ("Campus app keeps crashing", "technical"),
        
        # Hostel
        ("Roommate is creating disturbance late at night", "hostel"),
        ("Food quality in mess is very poor", "hostel"),
        ("Hot water not available in morning", "hostel"),
        ("Room cleaning is not done regularly", "hostel"),
        ("Need permission for late night entry", "hostel"),
        
        # Transport
        ("College bus is always late", "transport"),
        ("Bus route doesn't cover my area", "transport"),
        ("Overcrowding in morning bus", "transport"),
        ("Bus driver drives rashly", "transport"),
        ("Need additional bus for evening route", "transport"),
        
        # Other
        ("Stray dogs in campus are dangerous", "other"),
        ("Canteen prices are too high", "other"),
        ("No parking space available", "other"),
        ("Sports equipment needs replacement", "other"),
        ("Medical facility timings should be extended", "other"),
    ]
    
    # Extract texts and labels
    texts = [text for text, _ in training_data]
    labels = [label for _, label in training_data]
    
    # Create and train model
    classifier = ComplaintClassifier()
    classifier.train(texts, labels)
    
    # Save model
    classifier.save()
    
    # Test predictions
    print("\n" + "="*60)
    print("TESTING PREDICTIONS")
    print("="*60)
    
    test_cases = [
        "The internet connection in my dorm room keeps disconnecting",
        "Professor doesn't explain concepts clearly",
        "Broken window in classroom needs fixing",
        "My exam results are not showing in the portal"
    ]
    
    for test in test_cases:
        result = classifier.predict(test)
        print(f"\nComplaint: {test}")
        print(f"Predicted: {result['category']} (confidence: {result['confidence']:.2%})")
        print(f"Top 3: {result['top_3']}")
