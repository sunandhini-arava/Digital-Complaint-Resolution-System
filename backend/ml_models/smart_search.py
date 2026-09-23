"""
Smart Semantic Search
Improved search that understands meaning, not just keywords
Uses TF-IDF for lightweight semantic search
"""

import pickle
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class SmartSearch:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 3),  # Unigrams, bigrams, and trigrams
            stop_words='english',
            min_df=1
        )
        self.complaint_vectors = None
        self.complaint_data = []
        
        # Synonym mapping for better search
        self.synonyms = {
            'wifi': ['internet', 'network', 'connection', 'connectivity'],
            'broken': ['damaged', 'not working', 'faulty', 'malfunctioning'],
            'slow': ['sluggish', 'laggy', 'taking time', 'delay'],
            'professor': ['teacher', 'faculty', 'instructor'],
            'deadline': ['due date', 'submission', 'last date'],
            'dirty': ['unclean', 'messy', 'not cleaned', 'unhygienic'],
        }
    
    def preprocess_text(self, text):
        """Clean and expand text with synonyms"""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Expand with synonyms
        words = text.split()
        expanded_words = []
        for word in words:
            expanded_words.append(word)
            if word in self.synonyms:
                expanded_words.extend(self.synonyms[word])
        
        return ' '.join(expanded_words)
    
    def index_complaints(self, complaints):
        """
        Index complaints for search
        complaints: list of dicts with complaint data
        """
        if not complaints:
            return
        
        self.complaint_data = complaints
        
        # Combine all searchable fields
        texts = []
        for c in complaints:
            combined_text = f"{c.get('title', '')} {c.get('description', '')} {c.get('category', '')} {c.get('user_name', '')}"
            processed = self.preprocess_text(combined_text)
            texts.append(processed)
        
        # Create search index
        self.complaint_vectors = self.vectorizer.fit_transform(texts)
        
        print(f"Indexed {len(complaints)} complaints for smart search")
    
    def search(self, query, filters=None, top_k=10):
        """
        Smart search with optional filters
        query: search text
        filters: dict with 'category', 'status', 'priority', etc.
        top_k: number of results to return
        """
        if self.complaint_vectors is None or len(self.complaint_data) == 0:
            return {
                'results': [],
                'total': 0,
                'query': query,
                'message': 'No complaints indexed yet'
            }
        
        # Preprocess query
        processed_query = self.preprocess_text(query)
        
        # Vectorize query
        query_vector = self.vectorizer.transform([processed_query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_vector, self.complaint_vectors)[0]
        
        # Get indices sorted by similarity
        sorted_indices = similarities.argsort()[::-1]
        
        # Apply filters
        results = []
        for idx in sorted_indices:
            if len(results) >= top_k:
                break
            
            similarity = similarities[idx]
            
            # Skip if similarity is too low
            if similarity < 0.01:
                continue
            
            complaint = self.complaint_data[idx].copy()
            
            # Apply filters
            if filters:
                if 'category' in filters and filters['category']:
                    if complaint.get('category') != filters['category']:
                        continue
                
                if 'status' in filters and filters['status']:
                    if complaint.get('status') != filters['status']:
                        continue
                
                if 'priority' in filters and filters['priority']:
                    if complaint.get('priority') != filters['priority']:
                        continue
                
                if 'user_type' in filters and filters['user_type']:
                    if complaint.get('user_type') != filters['user_type']:
                        continue
            
            # Add search metadata
            complaint['search_score'] = float(similarity)
            complaint['relevance'] = self._get_relevance_label(similarity)
            
            results.append(complaint)
        
        return {
            'results': results,
            'total': len(results),
            'query': query,
            'processed_query': processed_query,
            'filters_applied': filters if filters else {},
            'message': f"Found {len(results)} results for '{query}'"
        }
    
    def _get_relevance_label(self, score):
        """Convert similarity score to relevance label"""
        if score > 0.7:
            return 'highly_relevant'
        elif score > 0.4:
            return 'relevant'
        elif score > 0.2:
            return 'somewhat_relevant'
        else:
            return 'low_relevance'
    
    def suggest_queries(self, partial_query):
        """
        Suggest search queries based on existing complaints
        (Simple implementation - finds common phrases)
        """
        if not self.complaint_data:
            return []
        
        suggestions = set()
        partial_lower = partial_query.lower()
        
        # Look for matching titles
        for complaint in self.complaint_data[:100]:  # Limit for performance
            title = complaint.get('title', '').lower()
            if partial_lower in title:
                suggestions.add(complaint.get('title'))
        
        return list(suggestions)[:5]  # Return top 5
    
    def get_related_complaints(self, complaint_id, top_k=5):
        """Find complaints related to a specific complaint"""
        # Find the complaint
        target_complaint = None
        target_index = None
        
        for i, c in enumerate(self.complaint_data):
            if c.get('complaint_id') == complaint_id or c.get('id') == complaint_id:
                target_complaint = c
                target_index = i
                break
        
        if target_complaint is None:
            return {'results': [], 'message': 'Complaint not found'}
        
        # Get its vector
        if self.complaint_vectors is None:
            return {'results': [], 'message': 'Index not built'}
        
        target_vector = self.complaint_vectors[target_index:target_index+1]
        
        # Find similar
        similarities = cosine_similarity(target_vector, self.complaint_vectors)[0]
        
        # Sort and exclude the complaint itself
        sorted_indices = similarities.argsort()[::-1]
        
        related = []
        for idx in sorted_indices:
            if idx == target_index:
                continue
            
            if len(related) >= top_k:
                break
            
            similarity = similarities[idx]
            if similarity > 0.3:  # Reasonable threshold
                complaint = self.complaint_data[idx].copy()
                complaint['similarity'] = float(similarity)
                related.append(complaint)
        
        return {
            'results': related,
            'total': len(related),
            'message': f"Found {len(related)} related complaints"
        }
    
    def save(self, filepath='ml_models/smart_search.pkl'):
        """Save the search index"""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"Smart search index saved to {filepath}")
    
    @staticmethod
    def load(filepath='ml_models/smart_search.pkl'):
        """Load a saved search index"""
        with open(filepath, 'rb') as f:
            return pickle.load(f)


if __name__ == "__main__":
    # Create search engine
    search_engine = SmartSearch()
    
    # Sample complaints
    sample_complaints = [
        {
            'id': 'CMP001',
            'complaint_id': 'CMP001',
            'title': 'WiFi not working in hostel',
            'description': 'The internet connection keeps dropping in block A hostel. Cannot attend online classes.',
            'category': 'technical',
            'status': 'pending',
            'priority': 'high',
            'user_name': 'John Doe',
            'user_type': 'student'
        },
        {
            'id': 'CMP002',
            'complaint_id': 'CMP002',
            'title': 'Broken AC in classroom 301',
            'description': 'Air conditioning not working. Room is very hot.',
            'category': 'infrastructure',
            'status': 'in-progress',
            'priority': 'medium',
            'user_name': 'Jane Smith',
            'user_type': 'faculty'
        },
        {
            'id': 'CMP003',
            'complaint_id': 'CMP003',
            'title': 'Slow internet in library',
            'description': 'Network speed is very poor. Taking forever to download research papers.',
            'category': 'technical',
            'status': 'resolved',
            'priority': 'medium',
            'user_name': 'Bob Johnson',
            'user_type': 'student'
        },
        {
            'id': 'CMP004',
            'complaint_id': 'CMP004',
            'title': 'Professor always late to class',
            'description': 'Teacher comes 20 minutes late every day. Syllabus not covered properly.',
            'category': 'academic',
            'status': 'pending',
            'priority': 'low',
            'user_name': 'Alice Brown',
            'user_type': 'student'
        },
        {
            'id': 'CMP005',
            'complaint_id': 'CMP005',
            'title': 'Dirty washrooms in hostel',
            'description': 'Bathrooms not cleaned regularly. Very unhygienic conditions.',
            'category': 'hostel',
            'status': 'pending',
            'priority': 'high',
            'user_name': 'Charlie Davis',
            'user_type': 'student'
        },
    ]
    
    # Index complaints
    search_engine.index_complaints(sample_complaints)
    
    # Save
    search_engine.save()
    
    # Test searches
    print("\n" + "="*70)
    print("TESTING SMART SEARCH")
    print("="*70)
    
    test_queries = [
        "network problem",
        "teacher late",
        "dirty bathroom",
        "not working",
    ]
    
    for query in test_queries:
        print(f"\n--- Search: '{query}' ---")
        results = search_engine.search(query, top_k=3)
        
        print(f"Found {results['total']} results")
        print(f"Processed query: {results['processed_query']}")
        
        for i, result in enumerate(results['results'], 1):
            print(f"\n{i}. {result['complaint_id']}: {result['title']}")
            print(f"   Category: {result['category']}, Status: {result['status']}")
            print(f"   Relevance: {result['relevance']} (score: {result['search_score']:.3f})")
        
        print("-" * 70)
    
    # Test related complaints
    print("\n" + "="*70)
    print("TESTING RELATED COMPLAINTS")
    print("="*70)
    
    related = search_engine.get_related_complaints('CMP001', top_k=3)
    print(f"\nComplaints related to CMP001:")
    for r in related['results']:
        print(f"  • {r['complaint_id']}: {r['title']} (similarity: {r['similarity']:.2%})")
