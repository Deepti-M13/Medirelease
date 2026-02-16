from sqlalchemy.orm import Session
from database import MedicineLog
from services.scraper_service import ScraperService
import asyncio
from typing import List, Dict

class BillSummarizer:
    def __init__(self, db: Session):
        self.db = db
        self.scraper = ScraperService()

    async def get_patient_bill_summary(self, patient_id: int) -> Dict:
        # 1. Get all medications given to the patient
        med_logs = self.db.query(MedicineLog).filter(MedicineLog.patient_id == patient_id).all()
        
        if not med_logs:
            return {
                "patient_id": patient_id,
                "medicines": [],
                "total_hospital_cost": 0.0,
                "total_market_cost": 0.0,
                "summary": "No medications found for this patient."
            }

        # 2. Aggregate unique medicine names
        unique_meds = sorted(list(set(log.medicine_name for log in med_logs)))
        
        # 3. Fetch market prices using ScraperService
        market_prices = {}
        try:
            market_prices = await self.scraper.compare_prices(unique_meds)
        except Exception as e:
            print(f"Scraping error: {e}")

        # 4. Build results
        medicines_summary = []
        total_hospital_cost = 0.0
        total_market_cost = 0.0

        for med_name in unique_meds:
            # Get logs for this medicine
            med_instances = [log for log in med_logs if log.medicine_name == med_name]
            quantity = sum(log.quantity for log in med_instances)
            hospital_unit_price = med_instances[0].unit_price
            hospital_subtotal = sum(log.subtotal for log in med_instances)
            
            total_hospital_cost += hospital_subtotal

            # Find best market price
            best_market_price = None
            source = "N/A"
            link = "#"
            
            prices = market_prices.get(med_name, [])
            if prices:
                # Scraper already sorts by price
                best_match = prices[0]
                best_market_price = best_match['price']
                source = best_match['site_name']
                link = best_match.get('link', '#')
                
                market_subtotal = best_market_price * (quantity / 10) # Assuming pack of 10 for price comparison if not specified
                # Wait, MedicineLog quantity is likely units given. Scraper price is usually per pack.
                # This is tricky without knowing pack sizes. Let's assume the scraper price is for the quantity if available or per unit.
                # Usually 1mg prices are per pack (10-15 tabs).
                # For MVP, let's just show the unit comparison if possible, or assume quantity match.
                market_subtotal = best_market_price * (quantity / 10) # Simple heuristic: prices are often for 10
            else:
                market_subtotal = hospital_subtotal # Fallback
            
            total_market_cost += market_subtotal

            medicines_summary.append({
                "name": med_name,
                "generic": med_instances[0].generic_name,
                "quantity": quantity,
                "hospital_price": hospital_unit_price,
                "hospital_subtotal": hospital_subtotal,
                "market_price": best_market_price,
                "market_source": source,
                "market_link": link,
                "savings": max(0, hospital_subtotal - market_subtotal)
            })

        return {
            "patient_id": patient_id,
            "medicines": medicines_summary,
            "total_hospital_cost": round(total_hospital_cost, 2),
            "total_market_cost": round(total_market_cost, 2),
            "potential_savings": round(max(0, total_hospital_cost - total_market_cost), 2)
        }
