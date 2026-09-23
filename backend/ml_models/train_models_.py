"""
Train All ML Models
Run this script to train and save all ML models
"""

import sys
import os

# Add ml_models to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ml_models.complaint_classifier import ComplaintClassifier
from ml_models.priority_predictor import PriorityPredictor
from ml_models.sentiment_analyzer import SentimentAnalyzer
from ml_models.duplicate_detector import DuplicateDetector
from ml_models.resolution_time_predictor import ResolutionTimePredictor
from ml_models.smart_search import SmartSearch

def train_all_models():
    """Train and save all ML models"""
    
    print("="*70)
    print("TRAINING ALL ML MODELS")
    print("="*70)
    
    # 1. Complaint Classifier
    print("\n1. Training Complaint Classifier...")
    print("-"*70)
    
    training_data = [
        # Academic (20 samples)
        ("Professor doesn't explain concepts clearly", "academic"),
        ("Need extension on assignment deadline", "academic"),
        ("Exam was too difficult", "academic"),
        ("Syllabus not covered in time", "academic"),
        ("Teacher always late to class", "academic"),
        ("Grading seems unfair", "academic"),
        ("Need clarification on lecture topic", "academic"),
        ("Lab sessions not conducted properly", "academic"),
        ("Project guidelines unclear", "academic"),
        ("Reference books not available", "academic"),
        ("Online classes poorly organized", "academic"),
        ("Attendance marked incorrectly", "academic"),
        ("Assignment not graded yet", "academic"),
        ("Tutorial sessions needed", "academic"),
        ("Course material outdated", "academic"),
        ("Practical exam schedule conflict", "academic"),
        ("Internal marks not updated", "academic"),
        ("Question paper pattern changed", "academic"),
        ("Study material not provided", "academic"),
        ("Faculty not responding to emails", "academic"),
        
        # Infrastructure (20 samples)
        ("Broken fan in classroom", "infrastructure"),
        ("AC not working", "infrastructure"),
        ("Leaking roof in library", "infrastructure"),
        ("Damaged desks", "infrastructure"),
        ("Poor lighting in corridor", "infrastructure"),
        ("Broken window panes", "infrastructure"),
        ("Ceiling falling apart", "infrastructure"),
        ("Door lock broken", "infrastructure"),
        ("Water cooler not working", "infrastructure"),
        ("Elevator out of service", "infrastructure"),
        ("Cracked walls", "infrastructure"),
        ("Broken chairs in auditorium", "infrastructure"),
        ("Drainage issue", "infrastructure"),
        ("Power outage frequent", "infrastructure"),
        ("Damaged flooring", "infrastructure"),
        ("Whiteboard not erasable", "infrastructure"),
        ("Projector not working", "infrastructure"),
        ("Fire extinguisher expired", "infrastructure"),
        ("Staircase railing loose", "infrastructure"),
        ("Washroom tap leaking", "infrastructure"),
        
        # Technical (20 samples)
        ("WiFi not working", "technical"),
        ("Computer lab PCs very slow", "technical"),
        ("Portal not loading", "technical"),
        ("App keeps crashing", "technical"),
        ("Printer not functioning", "technical"),
        ("Cannot login to system", "technical"),
        ("Software not installed", "technical"),
        ("Server down", "technical"),
        ("Database error", "technical"),
        ("Email not working", "technical"),
        ("Internet speed very slow", "technical"),
        ("Antivirus expired", "technical"),
        ("Scanner not detecting", "technical"),
        ("Network connectivity issues", "technical"),
        ("Website certificate error", "technical"),
        ("Mobile app login failed", "technical"),
        ("System update needed", "technical"),
        ("Password reset not working", "technical"),
        ("VPN connection problem", "technical"),
        ("Online exam portal crashed", "technical"),
        
        # Administrative (20 samples)
        ("Fee receipt not generated", "administrative"),
        ("Transcript taking too long", "administrative"),
        ("Certificate not issued", "administrative"),
        ("Bonafide not ready", "administrative"),
        ("Scholarship delayed", "administrative"),
        ("Registration not complete", "administrative"),
        ("ID card not received", "administrative"),
        ("Mark sheet error", "administrative"),
        ("Migration certificate pending", "administrative"),
        ("Library card not issued", "administrative"),
        ("Exam form not accepted", "administrative"),
        ("NOC not provided", "administrative"),
        ("Admission process unclear", "administrative"),
        ("Document verification delay", "administrative"),
        ("Refund not processed", "administrative"),
        ("Hostel allocation wrong", "administrative"),
        ("Timetable not published", "administrative"),
        ("Notice not communicated", "administrative"),
        ("Leave application pending", "administrative"),
        ("Bus pass not ready", "administrative"),
        
        # Hostel (20 samples)
        ("Roommate disturbing at night", "hostel"),
        ("Food quality poor", "hostel"),
        ("No hot water", "hostel"),
        ("Room not cleaned", "hostel"),
        ("Bed mattress damaged", "hostel"),
        ("Noise from neighboring room", "hostel"),
        ("Mess timing inconvenient", "hostel"),
        ("Warden not available", "hostel"),
        ("Laundry service poor", "hostel"),
        ("Security guard rude", "hostel"),
        ("Late night entry not allowed", "hostel"),
        ("Visitor rules too strict", "hostel"),
        ("Common room TV not working", "hostel"),
        ("Drinking water supply issue", "hostel"),
        ("Room change request", "hostel"),
        ("Electricity bill high", "hostel"),
        ("Cupboard lock broken", "hostel"),
        ("Bathroom exhaust not working", "hostel"),
        ("Food variety lacking", "hostel"),
        ("Pest control needed", "hostel"),
        
        # Transport (15 samples)
        ("Bus always late", "transport"),
        ("Bus route doesn't cover area", "transport"),
        ("Overcrowding in bus", "transport"),
        ("Driver drives rashly", "transport"),
        ("AC not working in bus", "transport"),
        ("Bus timing not convenient", "transport"),
        ("Need additional bus", "transport"),
        ("Bus conductor rude", "transport"),
        ("Bus stop too far", "transport"),
        ("Seats damaged in bus", "transport"),
        ("Bus fee too high", "transport"),
        ("Route change needed", "transport"),
        ("Bus breakdown frequent", "transport"),
        ("No bus on weekends", "transport"),
        ("Bus schedule not followed", "transport"),
        
        # Other (15 samples)
        ("Stray dogs in campus", "other"),
        ("Canteen prices high", "other"),
        ("No parking space", "other"),
        ("Sports equipment old", "other"),
        ("Medical room closed", "other"),
        ("Gym equipment broken", "other"),
        ("Green cover reducing", "other"),
        ("Noise pollution", "other"),
        ("Security lax", "other"),
        ("Campus cleanliness poor", "other"),
        ("Water fountain not working", "other"),
        ("Statue damaged", "other"),
        ("Garden not maintained", "other"),
        ("Lost and found not working", "other"),
        ("Suggestion box broken", "other"),
    ]
    
    texts = [t for t, _ in training_data]
    labels = [l for _, l in training_data]
    
    classifier = ComplaintClassifier()
    classifier.train(texts, labels)
    classifier.save('classifier.pkl')  # Save in current directory
    
    # 2. Priority Predictor
    print("\n2. Training Priority Predictor...")
    print("-"*70)
    predictor = PriorityPredictor()
    predictor.save('priority_predictor.pkl')  # Save in current directory
    print("Priority predictor ready (rule-based)")
    
    # 3. Sentiment Analyzer
    print("\n3. Training Sentiment Analyzer...")
    print("-"*70)
    analyzer = SentimentAnalyzer()
    analyzer.save('sentiment_analyzer.pkl')  # Save in current directory
    print("Sentiment analyzer ready")
    
    # 4. Duplicate Detector
    print("\n4. Training Duplicate Detector...")
    print("-"*70)
    detector = DuplicateDetector()
    # Will be trained dynamically with actual data
    detector.save('duplicate_detector.pkl')  # Save in current directory
    print("Duplicate detector ready")
    
    # 5. Resolution Time Predictor
    print("\n5. Training Resolution Time Predictor...")
    print("-"*70)
    time_predictor = ResolutionTimePredictor()
    # Will be trained with historical data
    time_predictor.save('resolution_predictor.pkl')  # Save in current directory
    print("Resolution time predictor ready (using defaults)")
    
    # 6. Smart Search
    print("\n6. Training Smart Search...")
    print("-"*70)
    search_engine = SmartSearch()
    # Will be indexed with actual complaints
    search_engine.save('smart_search.pkl')  # Save in current directory
    print("Smart search ready")
    
    print("\n" + "="*70)
    print("ALL MODELS TRAINED AND SAVED SUCCESSFULLY!")
    print("="*70)
    print("\nModel files saved in current directory (backend/ml_models/):")
    print("  • classifier.pkl")
    print("  • priority_predictor.pkl")
    print("  • sentiment_analyzer.pkl")
    print("  • duplicate_detector.pkl")
    print("  • resolution_predictor.pkl")
    print("  • smart_search.pkl")
    print("\nYou can now restart your Flask app!")
    
    return True

if __name__ == "__main__":
    try:
        train_all_models()
    except Exception as e:
        print(f"\n❌ Error training models: {e}")
        import traceback
        traceback.print_exc()