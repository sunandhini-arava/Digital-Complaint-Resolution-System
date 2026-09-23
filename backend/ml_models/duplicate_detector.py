"""
Duplicate Complaint Detector
Finds similar existing complaints to prevent duplicates
Uses TF-IDF and cosine similarity
"""

import pickle
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class DuplicateDetector:
    def __init__(self, similarity_threshold=0.65):
        self.vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            stop_words='english',
            min_df=1
        )
        self.similarity_threshold = similarity_threshold
        self.complaint_vectors = None
        self.complaint_data = []
    
    def preprocess_text(self, text):
        """Clean text for comparison"""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def index_complaints(self, complaints):
        """
        Index existing complaints for fast similarity search
        complaints: list of dicts with 'id', 'title', 'description', 'category'
        """
        if not complaints:
            return
        
        self.complaint_data = complaints
        
        # Combine title and description for better matching
        texts = [
            self.preprocess_text(f"{c['title']} {c['description']}")
            for c in complaints
        ]
        
        # Create TF-IDF vectors
        self.complaint_vectors = self.vectorizer.fit_transform(texts)
        
        print(f"Indexed {len(complaints)} complaints for duplicate detection")
    
    def find_similar(self, new_complaint_text, category=None, top_k=5):
        """
        Find similar complaints to the new one
        Returns list of similar complaints with similarity scores
        """
        if self.complaint_vectors is None or len(self.complaint_data) == 0:
            return {
                'has_duplicates': False,
                'similar_complaints': [],
                'message': 'No existing complaints to compare'
            }
        
        # Preprocess new complaint
        processed_text = self.preprocess_text(new_complaint_text)
        
        # Vectorize new complaint
        new_vector = self.vectorizer.transform([processed_text])
        
        # Calculate similarities
        similarities = cosine_similarity(new_vector, self.complaint_vectors)[0]
        
        # Get top similar complaints
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        similar_complaints = []
        for idx in top_indices:
            similarity = similarities[idx]
            
            # Only include if above threshold
            if similarity >= self.similarity_threshold:
                complaint = self.complaint_data[idx].copy()
                complaint['similarity_score'] = float(similarity)
                complaint['similarity_percentage'] = float(similarity * 100)
                
                # Filter by category if specified
                if category is None or complaint.get('category') == category:
                    similar_complaints.append(complaint)
        
        # Determine duplicate likelihood
        has_duplicates = len(similar_complaints) > 0
        
        if similar_complaints:
            max_similarity = similar_complaints[0]['similarity_score']
            if max_similarity > 0.85:
                likelihood = 'very_high'
                message = f"⚠️ Very likely duplicate! {max_similarity*100:.1f}% similar to existing complaint"
            elif max_similarity > 0.75:
                likelihood = 'high'
                message = f"⚡ Possible duplicate. {max_similarity*100:.1f}% similar to existing complaint"
            else:
                likelihood = 'moderate'
                message = f"Similar complaints found ({max_similarity*100:.1f}% match)"
        else:
            likelihood = 'none'
            message = "No similar complaints found. This appears to be a new issue."
        
        return {
            'has_duplicates': has_duplicates,
            'likelihood': likelihood,
            'message': message,
            'similar_complaints': similar_complaints[:3],  # Return top 3
            'total_similar': len(similar_complaints)
        }
    
    def check_duplicate(self, new_complaint_dict):
        """
        Convenience method that takes a complaint dict
        new_complaint_dict: {'title': '...', 'description': '...', 'category': '...'}
        """
        text = f"{new_complaint_dict.get('title', '')} {new_complaint_dict.get('description', '')}"
        category = new_complaint_dict.get('category')
        
        return self.find_similar(text, category)
    
    def save(self, filepath='ml_models/duplicate_detector.pkl'):
        """Save the detector"""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"Duplicate detector saved to {filepath}")
    
    @staticmethod
    def load(filepath='ml_models/duplicate_detector.pkl'):
        """Load a saved detector"""
        with open(filepath, 'rb') as f:
            return pickle.load(f)


if __name__ == "__main__":
    # Create detector
    detector = DuplicateDetector(similarity_threshold=0.65)
    
    # Sample existing complaints database
    existing_complaints = [
        {
            'id': 'CMP001',
            'title': 'WiFi not working in hostel',
            'description': 'The WiFi connection in hostel block A keeps disconnecting every few minutes. Unable to attend online classes.',
            'category': 'technical',
            'status': 'pending'
        },
        {
            'id': 'CMP002',
            'title': 'Broken AC in classroom',
            'description': 'Air conditioning unit in room 301 is not working. Temperature is very high.',
            'category': 'infrastructure',
            'status': 'in-progress'
        },
        {
            'id': 'CMP003',
            'title': 'Internet connectivity issues',
            'description': 'WiFi keeps dropping in the hostel. Very frustrating during online exams.',
            'category': 'technical',
            'status': 'pending'
        },
        {
            'id': 'CMP004',
            'title': 'Library books missing',
            'description': 'Several important reference books are missing from the library shelf.',
            'category': 'administrative',
            'status': 'resolved'
        },
        {
            'id': 'CMP005',
            'title': 'Canteen food quality poor',
            'description': 'The food served in canteen is not good. Many students are complaining.',
            'category': 'hostel',
            'status': 'pending'
        }
    ]
    
    # Index existing complaints
    detector.index_complaints(existing_complaints)
    
    # Save detector
    detector.save()
    
    # Test duplicate detection
    print("\n" + "="*70)
    print("TESTING DUPLICATE DETECTION")
    print("="*70)
    
    test_cases = [
        {
            'title': 'WiFi problem in hostel',
            'description': 'Internet is not working properly in hostel block A. Connection drops frequently.',
            'category': 'technical'
        },
        {
            'title': 'AC not cooling',
            'description': 'The air conditioner in classroom 301 stopped working.',
            'category': 'infrastructure'
        },
        {
            'title': 'Parking space shortage',
            'description': 'Not enough parking space available for students.',
            'category': 'other'
        }
    ]
    
    for i, test_complaint in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"New Complaint: {test_complaint['title']}")
        print(f"Category: {test_complaint['category']}")
        
        result = detector.check_duplicate(test_complaint)
        
        print(f"\nDuplicate Detection Result:")
        print(f"Has Duplicates: {result['has_duplicates']}")
        print(f"Likelihood: {result.get('likelihood', 'N/A')}")
        print(f"Message: {result['message']}")
        
        if result['similar_complaints']:
            print(f"\nSimilar Complaints Found ({result['total_similar']}):")
            for j, similar in enumerate(result['similar_complaints'], 1):
                print(f"\n  {j}. {similar['id']}: {similar['title']}")
                print(f"     Similarity: {similar['similarity_percentage']:.1f}%")
                print(f"     Status: {similar['status']}")
        
        print("-" * 70)
