"""
Resolution Time Predictor
Predicts how long it will take to resolve a complaint
Based on historical data and complaint characteristics
"""

import pickle
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder

class ResolutionTimePredictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.category_encoder = LabelEncoder()
        self.priority_encoder = LabelEncoder()
        self.is_trained = False
        
        # Default category order
        self.categories = ['academic', 'infrastructure', 'administrative', 
                          'technical', 'hostel', 'transport', 'other']
        self.priorities = ['low', 'medium', 'high', 'urgent']
        
        # Average resolution times (hours) - used as fallback
        self.avg_resolution_times = {
            'academic': 48,
            'infrastructure': 72,
            'administrative': 96,
            'technical': 24,
            'hostel': 36,
            'transport': 48,
            'other': 60
        }
        
        self.priority_multipliers = {
            'low': 1.5,
            'medium': 1.0,
            'high': 0.6,
            'urgent': 0.3
        }
    
    def extract_features(self, complaint):
        """Extract features from complaint"""
        features = []
        
        # Category (encoded)
        category = complaint.get('category', 'other')
        if category in self.categories:
            category_idx = self.categories.index(category)
        else:
            category_idx = self.categories.index('other')
        features.append(category_idx)
        
        # Priority (encoded)
        priority = complaint.get('priority', 'medium')
        if priority in self.priorities:
            priority_idx = self.priorities.index(priority)
        else:
            priority_idx = 1  # medium
        features.append(priority_idx)
        
        # Description length
        description = complaint.get('description', '')
        features.append(len(description))
        
        # Title length
        title = complaint.get('title', '')
        features.append(len(title))
        
        # Day of week (0 = Monday, 6 = Sunday)
        # Complaints submitted on weekends might take longer
        day_of_week = complaint.get('day_of_week', datetime.now().weekday())
        features.append(day_of_week)
        
        # Hour of day (complaints at night might wait till morning)
        hour = complaint.get('hour', datetime.now().hour)
        features.append(hour)
        
        # Has attachment
        has_attachment = 1 if complaint.get('has_attachment', False) else 0
        features.append(has_attachment)
        
        return features
    
    def train(self, historical_complaints):
        """
        Train the model on historical complaints
        historical_complaints: list of dicts with complaint data and actual resolution_time_hours
        """
        if len(historical_complaints) < 10:
            print("Warning: Not enough data to train. Need at least 10 resolved complaints.")
            return False
        
        X = []
        y = []
        
        for complaint in historical_complaints:
            if 'resolution_time_hours' in complaint and complaint['resolution_time_hours'] is not None:
                features = self.extract_features(complaint)
                X.append(features)
                y.append(complaint['resolution_time_hours'])
        
        if len(X) < 10:
            print("Warning: Not enough valid training data.")
            return False
        
        # Train model
        self.model.fit(np.array(X), np.array(y))
        self.is_trained = True
        
        print(f"Model trained on {len(X)} historical complaints")
        
        # Calculate and print performance metrics
        predictions = self.model.predict(np.array(X))
        mae = np.mean(np.abs(np.array(y) - predictions))
        print(f"Mean Absolute Error: {mae:.2f} hours")
        
        return True
    
    def predict(self, complaint):
        """Predict resolution time for a complaint"""
        category = complaint.get('category', 'other')
        priority = complaint.get('priority', 'medium')
        
        if self.is_trained:
            # Use ML model
            features = self.extract_features(complaint)
            predicted_hours = self.model.predict([features])[0]
        else:
            # Use rule-based fallback
            base_hours = self.avg_resolution_times.get(category, 60)
            multiplier = self.priority_multipliers.get(priority, 1.0)
            predicted_hours = base_hours * multiplier
        
        # Add some variance for realism
        predicted_hours = max(1, predicted_hours)  # At least 1 hour
        
        # Calculate different time formats
        predicted_days = predicted_hours / 24
        
        # Determine resolution date
        now = datetime.now()
        resolution_date = now + timedelta(hours=predicted_hours)
        
        # Generate time range (±20%)
        min_hours = predicted_hours * 0.8
        max_hours = predicted_hours * 1.2
        
        # Create human-readable time estimate
        if predicted_hours < 1:
            time_estimate = "Less than 1 hour"
        elif predicted_hours < 24:
            time_estimate = f"{int(predicted_hours)} hours"
        elif predicted_days < 2:
            time_estimate = "1-2 days"
        elif predicted_days < 7:
            time_estimate = f"{int(predicted_days)} days"
        else:
            weeks = int(predicted_days / 7)
            time_estimate = f"{weeks} week{'s' if weeks > 1 else ''}"
        
        return {
            'estimated_hours': round(predicted_hours, 1),
            'estimated_days': round(predicted_days, 1),
            'time_estimate': time_estimate,
            'estimated_resolution_date': resolution_date.strftime('%Y-%m-%d %H:%M'),
            'range': {
                'min_hours': round(min_hours, 1),
                'max_hours': round(max_hours, 1)
            },
            'confidence': 'high' if self.is_trained else 'moderate',
            'factors': self._get_factors(complaint)
        }
    
    def _get_factors(self, complaint):
        """Explain what factors affect the resolution time"""
        factors = []
        
        category = complaint.get('category', 'other')
        priority = complaint.get('priority', 'medium')
        
        if priority == 'urgent':
            factors.append("⚡ Urgent priority - faster resolution expected")
        elif priority == 'low':
            factors.append("📅 Low priority - may take longer")
        
        if category == 'technical':
            factors.append("💻 Technical issues usually resolved quickly")
        elif category == 'infrastructure':
            factors.append("🏗️ Infrastructure repairs may take time")
        elif category == 'administrative':
            factors.append("📋 Administrative processes can be lengthy")
        
        day_of_week = complaint.get('day_of_week', datetime.now().weekday())
        if day_of_week >= 5:  # Saturday or Sunday
            factors.append("📅 Submitted on weekend - may affect timing")
        
        if complaint.get('has_attachment'):
            factors.append("📎 Attachment provided - helps faster diagnosis")
        
        return factors
    
    def save(self, filepath='ml_models/resolution_predictor.pkl'):
        """Save the model"""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"Resolution time predictor saved to {filepath}")
    
    @staticmethod
    def load(filepath='ml_models/resolution_predictor.pkl'):
        """Load a saved model"""
        with open(filepath, 'rb') as f:
            return pickle.load(f)


if __name__ == "__main__":
    # Create predictor
    predictor = ResolutionTimePredictor()
    
    # Sample historical data for training
    historical_data = [
        {'category': 'technical', 'priority': 'urgent', 'description': 'WiFi not working', 
         'title': 'Internet issue', 'resolution_time_hours': 4, 'day_of_week': 2, 'hour': 10, 'has_attachment': True},
        {'category': 'technical', 'priority': 'high', 'description': 'Computer not booting', 
         'title': 'PC problem', 'resolution_time_hours': 8, 'day_of_week': 3, 'hour': 14, 'has_attachment': False},
        {'category': 'infrastructure', 'priority': 'medium', 'description': 'AC not working in class', 
         'title': 'AC issue', 'resolution_time_hours': 48, 'day_of_week': 1, 'hour': 9, 'has_attachment': True},
        {'category': 'infrastructure', 'priority': 'urgent', 'description': 'Water leakage', 
         'title': 'Leak in bathroom', 'resolution_time_hours': 12, 'day_of_week': 0, 'hour': 7, 'has_attachment': True},
        {'category': 'academic', 'priority': 'medium', 'description': 'Grade dispute', 
         'title': 'Marks issue', 'resolution_time_hours': 72, 'day_of_week': 4, 'hour': 11, 'has_attachment': False},
        {'category': 'administrative', 'priority': 'low', 'description': 'Certificate request', 
         'title': 'Need certificate', 'resolution_time_hours': 120, 'day_of_week': 2, 'hour': 15, 'has_attachment': False},
        {'category': 'hostel', 'priority': 'medium', 'description': 'Room cleaning issue', 
         'title': 'Dirty room', 'resolution_time_hours': 24, 'day_of_week': 3, 'hour': 8, 'has_attachment': False},
        {'category': 'transport', 'priority': 'high', 'description': 'Bus always late', 
         'title': 'Bus timing', 'resolution_time_hours': 36, 'day_of_week': 1, 'hour': 7, 'has_attachment': False},
        {'category': 'technical', 'priority': 'medium', 'description': 'Portal not loading', 
         'title': 'Website issue', 'resolution_time_hours': 6, 'day_of_week': 0, 'hour': 16, 'has_attachment': True},
        {'category': 'infrastructure', 'priority': 'low', 'description': 'Paint peeling', 
         'title': 'Wall condition', 'resolution_time_hours': 168, 'day_of_week': 5, 'hour': 10, 'has_attachment': False},
    ]
    
    # Train model
    predictor.train(historical_data)
    
    # Save model
    predictor.save()
    
    # Test predictions
    print("\n" + "="*70)
    print("TESTING RESOLUTION TIME PREDICTIONS")
    print("="*70)
    
    test_cases = [
        {'category': 'technical', 'priority': 'urgent', 'description': 'WiFi down everywhere', 
         'title': 'Network failure', 'has_attachment': True},
        {'category': 'infrastructure', 'priority': 'medium', 'description': 'Broken window needs fixing', 
         'title': 'Window broken', 'has_attachment': False},
        {'category': 'administrative', 'priority': 'low', 'description': 'Request for transcript', 
         'title': 'Transcript needed', 'has_attachment': False},
        {'category': 'academic', 'priority': 'high', 'description': 'Assignment deadline extension request', 
         'title': 'Extension request', 'has_attachment': False},
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Complaint: {test['title']}")
        print(f"Category: {test['category']}, Priority: {test['priority']}")
        
        result = predictor.predict(test)
        
        print(f"\nPrediction:")
        print(f"  Estimated Time: {result['time_estimate']}")
        print(f"  Hours: {result['estimated_hours']} ({result['estimated_days']} days)")
        print(f"  Expected Resolution: {result['estimated_resolution_date']}")
        print(f"  Range: {result['range']['min_hours']:.1f} - {result['range']['max_hours']:.1f} hours")
        print(f"  Confidence: {result['confidence']}")
        print(f"  Factors:")
        for factor in result['factors']:
            print(f"    • {factor}")
        print("-" * 70)
