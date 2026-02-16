from playwright.async_api import async_playwright
import asyncio
from typing import List, Dict, Optional
from datetime import datetime
import re
import urllib.parse
import traceback

class ScraperService:
    def __init__(self):
        self.browser = None
        self.context = None
        self.playwright = None

    async def _get_page(self):
        if not self.context:
            await self.initialize()
        return await self.context.new_page()

    async def initialize(self):
        if not self.playwright:
            print("Starting Playwright...")
            self.playwright = await async_playwright().start()
            print("Launching Chromium...")
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--disable-dev-shm-usage', '--no-sandbox'] # Help in certain environments
            )
            print("Creating Context...")
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                viewport={'width': 1280, 'height': 800}
            )

    async def cleanup(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.browser = None
        self.context = None
        self.playwright = None

    async def scrape_tata_1mg(self, medicine_name: str) -> List[Dict]:
        results = []
        page = None
        try:
            print(f"Scraping Tata 1mg for {medicine_name}...")
            page = await self._get_page()
            url = f"https://www.1mg.com/search/all?name={urllib.parse.quote(medicine_name)}"
            await page.goto(url, timeout=45000, wait_until="networkidle")
            
            # Additional wait for actual content if networkidle isn't enough
            try:
                await page.wait_for_selector('[class*="VerticalProductTile__styledContainer"], [class*="product-card"]', timeout=15000)
            except:
                pass

            # Find product cards - Using more specific classes found in local HTML
            cards = await page.locator('[class*="VerticalProductTile__styledContainer"], [class*="product-box"], [class*="ProductTile"]').all()
            
            if not cards:
                # Very generic fallback: look for any div that contains the medicine name and a price
                cards = await page.locator('div').filter(has_text=re.compile(medicine_name, re.IGNORECASE)).filter(has_text=re.compile(r'₹')).all()

            for card in cards[:5]:
                try:
                    # Name: Any heading or title-like class
                    name = ""
                    # Priority list of selectors
                    name_locs = [
                        card.locator('[class*="VerticalProductTile__header"]'),
                        card.locator('[class*="product-title"]'),
                        card.locator('[class*="title"]'),
                        card.locator('h1,h2,h3,h4,span')
                    ]
                    for loc in name_locs:
                        if await loc.first.count() > 0:
                            t = await loc.first.inner_text(timeout=1000)
                            if t and len(t) > 3: 
                                name = t
                                break
                    
                    # Price: Anything with ₹
                    price_text = ""
                    price_loc = card.locator('[class*="Price__marginLeft"], [class*="price"], span, div').filter(has_text="₹").first
                    if await price_loc.count() > 0:
                        price_text = await price_loc.inner_text(timeout=1000)
                    
                    if not name or not price_text:
                        continue

                    results.append({
                        "medicine_name": name.strip(),
                        "site_name": "Tata 1mg",
                        "price": self._clean_price(price_text),
                        "pack_size": "Check site",
                        "availability": "Available", 
                        "scraped_at": datetime.now().isoformat(),
                        "link": url
                    })
                except: continue
        except Exception as e:
            print(f"Error scraping 1mg: {e}")
        finally:
            if page: 
                try: await page.close()
                except: pass
        return results

    async def scrape_pharmeasy(self, medicine_name: str) -> List[Dict]:
        results = []
        page = None
        try:
            print(f"Scraping PharmEasy for {medicine_name}...")
            page = await self._get_page()
            url = f"https://pharmeasy.in/search/all?name={urllib.parse.quote(medicine_name)}"
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            try:
                await page.wait_for_selector('div[class*="ProductCard"], a[href*="/online-medicine-order/"]', timeout=8000)
            except: pass
                
            cards = await page.locator('div[class*="ProductCard"], a[href*="/online-medicine-order/"]').all()

            for card in cards[:5]:
                try:
                    name = ""
                    name_loc = card.locator('h1, h2, h3, div[class*="Name"], .product-name').first
                    if await name_loc.count() > 0:
                        name = await name_loc.inner_text(timeout=1000)

                    price_text = ""
                    price_loc = card.locator('div[class*="Price"], .product-price, span[class*="price"]').filter(has_text="₹").first
                    if await price_loc.count() > 0:
                        price_text = await price_loc.inner_text(timeout=1000)
                    
                    if not name or not price_text:
                        continue

                    results.append({
                        "medicine_name": name.strip(),
                        "site_name": "PharmEasy",
                        "price": self._clean_price(price_text),
                        "pack_size": "Check link",
                        "availability": "Available",
                        "scraped_at": datetime.now().isoformat(),
                        "link": url
                    })
                except: continue
        except Exception as e:
            print(f"Error scraping PharmEasy: {e}")
        finally:
            if page: 
                try: await page.close()
                except: pass
        return results

    async def scrape_netmeds(self, medicine_name: str) -> List[Dict]:
        results = []
        page = None
        try:
            print(f"Scraping NetMeds for {medicine_name}...")
            page = await self._get_page()
            url = f"https://www.netmeds.com/catalogsearch/result?q={urllib.parse.quote(medicine_name)}"
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            try:
                await page.wait_for_selector('.drug_list, .product-item, div[class*="product"]', timeout=8000)
            except: pass

            cards = await page.locator('.drug_list .drug_item, .product-item, div[class*="product-card"]').all()
            
            for card in cards[:5]:
                try:
                    name = ""
                    name_loc = card.locator('.drug_name, .product-name, h3, div[class*="name"]').first
                    if await name_loc.count() > 0:
                        name = await name_loc.inner_text(timeout=1000)

                    price_text = ""
                    price_loc = card.locator('.final_price, .product-price, .price, span').filter(has_text="₹").first
                    if await price_loc.count() > 0:
                        price_text = await price_loc.inner_text(timeout=1000)
                    
                    if not name or not price_text:
                        continue

                    results.append({
                        "medicine_name": name.strip(),
                        "site_name": "NetMeds",
                        "price": self._clean_price(price_text),
                        "pack_size": "N/A",
                        "availability": "Available",
                        "scraped_at": datetime.now().isoformat(),
                        "link": url
                    })
                except: continue
        except Exception as e:
            print(f"Error scraping NetMeds: {e}")
        finally:
            if page: 
                try: await page.close()
                except: pass
        return results

    async def scrape_apollo(self, medicine_name: str) -> List[Dict]:
        results = []
        page = None
        try:
            print(f"Scraping Apollo Pharmacy for {medicine_name}...")
            page = await self._get_page()
            
            # Try hyphenated path first as it's common for Apollo
            hyphenated_name = medicine_name.replace(" ", "-")
            url = f"https://www.apollopharmacy.in/search-medicines/{urllib.parse.quote(hyphenated_name)}"
            
            try:
                await page.goto(url, timeout=45000, wait_until="networkidle")
            except:
                # Fallback to search query
                url = f"https://www.apollopharmacy.in/search?q={urllib.parse.quote(medicine_name)}"
                await page.goto(url, timeout=45000, wait_until="networkidle")
            
            try:
                # Wait for any product card-like element
                await page.wait_for_selector('[class*="ProductCard"], [class*="product-item"], [class*="MuiGrid-item"]', timeout=15000)
            except: pass
            
            # Use broader selectors
            cards = await page.locator('[class*="ProductCard"], [class*="product-item"], a[href*="/medicine/"], [class*="MuiGrid-item"]').all()
            
            # If still nothing, try to find by text patterns
            if not cards:
                cards = await page.locator('div, a').filter(has_text=re.compile(r'₹')).filter(has_text=re.compile(medicine_name, re.IGNORECASE)).all()

            for card in cards[:5]:
                try:
                    name = ""
                    name_locs = [
                        card.locator('[class*="ProductName"]'),
                        card.locator('[class*="ProductCard_productName"]'),
                        card.locator('h1, h2, h3, div[class*="name"]'),
                        card.locator('.product-name')
                    ]
                    for loc in name_locs:
                        if await loc.first.count() > 0:
                            t = await loc.first.inner_text(timeout=1000)
                            if t and len(t) > 3:
                                name = t
                                break
                    
                    price_text = ""
                    price_loc = card.locator('[class*="Price"], [class*="price"], .price, span').filter(has_text="₹").first
                    if await price_loc.count() > 0:
                        price_text = await price_loc.inner_text(timeout=1000)
                    
                    if not name or not price_text or len(name) < 3:
                        continue

                    results.append({
                        "medicine_name": name.strip(),
                        "site_name": "Apollo Pharmacy",
                        "price": self._clean_price(price_text),
                        "pack_size": "N/A",
                        "availability": "Available",
                        "scraped_at": datetime.now().isoformat(),
                        "link": url
                    })
                except: continue
        except Exception as e:
            print(f"Error scraping Apollo: {e}")
        finally:
            if page: 
                try: await page.close()
                except: pass
        return results

    async def scrape_truemeds(self, medicine_name: str) -> List[Dict]:
        results = []
        page = None
        try:
            print(f"Scraping Truemeds for {medicine_name}...")
            page = await self._get_page()
            url = f"https://www.truemeds.in/search?q={urllib.parse.quote(medicine_name)}"
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            try:
                await page.wait_for_selector('[class*="ProductCard"], div[class*="Card_container"]', timeout=10000)
            except: pass
                
            cards = await page.locator('[class*="ProductCard"], div[class*="Card_container"]').all()

            for card in cards[:5]:
                try:
                    name = ""
                    name_loc = card.locator('h1, h2, h3, div[class*="Name"], [class*="productName"]').first
                    if await name_loc.count() > 0:
                        name = await name_loc.inner_text(timeout=1000)

                    price_text = ""
                    price_loc = card.locator('[class*="sellingPrice"], [class*="Price"], span').filter(has_text="₹").first
                    if await price_loc.count() > 0:
                        price_text = await price_loc.inner_text(timeout=1000)
                    
                    if not name or not price_text:
                        continue

                    results.append({
                        "medicine_name": name.strip(),
                        "site_name": "Truemeds",
                        "price": self._clean_price(price_text),
                        "pack_size": "Check site",
                        "availability": "Available",
                        "scraped_at": datetime.now().isoformat(),
                        "link": url
                    })
                except: continue
        except Exception as e:
            print(f"Error scraping Truemeds: {e}")
        finally:
            if page: 
                try: await page.close()
                except: pass
        return results

    async def scrape_wellnessforever(self, medicine_name: str) -> List[Dict]:
        results = []
        page = None
        try:
            print(f"Scraping Wellness Forever for {medicine_name}...")
            page = await self._get_page()
            url = f"https://wellnessforever.com/search?q={urllib.parse.quote(medicine_name)}"
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            try:
                await page.wait_for_selector('.product-card-container, .product-inner, .product-item, [class*="product"]', timeout=10000)
            except: pass
                
            cards = await page.locator('.product-card-container, .product-inner, .product-item, .product-item-info, div[class*="product-tile"]').all()

            for card in cards[:5]:
                try:
                    name = ""
                    name_locs = [
                        card.locator('.product-name'),
                        card.locator('.product-item-name'),
                        card.locator('a.product-item-link'),
                        card.locator('h3'),
                        card.locator('a.product-title')
                    ]
                    for loc in name_locs:
                        if await loc.first.count() > 0:
                            t = await loc.first.inner_text(timeout=1000)
                            if t and len(t) > 3:
                                name = t
                                break

                    price_text = ""
                    price_loc = card.locator('.price, .special-price, [data-price-type="finalPrice"], span').filter(has_text="₹").first
                    if await price_loc.count() > 0:
                        price_text = await price_loc.inner_text(timeout=1000)
                    
                    if not name or not price_text:
                        continue

                    results.append({
                        "medicine_name": name.strip(),
                        "site_name": "Wellness Forever",
                        "price": self._clean_price(price_text),
                        "pack_size": "Check site",
                        "availability": "Available",
                        "scraped_at": datetime.now().isoformat(),
                        "link": url
                    })
                except: continue
        except Exception as e:
            print(f"Error scraping Wellness Forever: {e}")
        finally:
            if page: 
                try: await page.close()
                except: pass
        return results

    def _clean_price(self, price_text: str) -> float:
        try:
            # Remove currency symbols and comma, then find first number
            cleaned = price_text.replace('₹', '').replace(',', '').strip()
            # Extract only the numeric part (e.g., from "MRP 100.00")
            match = re.search(r'(\d+\.?\d*)', cleaned)
            if match:
                return float(match.group(1))
            return 0.0
        except Exception:
            return 0.0

    async def compare_prices(self, medicine_names: List[str]) -> Dict[str, List[Dict]]:
        all_results = {}
        try:
            await self.cleanup() 
            await self.initialize()
            
            # Skip extremely generic or common noise words that escaped OCR
            skip_words = {'for', 'and', 'the', 'with', 'from', 'each', 'take', 'give'}
            
            for med in medicine_names:
                if med.lower() in skip_words or len(med) < 3:
                    print(f"Skipping extremely generic search term: {med}")
                    all_results[med] = []
                    continue

                tasks = [
                    self.scrape_tata_1mg(med),
                    self.scrape_pharmeasy(med),
                    self.scrape_netmeds(med),
                    self.scrape_apollo(med),
                    self.scrape_truemeds(med),
                    self.scrape_wellnessforever(med)
                ]
                
                print(f"Starting scraping tasks for {med}...")
                site_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                combined_med_results = []
                seen_sites = set()
                
                for i, res in enumerate(site_results):
                    sites = ["1mg", "PharmEasy", "NetMeds", "Apollo", "Truemeds", "Wellness Forever"]
                    site_name = sites[i]
                    
                    if isinstance(res, list):
                        print(f"  - {site_name}: Found {len(res)} results")
                        # Add only unique/top results from each site to avoid massive redundancy
                        # Here we take the top 2 matches if they exist
                        for result in res[:2]:
                            # Simple key to avoid exact duplicates
                            res_key = (result['site_name'], result['price'], result['medicine_name'].lower())
                            if res_key not in seen_sites:
                                combined_med_results.append(result)
                                seen_sites.add(res_key)
                    else:
                        print(f"  - {site_name}: Failed with error: {res}")
                
                # Sort by price and take top results
                combined_med_results.sort(key=lambda x: x['price'])
                all_results[med] = combined_med_results
                await asyncio.sleep(0.5) 
                
        except Exception as e:
            print(f"Critical error in compare_prices: {e}")
            traceback.print_exc()
        finally:
            await self.cleanup()
            
        return all_results
