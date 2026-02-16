import unittest
import os
import sys

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.services.negotiation import analyze_negotiability, generate_negotiation_summary

class TestNegotiationService(unittest.TestCase):

    def test_critical_care_item(self):
        item = {
            'description': 'Injection Adrenaline 1mg',
            'category': 'medicines',
            'excess': 200
        }
        result = analyze_negotiability(item)
        self.assertEqual(result['status'], 'Not negotiable', "Adrenaline should be non-negotiable")
        self.assertIn("Critical care charge", result['wording'])

    def test_high_excess_critical_care(self):
        item = {
            'description': 'ICU Oxygen Supply',
            'category': 'room_charges',
            'excess': 8000
        }
        result = analyze_negotiability(item)
        self.assertEqual(result['status'], 'Partially negotiable', "High excess ICU charge should be partially negotiable")
        self.assertEqual(result['amount'], 4000.0)

    def test_common_medicine(self):
        item = {
            'description': 'Tablet Pan D',
            'category': 'medicines',
            'excess': 150
        }
        result = analyze_negotiability(item)
        self.assertEqual(result['status'], 'Negotiable')
        self.assertEqual(result['amount'], 150)
        self.assertIn("generic equivalent", result['wording'])

    def test_investigation(self):
        item = {
            'description': 'CBC Hemogram',
            'category': 'investigations',
            'excess': 400
        }
        result = analyze_negotiability(item)
        self.assertEqual(result['status'], 'Partially negotiable')
        self.assertEqual(result['amount'], 300.0)

    def test_room_rent(self):
        item = {
            'description': 'Private Ward Room Rent',
            'category': 'room_charges',
            'excess': 2000
        }
        result = analyze_negotiability(item)
        self.assertEqual(result['status'], 'Partially negotiable')
        self.assertIn("check-in and check-out timings", result['wording'])

    def test_summary_generation(self):
        items = [
            {'description': 'Tab PCM', 'category': 'medicines', 'excess': 100},
            {'description': 'MRI Scan', 'category': 'investigations', 'excess': 2000},
            {'description': 'ICU Kit', 'category': 'medicines', 'excess': 50} # Critical keyword absent, normal med rules apply unless strictly mapped
        ]
        # Wait, ICU kit might not trigger critical strictly by name unless added to keywords.
        # Let's use robust keywords. 'ICU' is in keywords.
        # "ICU Kit" -> contains "icu", so Rule 1 applies.
        
        summary = generate_negotiation_summary(items)
        
        # 1. PCM: Negotiable (100)
        # 2. MRI: Partial (2000 * 0.75 = 1500)
        # 3. ICU Kit: Critical, excess 50 (< 5000) -> Not Negotiable (0)
        
        expected_negotiable = 100 + 1500 + 0
        self.assertEqual(summary['potentially_negotiable'], expected_negotiable)
        self.assertEqual(summary['total_overcharge'], 2150)

if __name__ == '__main__':
    unittest.main()
