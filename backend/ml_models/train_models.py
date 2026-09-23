"""
Train All ML Models - Enhanced Version with Rich Training Data
Run this script to train and save all ML models.
Usage: python ml_models/train_models.py
"""

import sys
import os
import pickle
import re
import numpy as np
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

BASE = os.path.dirname(os.path.abspath(__file__))
def save_path(filename):
    return os.path.join(BASE, filename)


# =============================================================================
# 1. COMPLAINT CLASSIFIER
# =============================================================================
def train_classifier():
    print("\n" + "="*60)
    print("1. Training Complaint Classifier")
    print("="*60)

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import cross_val_score

    training_data = [
        # ACADEMIC
        ("Professor is always late to class and does not cover the full syllabus", "academic"),
        ("The assignment deadline is too close to the exam schedule", "academic"),
        ("I want to dispute my final exam marks they were graded incorrectly", "academic"),
        ("The course material provided is outdated and not relevant to current industry", "academic"),
        ("Teacher does not respond to student emails or doubts", "academic"),
        ("Lab sessions are being cancelled without prior notice", "academic"),
        ("The internal marks were not updated in the portal correctly", "academic"),
        ("We need more tutorial sessions to understand difficult topics", "academic"),
        ("Attendance has been marked wrongly for several students", "academic"),
        ("Question paper was extremely out of syllabus for end semester exam", "academic"),
        ("Online classes have very poor audio and video quality", "academic"),
        ("Project guidelines given by the professor are very unclear", "academic"),
        ("The grading criteria for assignments is inconsistent and unfair", "academic"),
        ("Reference books recommended by faculty are not available in library", "academic"),
        ("Practical exam schedule conflicts with theory examination", "academic"),
        ("Assignment marks not displayed even after two weeks of submission", "academic"),
        ("Faculty member uses outdated teaching methods and no practical examples", "academic"),
        ("Student failed even though attendance is above 75 percent requirement", "academic"),
        ("Professor did not complete the syllabus before the exam started", "academic"),
        ("I need a re-evaluation of my answer sheet for the second exam", "academic"),
        ("Class test was conducted without any prior announcement", "academic"),
        ("I was marked absent during an exam I clearly attended", "academic"),
        ("Semester registration was blocked despite having no backlogs", "academic"),
        ("Teacher plays favorites and gives higher marks to certain students", "academic"),
        ("I want to challenge the sessional marks given for mid semester test", "academic"),
        ("Exam results have not been published even after one month", "academic"),
        ("Study material PDF shared in class portal is corrupted and unreadable", "academic"),
        ("Extra classes are scheduled without informing students in advance", "academic"),
        ("Department is not following the official academic calendar", "academic"),
        ("The professor gave very low marks without explanation or feedback", "academic"),

        # INFRASTRUCTURE
        ("The air conditioning unit in classroom 301 has not been working for two weeks", "infrastructure"),
        ("There is a water leakage from the ceiling in the first floor corridor", "infrastructure"),
        ("Broken benches and damaged desks in the computer lab need urgent repair", "infrastructure"),
        ("The street lights in the campus main road are not working at night", "infrastructure"),
        ("Toilets on the third floor are not clean and have broken flush systems", "infrastructure"),
        ("The elevator in block B has been out of service for over a month", "infrastructure"),
        ("Drinking water cooler on the second floor is not producing cold water", "infrastructure"),
        ("Paint on classroom walls is peeling and creating a shabby environment", "infrastructure"),
        ("Windows in the lecture hall are broken and allow mosquitoes inside", "infrastructure"),
        ("Campus main gate has a broken lock and compromises security", "infrastructure"),
        ("Sewage smell is coming from the drain near the cafeteria area", "infrastructure"),
        ("Electrical wiring in lab 204 is exposed and poses a safety hazard", "infrastructure"),
        ("Whiteboard in seminar hall is badly damaged and cannot be written on", "infrastructure"),
        ("Roof of the old block building is leaking during heavy rains", "infrastructure"),
        ("Generator backup is not working causing power outages during classes", "infrastructure"),
        ("Fire extinguishers in the building are expired and not replaced", "infrastructure"),
        ("Gym equipment in the sports complex is broken and dangerous to use", "infrastructure"),
        ("Footpaths across campus are broken causing difficulty for walking", "infrastructure"),
        ("CCTV cameras near the library entrance are not working", "infrastructure"),
        ("Classroom projector bulb is blown and needs replacement urgently", "infrastructure"),
        ("Fan in room 105 makes loud noise and vibrates badly", "infrastructure"),
        ("Washroom doors in the academic block do not have proper locks", "infrastructure"),
        ("Basketball court floor is cracked and players are getting injured", "infrastructure"),
        ("Laboratory sink drains are blocked causing water to overflow", "infrastructure"),
        ("Auditorium sound system has a constant noise that disrupts events", "infrastructure"),
        ("Classroom blackboard surface is too worn out and writing is not visible", "infrastructure"),
        ("Fire alarm system in block A has been malfunctioning for weeks", "infrastructure"),
        ("Campus roads have very large potholes that damage vehicles", "infrastructure"),
        ("Water tanker supply to hostel is irregular causing daily shortages", "infrastructure"),
        ("Transformer near hostel keeps tripping causing frequent power cuts", "infrastructure"),

        # ADMINISTRATIVE
        ("My bonafide certificate request has not been processed for 30 days", "administrative"),
        ("Fee payment receipt was not generated after successful online transaction", "administrative"),
        ("I need a no objection certificate for my visa application urgently", "administrative"),
        ("Scholarship amount was not disbursed even though I am eligible", "administrative"),
        ("Hall ticket for examination has not been issued due to a fee error", "administrative"),
        ("College leaving certificate is required for job application but not issued", "administrative"),
        ("Migration certificate request submitted two months ago has no update", "administrative"),
        ("Student ID card was not provided even after joining the institution", "administrative"),
        ("Office staff are rude and unhelpful when students come with requests", "administrative"),
        ("Course completion certificate has wrong marks printed on it", "administrative"),
        ("Admission documents submitted during joining are lost by the office", "administrative"),
        ("Fee concession application was rejected without any valid reason given", "administrative"),
        ("Duplicate mark sheet request is taking more than two months to process", "administrative"),
        ("Transfer certificate was issued with wrong date of joining information", "administrative"),
        ("Semester fee was paid twice due to portal error and refund not given", "administrative"),
        ("Application for hostel accommodation was ignored without any response", "administrative"),
        ("Staff verification letter needed for railway concession not provided", "administrative"),
        ("Exam fee was deducted from bank twice and refund not processed", "administrative"),
        ("Request for change of elective subject not processed before deadline", "administrative"),
        ("Application for academic transcript apostille is pending since last year", "administrative"),
        ("My official name spelling is wrong in all college issued documents", "administrative"),
        ("Provisional certificate has wrong course duration mentioned on it", "administrative"),
        ("I did not receive any acknowledgement for my scholarship application", "administrative"),
        ("Medical reimbursement claim submitted three months ago has no update", "administrative"),
        ("Administration has not responded to any email I sent in the last month", "administrative"),
        ("Refund for cancelled hostel booking has not been processed in 60 days", "administrative"),
        ("I was charged extra fees without any explanation or invoice provided", "administrative"),
        ("Important circular about exam schedule was not communicated to students", "administrative"),
        ("Annual report and progress card not shared with parents on time", "administrative"),
        ("Fee structure for next academic year not yet published causing confusion", "administrative"),

        # TECHNICAL
        ("WiFi connection in hostel room keeps dropping every few minutes", "technical"),
        ("College student portal shows server error when trying to check results", "technical"),
        ("Computer lab systems are extremely slow and take too long to boot", "technical"),
        ("Online exam platform crashed during the middle of my examination", "technical"),
        ("Campus intranet website is showing access denied for students", "technical"),
        ("Printer in the library is not working and students cannot print notes", "technical"),
        ("College mobile app crashes whenever I try to see attendance details", "technical"),
        ("LMS system is not loading uploaded assignments and showing error", "technical"),
        ("I cannot register for subjects online due to a portal error message", "technical"),
        ("Email account provided by college is not allowing password reset", "technical"),
        ("Biometric attendance system is not recognizing my fingerprint", "technical"),
        ("Campus WiFi password was reset without informing students", "technical"),
        ("Online fee payment gateway times out before completing transaction", "technical"),
        ("Video conferencing software does not work on college lab computers", "technical"),
        ("Student database portal shows wrong semester for my enrollment", "technical"),
        ("Laboratory software license has expired and tools do not open", "technical"),
        ("College ERP system logs me out automatically every two minutes", "technical"),
        ("I cannot download my hall ticket because the PDF fails to generate", "technical"),
        ("Zoom link shared by professor is showing meeting not found error", "technical"),
        ("Smart board in seminar hall does not respond to touch interactions", "technical"),
        ("College website is not working on mobile browser", "technical"),
        ("Result portal is showing marks from previous semester instead of current", "technical"),
        ("Cannot log in to student portal even with correct username and password", "technical"),
        ("OTP for college portal verification is not being received on mobile", "technical"),
        ("Digital attendance system marked me absent on a day I was present", "technical"),
        ("ERP system does not allow editing profile information once submitted", "technical"),
        ("System in lab keeps restarting during work causing data loss", "technical"),
        ("Network speed in the academic block is too slow for online classes", "technical"),
        ("IT department is not responding to support tickets raised by students", "technical"),
        ("Scanner in library is not working and needed for document submission", "technical"),

        # HOSTEL
        ("Roommate creates loud disturbances late at night disturbing sleep", "hostel"),
        ("Mess food quality is very poor and not hygienic at all", "hostel"),
        ("Hot water is not available for bathing in the morning hours", "hostel"),
        ("Hostel room has not been cleaned by housekeeping for two weeks", "hostel"),
        ("Hostel warden is rude and does not listen to student complaints", "hostel"),
        ("Cockroaches and rats are frequently seen in the hostel mess area", "hostel"),
        ("Laundry facility in hostel has been broken for over three weeks", "hostel"),
        ("Mess committee is not following the approved menu for students", "hostel"),
        ("Drinking water in hostel is not clean and causes stomach infections", "hostel"),
        ("Hostel internet connection is very slow and unusable after 10pm", "hostel"),
        ("Security guard at hostel gate misbehaves with female students", "hostel"),
        ("I was allotted a room with a broken window and damaged furniture", "hostel"),
        ("Mess food quantity is very less and students go to bed hungry", "hostel"),
        ("Power cuts in hostel at night are very frequent and last long", "hostel"),
        ("Hostel room allocation was done unfairly without following rules", "hostel"),
        ("No first aid kit available in hostel in case of emergencies", "hostel"),
        ("Study room in hostel does not have proper lighting for night study", "hostel"),
        ("Hostel mess serves the same food every day without any variety", "hostel"),
        ("Unauthorized persons are frequently seen inside the hostel premises", "hostel"),
        ("Hostel roof leaks during rain and damages student belongings", "hostel"),
        ("Geyser in hostel bathroom has not been working for two months", "hostel"),
        ("Hostel water supply is only available for one hour per day", "hostel"),
        ("Students are being charged hostel fee for vacation period also", "hostel"),
        ("Hostel security cameras are not working increasing theft concerns", "hostel"),
        ("Mess workers do not follow food safety and hygiene standards", "hostel"),
        ("Hostel gate is left open at night and no guard is present", "hostel"),
        ("Electrical socket in hostel room is faulty and gives sparks", "hostel"),
        ("Mattresses in hostel are very old and unhygienic for sleeping", "hostel"),
        ("Students with medical conditions are not given special diet in mess", "hostel"),
        ("Hostel mess is closed on public holidays but fees are charged", "hostel"),

        # TRANSPORT
        ("College bus number 5 is always 30 minutes late to pick up students", "transport"),
        ("Bus driver drives at very high speed endangering student safety", "transport"),
        ("Morning bus is severely overcrowded with students standing in aisle", "transport"),
        ("Bus route does not cover my residential area at all", "transport"),
        ("Request for an additional evening bus on route 7 has not been addressed", "transport"),
        ("College bus conductor is misbehaving with female students", "transport"),
        ("Bus breaks down every other week due to poor maintenance", "transport"),
        ("Bus pass renewal is taking too long at the transport office", "transport"),
        ("Bus AC is not working during extremely hot summer months", "transport"),
        ("I was not allowed to board the bus even though I have a valid pass", "transport"),
        ("College transport is not available for early morning practical sessions", "transport"),
        ("Bus does not stop at the designated stop and students must run after it", "transport"),
        ("Transport fee was collected but bus route was discontinued later", "transport"),
        ("Bus smells bad and windows cannot be opened due to broken handles", "transport"),
        ("Driver does not follow traffic rules and ignores red lights", "transport"),
        ("Bus route timing sheet displayed on notice board is outdated", "transport"),
        ("I lost my bus pass but no duplicate is being issued by transport office", "transport"),
        ("No shelter at the college bus stop outside the main gate", "transport"),
        ("Bus seating capacity is being exceeded regularly without any action", "transport"),
        ("Transport department does not respond to complaints about bus timing", "transport"),
        ("Student was left behind at a stop because the bus did not wait", "transport"),
        ("College bus does not have a first aid kit for emergency situations", "transport"),
        ("Two bus routes were merged without any notice to affected students", "transport"),
        ("The bus frequently takes longer alternate routes adding travel time", "transport"),
        ("Bus is not sanitised and cleaned regularly causing hygiene issues", "transport"),
        ("Fuel shortage caused bus to be cancelled without informing students", "transport"),
        ("Special bus for students with disabilities is not available", "transport"),
        ("Bus timetable for semester end exams was not updated on time", "transport"),
        ("Complaint about reckless bus driver was ignored by transport office", "transport"),
        ("No bus service is provided during semester break for outstation students", "transport"),

        # OTHER
        ("Stray dogs inside campus are aggressive and biting students", "other"),
        ("Canteen food prices are very high compared to outside market rates", "other"),
        ("No dedicated parking area for two wheelers near academic blocks", "other"),
        ("Sports equipment in the ground is damaged and not replaced", "other"),
        ("Medical centre timings are too short and doctor is often absent", "other"),
        ("Campus garbage bins are overflowing and not cleaned regularly", "other"),
        ("Anti-ragging policy is not being enforced properly in college", "other"),
        ("Canteen does not provide any healthy food options for students", "other"),
        ("No proper signage or directions available inside the campus", "other"),
        ("Lost and found facility is not available anywhere in campus", "other"),
        ("Student grievance cell does not work and ignores complaints", "other"),
        ("Career guidance counsellor is never available for appointments", "other"),
        ("Campus smoking policy is not followed and enforcement is absent", "other"),
        ("No mental health counselling service is available on campus", "other"),
        ("Student welfare fund is collected but students see no benefit of it", "other"),
        ("NSS activities are being conducted only on paper and not actually done", "other"),
        ("Canteen opens very late and students miss breakfast before class", "other"),
        ("College website has wrong information about courses and facilities", "other"),
        ("Internship cell does not assist students from all departments equally", "other"),
        ("Placement cell focuses only on IT companies ignoring other sectors", "other"),
        ("Library subscription to online journals has expired and not renewed", "other"),
        ("Language lab is closed and no practical sessions have been conducted", "other"),
        ("Students with disabilities are not provided adequate support services", "other"),
        ("Anti-harassment committee details are not displayed in campus", "other"),
        ("Cultural committee has not organized any student events this semester", "other"),
        ("Swimming pool is closed without any official announcement", "other"),
        ("Annual sports day was cancelled at last minute without informing anyone", "other"),
        ("College social media handles share only promotional content not info", "other"),
        ("Guest lecture events are not being organised regularly this year", "other"),
        ("Campus map on website does not show the new building locations", "other"),
    ]

    texts  = [t for t, _ in training_data]
    labels = [l for _, l in training_data]

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(
            max_features=5000, ngram_range=(1, 3),
            stop_words='english', sublinear_tf=True, min_df=1
        )),
        ('clf', LogisticRegression(
            C=5.0, max_iter=1000, random_state=42,
            multi_class='multinomial', solver='lbfgs'
        ))
    ])

    scores = cross_val_score(pipeline, texts, labels, cv=5, scoring='accuracy')
    print(f"Cross-validation accuracy: {scores.mean()*100:.1f}% (+-{scores.std()*100:.1f}%)")
    pipeline.fit(texts, labels)

    from ml_models.complaint_classifier import ComplaintClassifier
    import types
    clf = ComplaintClassifier.__new__(ComplaintClassifier)
    clf.pipeline = pipeline
    clf.categories = list(set(labels))

    def predict(self, complaint_text):
        text = re.sub(r'[^a-zA-Z\s]', ' ', complaint_text.lower()).strip()
        proba = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_
        top_idx = proba.argsort()[::-1]
        return {
            'category': classes[top_idx[0]],
            'confidence': float(proba[top_idx[0]]),
            'top_3': [{'category': classes[i], 'confidence': float(proba[i])} for i in top_idx[:3]]
        }
    clf.predict = types.MethodType(predict, clf)

    with open(save_path('classifier.pkl'), 'wb') as f:
        pickle.dump(clf, f)
    print(f"Classifier saved  — {len(texts)} samples, {len(set(labels))} categories")


# =============================================================================
# 2. PRIORITY PREDICTOR
# =============================================================================
def train_priority_predictor():
    print("\n" + "="*60)
    print("2. Training Priority Predictor")
    print("="*60)

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.pipeline import Pipeline
    from sklearn.model_selection import cross_val_score

    training_data = [
        # URGENT
        ("Water pipe burst flooding the corridor urgent help needed immediately", "urgent"),
        ("URGENT electrical sparks from wiring in lab fire hazard dangerous", "urgent"),
        ("Student collapsed in hostel no medical help available emergency", "urgent"),
        ("Sexual harassment incident reported needs immediate action", "urgent"),
        ("Fire alarm going off in block A smoke visible evacuate now", "urgent"),
        ("Stray dog bit student outside canteen bleeding needs first aid urgent", "urgent"),
        ("Online exam platform crashed in the middle of the examination happening now", "urgent"),
        ("Roof of old classroom has partially collapsed danger to students", "urgent"),
        ("Gas leak smell near canteen very dangerous immediate attention needed", "urgent"),
        ("Student is being ragged by seniors needs urgent intervention", "urgent"),
        ("Power supply to medical centre is cut off patients inside urgent", "urgent"),
        ("Elevator stuck with students inside cannot open emergency help needed", "urgent"),
        ("Bus accident on way to college students injured need hospital help", "urgent"),
        ("Flood water entering ground floor classrooms urgent drainage needed", "urgent"),
        ("Unknown person with weapon seen inside campus security emergency", "urgent"),

        # HIGH
        ("Examination hall ticket not issued and exam is in two days", "high"),
        ("Scholarship not credited account shows zero before fee deadline", "high"),
        ("WiFi has been completely down for five days affecting all students", "high"),
        ("Semester registration portal shows error with only one day remaining", "high"),
        ("Fee payment deadline tomorrow but portal is not processing payments", "high"),
        ("Water supply completely cut off in hostel for more than three days", "high"),
        ("Mid semester exam marks not entered and result date is approaching", "high"),
        ("College bus has not arrived for three consecutive days students stranded", "high"),
        ("Internet down in entire campus for four days affecting online classes", "high"),
        ("Student medical certificate needed urgently for visa application", "high"),
        ("Result portal shows wrong grades affecting placement eligibility", "high"),
        ("Mess food has made multiple students sick this week needs attention", "high"),
        ("Printer broken with mass printing deadline for projects tomorrow", "high"),
        ("Campus lights completely off in all areas creating security risk at night", "high"),
        ("Broken glass on laboratory floor students walking barefoot danger", "high"),

        # MEDIUM
        ("Assignment deadline should be extended as the topic was just covered", "medium"),
        ("Classroom projector is not working properly during lectures", "medium"),
        ("WiFi speed is slow in hostel affecting online study and assignments", "medium"),
        ("Mess food quality has gone down compared to last semester", "medium"),
        ("Library does not have enough copies of prescribed textbook", "medium"),
        ("Bus is running 20 minutes late on most mornings this week", "medium"),
        ("Attendance marked incorrectly for two students in my class", "medium"),
        ("College portal is slow and takes long time to load pages", "medium"),
        ("Classroom air conditioning is not set to right temperature", "medium"),
        ("Request for bonafide certificate submitted 10 days ago no update", "medium"),
        ("Hostel room cleaning is done only once a week not enough", "medium"),
        ("Professor cancelled three classes in a row without any notice", "medium"),
        ("Computer lab has some systems that boot very slowly", "medium"),
        ("Canteen closes at 4pm but many students have classes till 5pm", "medium"),
        ("Study room in library does not have enough seating for all students", "medium"),
        ("Campus road has potholes causing discomfort for cyclists", "medium"),
        ("Notice board information is outdated by more than a month", "medium"),
        ("Online class link shared by professor expired before class time", "medium"),
        ("Fee receipt not sent to my email after successful payment", "medium"),
        ("Hostel visitor log is not being maintained properly", "medium"),

        # LOW
        ("Could the canteen please add more south Indian food options", "low"),
        ("Suggestion to add more benches near the academic block garden", "low"),
        ("It would be nice if library extended closing time by one hour", "low"),
        ("Request to organise more cultural events this academic semester", "low"),
        ("Feedback about college website needing a better mobile version", "low"),
        ("Suggesting to plant more trees in the campus open spaces", "low"),
        ("Requesting a suggestion box to be placed near admin office", "low"),
        ("Would like a dedicated study area near the hostel block", "low"),
        ("Requesting better signage for new students to find departments", "low"),
        ("Canteen tables could use better chairs for longer sitting comfort", "low"),
        ("Hostel common room TV remote is missing but TV works fine", "low"),
        ("Please add more power sockets in the library reading area", "low"),
        ("Would appreciate if gym had longer working hours on weekends", "low"),
        ("Request for potted plants to be placed in corridor for aesthetics", "low"),
        ("Suggestion to have a water vending machine near exam halls", "low"),
        ("Would like to see a weekly email digest of campus events", "low"),
        ("Basketball court could use new nets for the hoops", "low"),
        ("Footpath near parking could have better paving stones", "low"),
        ("It would help if college app showed mess menu for the week", "low"),
        ("Campus map on website could include the new buildings", "low"),
    ]

    texts  = [t for t, _ in training_data]
    labels = [l for _, l in training_data]

    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=3000, ngram_range=(1, 3),
                                  stop_words='english', sublinear_tf=True)),
        ('clf', GradientBoostingClassifier(n_estimators=200, learning_rate=0.1,
                                           max_depth=4, random_state=42))
    ])

    scores = cross_val_score(pipeline, texts, labels, cv=5, scoring='accuracy')
    print(f"Cross-validation accuracy: {scores.mean()*100:.1f}% (+-{scores.std()*100:.1f}%)")
    pipeline.fit(texts, labels)

    from ml_models.priority_predictor import PriorityPredictor
    import types
    pp = PriorityPredictor.__new__(PriorityPredictor)
    pp.pipeline = pipeline

    REASONING = {
        'urgent': 'Immediate safety/critical deadline risk — requires same-day action.',
        'high':   'Significant impact on studies or daily life — resolve within 24-48 hours.',
        'medium': 'Moderate inconvenience — should be resolved within 3-5 working days.',
        'low':    'Minor suggestion — can be addressed at next available opportunity.',
    }

    def predict_priority(self, text, category=None):
        clean = re.sub(r'[^a-zA-Z\s]', ' ', text.lower()).strip()
        proba  = self.pipeline.predict_proba([clean])[0]
        classes = self.pipeline.classes_
        top_idx = proba.argsort()[::-1]
        priority = classes[top_idx[0]]
        return {
            'priority': priority,
            'confidence': float(proba[top_idx[0]]),
            'reasoning': REASONING.get(priority, ''),
            'all_scores': {classes[i]: float(proba[i]) for i in range(len(classes))}
        }
    pp.predict_priority = types.MethodType(predict_priority, pp)

    with open(save_path('priority_predictor.pkl'), 'wb') as f:
        pickle.dump(pp, f)
    print(f"Priority predictor saved — {len(texts)} samples")


# =============================================================================
# 3. SENTIMENT ANALYZER
# =============================================================================
def train_sentiment_analyzer():
    print("\n" + "="*60)
    print("3. Saving Enhanced Sentiment Analyzer")
    print("="*60)

    from ml_models.sentiment_analyzer import SentimentAnalyzer
    from textblob import TextBlob
    import types

    analyzer = SentimentAnalyzer()
    analyzer.negative_intensifiers = [
        'very','extremely','absolutely','completely','totally','utterly','highly',
        'severely','badly','terribly','incredibly','deeply','outright','profoundly',
        'enormously','awfully','dreadfully','unbearably','outrageously','desperately'
    ]
    analyzer.frustration_indicators = [
        'frustrated','annoyed','angry','disappointed','upset','irritated','fed up',
        'sick of','tired of','enough','unacceptable','ridiculous','pathetic',
        'disgusted','furious','outraged','helpless','hopeless','ignored','neglected',
        'embarrassed','humiliated','harassed','disrespected','cheated','unfair',
        'injustice','terrible','horrible','worst','useless','incompetent','careless',
        'rude','unprofessional','irresponsible','disgraceful','shameful','shocking'
    ]
    analyzer.urgency_words = [
        'urgent','emergency','immediately','asap','critical','dangerous','hazardous',
        'severe','serious','now','today','deadline','overdue','escalate','must'
    ]
    analyzer.positive_words = [
        'thank','appreciate','helpful','excellent','great','good','satisfied',
        'resolved','happy','pleased','wonderful','amazing'
    ]

    def analyze(self, text):
        try:
            blob = TextBlob(text)
            polarity     = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            text_lower   = text.lower()

            intensifier_count = sum(1 for w in self.negative_intensifiers if w in text_lower)
            frustration_count = sum(1 for p in self.frustration_indicators if p in text_lower)
            urgency_count     = sum(1 for u in self.urgency_words           if u in text_lower)
            positive_count    = sum(1 for p in self.positive_words          if p in text_lower)
            exclamation_count = text.count('!')
            capital_ratio     = sum(1 for c in text if c.isupper()) / max(len(text), 1)

            adj  = polarity
            adj -= 0.25 * frustration_count
            adj -= 0.08 * intensifier_count if polarity < 0 else 0
            adj -= 0.08 * urgency_count
            adj += 0.10 * positive_count
            if exclamation_count >= 2: adj -= 0.08
            if capital_ratio > 0.25:   adj -= 0.12
            adj = max(-1.0, min(1.0, adj))

            urgency_score = urgency_count * 2 + frustration_count + (1 if capital_ratio > 0.2 else 0)
            if   urgency_score >= 3 or adj <= -0.6: urgency = 'critical'
            elif urgency_score >= 2 or adj <= -0.35: urgency = 'high'
            elif urgency_score >= 1 or adj <= -0.1:  urgency = 'medium'
            else:                                     urgency = 'normal'

            if   adj >= 0.3:  sentiment, emoji = 'positive',         '😊'
            elif adj >= 0.1:  sentiment, emoji = 'slightly_positive', '🙂'
            elif adj >= -0.1: sentiment, emoji = 'neutral',           '😐'
            elif adj >= -0.3: sentiment, emoji = 'slightly_negative', '😕'
            elif adj >= -0.6: sentiment, emoji = 'negative',          '😞'
            else:             sentiment, emoji = 'very_negative',     '😡'

            if   frustration_count >= 2 or sentiment == 'very_negative': emotion = 'frustrated'
            elif urgency_count >= 1:                                       emotion = 'concerned'
            elif sentiment in ('negative','slightly_negative'):            emotion = 'dissatisfied'
            elif sentiment == 'neutral':                                   emotion = 'calm'
            else:                                                          emotion = 'satisfied'

            rec_map = {
                'very_negative':    '🚨 High priority: User is very frustrated. Immediate personal response recommended.',
                'negative':         '⚡ User is dissatisfied. Quick resolution and acknowledgement suggested.',
                'slightly_negative':'👀 User has concerns. Timely response needed within 48 hours.',
                'neutral':          '✅ Standard complaint. Process through normal workflow.',
                'slightly_positive':'📋 Routine request. Handle at earliest convenience.',
                'positive':         '😊 Positive tone. Likely a suggestion or appreciation.',
            }

            return {
                'sentiment': sentiment,
                'polarity':  round(float(adj), 3),
                'original_polarity': round(float(polarity), 3),
                'subjectivity': round(float(subjectivity), 3),
                'urgency_indicator': urgency,
                'emotion': emotion,
                'emoji':   emoji,
                'satisfaction_score': round((adj + 1) * 50, 1),
                'metrics': {
                    'frustration_indicators': frustration_count,
                    'urgency_words':          urgency_count,
                    'intensifiers':           intensifier_count,
                    'exclamation_marks':      exclamation_count,
                    'capital_ratio':          round(capital_ratio, 3),
                },
                'recommendation': rec_map.get(sentiment, 'Process normally.')
            }
        except Exception as e:
            return {
                'sentiment': 'neutral', 'polarity': 0.0,
                'urgency_indicator': 'normal', 'emotion': 'calm',
                'emoji': '😐', 'satisfaction_score': 50.0,
                'recommendation': 'Process as standard complaint.',
                'metrics': {}
            }

    analyzer.analyze = types.MethodType(analyze, analyzer)

    with open(save_path('sentiment_analyzer.pkl'), 'wb') as f:
        pickle.dump(analyzer, f)
    print("Sentiment analyzer saved with enhanced keyword lists")


# =============================================================================
# 4. RESOLUTION TIME PREDICTOR
# =============================================================================
def train_resolution_predictor():
    print("\n" + "="*60)
    print("4. Training Resolution Time Predictor")
    print("="*60)

    from sklearn.ensemble import RandomForestRegressor
    import numpy as np, types
    from datetime import datetime, timedelta

    # (category, priority, desc_len, title_len, day_of_week, hour, has_attachment, resolution_hours)
    historical = [
        ('technical','urgent',80,25,2,10,1,3),  ('technical','urgent',60,20,1,9,0,5),
        ('technical','high',120,30,3,14,1,8),   ('technical','high',100,28,0,11,0,10),
        ('technical','medium',90,22,4,15,1,18), ('technical','medium',70,18,2,13,0,24),
        ('technical','low',80,20,5,10,0,48),    ('technical','low',60,15,6,14,0,60),
        ('technical','urgent',50,18,0,8,1,4),   ('technical','high',90,25,1,10,1,9),
        ('technical','medium',110,30,3,16,0,20),('technical','urgent',75,22,2,7,0,6),
        ('technical','high',85,27,4,12,1,12),   ('technical','medium',95,24,5,11,0,30),
        ('technical','low',65,19,1,9,1,72),     ('technical','urgent',55,17,3,8,1,4),
        ('technical','high',105,29,2,11,0,11),  ('technical','medium',80,21,0,14,1,22),

        ('hostel','urgent',100,28,1,6,1,12),    ('hostel','urgent',90,25,0,7,0,15),
        ('hostel','high',130,35,2,10,1,24),     ('hostel','high',110,30,3,11,0,30),
        ('hostel','medium',120,32,4,9,1,48),    ('hostel','medium',100,28,1,14,0,60),
        ('hostel','low',80,22,5,10,0,96),       ('hostel','low',70,20,6,12,0,120),
        ('hostel','urgent',85,24,2,8,1,10),     ('hostel','high',115,33,0,13,1,28),
        ('hostel','medium',105,29,3,16,0,52),   ('hostel','urgent',95,27,4,6,0,18),
        ('hostel','high',125,34,1,9,1,26),      ('hostel','medium',90,26,2,10,0,55),
        ('hostel','low',75,21,5,14,1,108),      ('hostel','high',108,31,0,12,0,32),
        ('hostel','medium',112,30,4,15,1,58),   ('hostel','urgent',88,26,1,7,0,14),

        ('transport','urgent',120,35,1,7,1,24), ('transport','urgent',100,30,2,6,0,28),
        ('transport','high',140,38,0,8,1,36),   ('transport','high',120,32,3,9,0,42),
        ('transport','medium',130,35,4,10,1,72),('transport','medium',110,28,1,14,0,84),
        ('transport','low',90,24,5,11,0,120),   ('transport','low',80,22,6,12,0,144),
        ('transport','urgent',110,32,2,7,1,20), ('transport','high',130,36,0,10,1,38),
        ('transport','medium',120,30,3,15,0,78),('transport','urgent',105,28,4,8,0,25),

        ('academic','urgent',150,40,1,9,1,24),  ('academic','urgent',130,36,2,10,0,30),
        ('academic','high',160,42,0,11,1,48),   ('academic','high',140,38,3,12,0,60),
        ('academic','medium',150,40,4,13,1,96), ('academic','medium',130,35,1,14,0,120),
        ('academic','low',110,30,5,10,0,168),   ('academic','low',100,28,6,11,0,192),
        ('academic','urgent',140,38,2,9,1,28),  ('academic','high',155,41,0,12,1,52),
        ('academic','medium',145,39,3,15,0,100),('academic','urgent',125,34,4,10,0,32),

        ('infrastructure','urgent',170,44,1,8,1,18), ('infrastructure','urgent',150,40,2,7,0,24),
        ('infrastructure','high',180,46,0,9,1,48),   ('infrastructure','high',160,42,3,10,0,60),
        ('infrastructure','medium',170,44,4,11,1,96),('infrastructure','medium',150,40,1,12,0,120),
        ('infrastructure','low',130,36,5,9,0,168),   ('infrastructure','low',120,32,6,10,0,240),
        ('infrastructure','urgent',155,42,2,8,1,20), ('infrastructure','high',175,45,0,11,1,52),
        ('infrastructure','medium',165,43,3,14,0,100),('infrastructure','urgent',145,39,4,7,0,22),

        ('administrative','urgent',160,42,1,9,1,24), ('administrative','urgent',140,38,2,10,0,36),
        ('administrative','high',170,44,0,11,1,60),  ('administrative','high',150,40,3,12,0,72),
        ('administrative','medium',160,42,4,13,1,120),('administrative','medium',140,38,1,14,0,144),
        ('administrative','low',120,34,5,10,0,192),  ('administrative','low',110,30,6,11,0,240),
        ('administrative','urgent',145,40,2,9,1,28), ('administrative','high',165,43,0,12,1,65),
        ('administrative','medium',155,41,3,15,0,130),('administrative','urgent',135,37,4,10,0,32),

        ('other','urgent',100,28,1,9,1,24),  ('other','urgent',90,25,2,10,0,30),
        ('other','high',120,32,0,11,1,48),   ('other','high',110,30,3,12,0,60),
        ('other','medium',115,31,4,13,1,72), ('other','medium',100,28,1,14,0,84),
        ('other','low',85,24,5,10,0,120),    ('other','low',75,20,6,11,0,144),
        ('other','urgent',105,29,2,9,1,22),  ('other','high',115,31,0,12,1,50),
        ('other','medium',108,30,3,15,0,76), ('other','urgent',95,27,4,10,0,26),
    ]

    categories = ['academic','infrastructure','administrative','technical','hostel','transport','other']
    priorities  = ['low','medium','high','urgent']

    X, y = [], []
    for row in historical:
        cat,pri,dl,tl,dow,hr,att,hrs = row
        X.append([categories.index(cat), priorities.index(pri), dl, tl, dow, hr, att])
        y.append(hrs)

    model = RandomForestRegressor(n_estimators=300, max_depth=8,
                                  min_samples_leaf=2, random_state=42)
    model.fit(np.array(X), np.array(y))
    mae = np.mean(np.abs(np.array(y) - model.predict(np.array(X))))
    print(f"Training MAE: {mae:.1f} hours")

    from ml_models.resolution_time_predictor import ResolutionTimePredictor
    rtp = ResolutionTimePredictor.__new__(ResolutionTimePredictor)
    rtp.model      = model
    rtp.categories = categories
    rtp.priorities  = priorities
    rtp.is_trained  = True
    rtp.avg_resolution_times = {'academic':96,'infrastructure':120,'administrative':144,
                                 'technical':18,'hostel':48,'transport':60,'other':72}
    rtp.priority_multipliers = {'low':1.6,'medium':1.0,'high':0.55,'urgent':0.25}

    def predict(self, complaint):
        cat = complaint.get('category','other')
        pri = complaint.get('priority','medium')
        if cat not in self.categories: cat = 'other'
        if pri not in self.priorities:  pri = 'medium'
        desc_len  = len(complaint.get('description',''))
        title_len = len(complaint.get('title',''))
        dow = complaint.get('day_of_week', datetime.now().weekday())
        hr  = complaint.get('hour', datetime.now().hour)
        att = 1 if complaint.get('has_attachment', False) else 0
        feats = [[self.categories.index(cat), self.priorities.index(pri),
                  desc_len, title_len, dow, hr, att]]
        predicted_hours = max(1.0, float(self.model.predict(feats)[0]))
        predicted_days  = predicted_hours / 24
        resolution_date = datetime.now() + timedelta(hours=predicted_hours)

        if   predicted_hours < 1:    time_est = "Less than 1 hour"
        elif predicted_hours < 24:   time_est = f"{int(predicted_hours)} hours"
        elif predicted_days  < 2:    time_est = "1-2 days"
        elif predicted_days  < 7:    time_est = f"{int(predicted_days)} days"
        else:
            w = int(predicted_days / 7)
            time_est = f"{w} week{'s' if w>1 else ''}"

        factors = []
        if pri=='urgent': factors.append("Urgent priority — escalated processing")
        elif pri=='high': factors.append("High priority — fast-tracked for resolution")
        elif pri=='low':  factors.append("Low priority — scheduled at next availability")
        if cat=='technical':        factors.append("Technical issues typically resolved quickly")
        elif cat=='infrastructure': factors.append("Infrastructure repairs may require procurement time")
        elif cat=='administrative': factors.append("Administrative processes follow formal procedures")
        if dow >= 5: factors.append("Submitted on weekend — processing begins Monday")
        if hr  >= 18: factors.append("Submitted after hours — reviewed next business day")
        if att:       factors.append("Attachment provided — aids faster diagnosis")

        return {
            'estimated_hours': round(predicted_hours,1),
            'estimated_days':  round(predicted_days,1),
            'time_estimate':   time_est,
            'estimated_resolution_date': resolution_date.strftime('%Y-%m-%d %H:%M'),
            'range': {'min_hours': round(predicted_hours*0.75,1),
                      'max_hours': round(predicted_hours*1.35,1)},
            'confidence': 'high',
            'factors': factors
        }
    rtp.predict = types.MethodType(predict, rtp)

    with open(save_path('resolution_predictor.pkl'), 'wb') as f:
        pickle.dump(rtp, f)
    print(f"Resolution predictor saved — {len(X)} samples, is_trained=True")


# =============================================================================
# 5 & 6. DUPLICATE DETECTOR + SMART SEARCH
# =============================================================================
def train_duplicate_detector():
    print("\n" + "="*60)
    print("5. Saving Duplicate Detector")
    print("="*60)
    from ml_models.duplicate_detector import DuplicateDetector
    dd = DuplicateDetector()
    with open(save_path('duplicate_detector.pkl'), 'wb') as f:
        pickle.dump(dd, f)
    print("Duplicate detector saved")

def train_smart_search():
    print("\n" + "="*60)
    print("6. Saving Smart Search")
    print("="*60)
    from ml_models.smart_search import SmartSearch
    ss = SmartSearch()
    with open(save_path('smart_search.pkl'), 'wb') as f:
        pickle.dump(ss, f)
    print("Smart search saved")


# =============================================================================
# MAIN
# =============================================================================
if __name__ == '__main__':
    print("=" * 60)
    print("  CMS - Retraining All ML Models")
    print("=" * 60)

    for fn_name, fn in [
        ("Classifier",          train_classifier),
        ("Priority Predictor",  train_priority_predictor),
        ("Sentiment Analyzer",  train_sentiment_analyzer),
        ("Resolution Predictor",train_resolution_predictor),
        ("Duplicate Detector",  train_duplicate_detector),
        ("Smart Search",        train_smart_search),
    ]:
        try:
            fn()
            print(f"[OK] {fn_name}")
        except Exception as e:
            import traceback
            print(f"[FAILED] {fn_name}: {e}")
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("  Done! Restart server:  python app.py")
    print("=" * 60)
