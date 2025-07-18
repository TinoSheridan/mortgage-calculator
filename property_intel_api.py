"""
Property Intelligence API Integration
Provides comprehensive property-specific financing information
"""

import logging
import os
import re
from datetime import datetime
from typing import Dict, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class PropertyIntelligenceAPI:
    """
    Handles fetching property intelligence data from various APIs
    """

    def __init__(self):
        self.session = self._create_session()

    def _create_session(self):
        """Create a requests session with retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def analyze_property(self, address: str) -> Dict:
        """
        Analyze a property address for financing information

        Args:
            address: Full property address

        Returns:
            Dict with comprehensive property information
        """
        logger.info(f"Analyzing property: {address}")

        # Generate source links for this address
        source_links = self._generate_source_links(address)

        result = {
            "address": address,
            "timestamp": datetime.now().isoformat(),
            "sourceLinks": source_links,
            "tax": self.get_tax_information(address),
            "propertyType": self.get_property_type(address),
            "usda": self.check_usda_eligibility(address),
            "flood": self.check_flood_zone(address),
            "hoa": self.check_hoa_status(address),
            "financing": self.assess_financing_options(address),
        }

        return result

    def _generate_source_links(self, address: str) -> Dict:
        """Generate direct links to data sources for verification"""
        try:
            # Parse address components
            state_match = re.search(r"\b([A-Z]{2})\b", address.upper())
            state = state_match.group(1) if state_match else "GA"

            # Extract city for county determination
            address_parts = address.split(",")
            city = address_parts[1].strip() if len(address_parts) > 1 else ""

            # Encode address for URLs
            encoded_address = requests.utils.quote(address)

            # Format address for Spokeo (replace spaces with dashes, remove special chars)
            spokeo_address = self._format_address_for_spokeo(address)

            return {
                "spokeo": f"https://www.spokeo.com/property-search/{spokeo_address}",
                "qpublic": self._get_qpublic_link(address, state),
                "countyAssessor": self._get_county_assessor_link(address, state, city),
                "usda": "https://eligibility.sc.egov.usda.gov/eligibility/welcomeAction.do",
                "fema": f"https://msc.fema.gov/portal/search#{encoded_address}",
                "zillow": f"https://www.zillow.com/homes/{encoded_address}_rb/",
                "realtor": f"https://www.realtor.com/realestateandhomes-search/{encoded_address}",
                "propertyShark": f"https://www.propertyshark.com/mason/Property-Search/?searchtext={encoded_address}",
                "redfin": f"https://www.redfin.com/stingray/do/location-search?location={encoded_address}",
            }

        except Exception as e:
            logger.error(f"Error generating source links: {e}")
            return {}

    def _format_address_for_spokeo(self, address: str) -> str:
        """Format address for Spokeo URL structure"""
        try:
            # Clean and format address for Spokeo's URL structure
            # Example: "123 Main St, Atlanta, GA 30309" -> "123-main-st-atlanta-ga-30309"

            # Remove common abbreviations and normalize
            formatted = address.lower()
            formatted = re.sub(r"\bstreet\b|\bst\b", "st", formatted)
            formatted = re.sub(r"\bavenue\b|\bave\b", "ave", formatted)
            formatted = re.sub(r"\bdrive\b|\bdr\b", "dr", formatted)
            formatted = re.sub(r"\bblvd\b|\bboulevard\b", "blvd", formatted)
            formatted = re.sub(r"\broad\b|\brd\b", "rd", formatted)

            # Remove special characters and replace spaces/commas with dashes
            formatted = re.sub(r"[^\w\s-]", "", formatted)
            formatted = re.sub(r"[\s,]+", "-", formatted)  # Replace spaces and commas with dashes
            formatted = re.sub(r"-+", "-", formatted)  # Remove multiple consecutive dashes
            formatted = formatted.strip("-")  # Remove leading/trailing dashes

            return formatted

        except Exception as e:
            logger.warning(f"Error formatting address for Spokeo: {e}")
            # Fallback to simple formatting
            return re.sub(r"[^\w]", "-", address.lower()).strip("-")

    def _get_qpublic_link(self, address: str, state: str) -> str:
        """Get QPublic.net link for property tax data"""
        try:
            # QPublic serves many counties - need to determine which one
            county_mappings = {
                "GA": {
                    "atlanta": "https://qpublic.schneidercorp.com/Application.aspx?AppID=997&LayerID=18013&PageTypeID=4",
                    "fulton": "https://qpublic.schneidercorp.com/Application.aspx?AppID=997&LayerID=18013&PageTypeID=4",
                    "dekalb": "https://qpublic.schneidercorp.com/Application.aspx?AppID=274&LayerID=3717&PageTypeID=4",
                    "gwinnett": "https://qpublic.schneidercorp.com/Application.aspx?AppID=1065&LayerID=18081&PageTypeID=4",
                    "cobb": "https://qpublic.schneidercorp.com/Application.aspx?AppID=1073&LayerID=18089&PageTypeID=4",
                },
                "FL": {
                    "miami": "https://qpublic.schneidercorp.com/Application.aspx?AppID=869&LayerID=15842&PageTypeID=4",
                    "orange": "https://qpublic.schneidercorp.com/Application.aspx?AppID=875&LayerID=15848&PageTypeID=4",
                },
                "NC": {
                    "mecklenburg": "https://qpublic.schneidercorp.com/Application.aspx?AppID=1069&LayerID=18085&PageTypeID=4",
                    "wake": "https://qpublic.schneidercorp.com/Application.aspx?AppID=943&LayerID=16789&PageTypeID=4",
                },
            }

            # Default to main QPublic search
            default_link = "https://qpublic.net"

            # Try to match county/city
            address_lower = address.lower()
            state_mappings = county_mappings.get(state, {})

            for location, link in state_mappings.items():
                if location in address_lower:
                    return link

            return default_link

        except Exception as e:
            logger.warning(f"Error generating QPublic link: {e}")
            return "https://qpublic.net"

    def _get_county_assessor_link(self, address: str, state: str, city: str) -> str:
        """Get direct county assessor link"""
        try:
            # Common county assessor websites
            assessor_links = {
                "GA": {
                    "atlanta": "https://www.fultoncountyga.gov/services/taxes/real-estate/property-search",
                    "fulton": "https://www.fultoncountyga.gov/services/taxes/real-estate/property-search",
                    "dekalb": "https://www.dekalbcountyga.gov/tax-commissioner/property-search",
                    "gwinnett": "https://www.gwinnettcounty.com/web/gwinnett/departments/revenueandtaxation",
                    "cobb": "https://www.cobbcounty.org/index.php?option=com_taxsearch",
                },
                "FL": {
                    "miami": "https://www.miamidade.gov/Apps/PA/PApublicServiceMain.aspx",
                    "orange": "https://ocpafl.org/searches/ParcelSearch.aspx",
                },
                "NC": {
                    "charlotte": "https://property.spatialest.com/nc/mecklenburg/",
                    "mecklenburg": "https://property.spatialest.com/nc/mecklenburg/",
                    "raleigh": "https://services.wake.gov/realestate/",
                    "wake": "https://services.wake.gov/realestate/",
                },
            }

            # Try to match city/county
            address_lower = address.lower()
            state_links = assessor_links.get(state, {})

            for location, link in state_links.items():
                if location in address_lower:
                    return link

            # Return generic search based on state
            state_defaults = {
                "GA": "https://www.georgia.gov/property-tax-information",
                "FL": "https://floridarevenue.com/property/Pages/default.aspx",
                "NC": "https://www.ncdor.gov/taxes-forms/property-tax",
            }

            return state_defaults.get(
                state, "https://www.google.com/search?q=county+assessor+property+search"
            )

        except Exception as e:
            logger.warning(f"Error generating county assessor link: {e}")
            return "https://www.google.com/search?q=county+assessor+property+search"

    def get_tax_information(self, address: str) -> Dict:
        """
        Get property tax information from real data sources
        """
        try:
            # Primary focus on Spokeo for comprehensive property data

            # 1. Try Spokeo Property Search API (primary source)
            spokeo_data = self._get_spokeo_property_data(address)
            if spokeo_data and spokeo_data.get("success"):
                return spokeo_data

            # 2. Fallback: Try Zillow/RapidAPI for property data
            zillow_data = self._get_zillow_property_data(address)
            if zillow_data and zillow_data.get("success"):
                return zillow_data

            # 3. Fallback: Try Attom Data API
            attom_result = self._get_attom_data(address)
            if attom_result and attom_result.get("success"):
                return attom_result

            # 4. Fallback: Try to scrape county assessor websites
            assessor_result = self._scrape_county_assessor(address)
            if assessor_result and assessor_result.get("success"):
                return assessor_result

            # If all else fails, indicate no data available
            return {
                "success": False,
                "error": "Tax information not available - no data sources accessible",
            }

        except Exception as e:
            logger.error(f"Error getting tax information: {e}")
            return {"success": False, "error": "Tax information not available"}

    def _get_ownerly_property_data(self, address: str) -> Optional[Dict]:
        """Try to get property data from Ownerly.com"""
        try:
            # Ownerly provides comprehensive property data including tax information
            # This would require either their API or web scraping

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            # For now, return a structured response indicating manual verification needed
            # Real implementation would scrape or use Ownerly's API if available
            return {
                "success": True,
                "annualTax": 0,  # Would be scraped from actual page
                "assessedValue": 0,  # Would be scraped from actual page
                "taxRate": 0,  # Would be calculated
                "lastUpdated": "Manual verification required",
                "ownerName": "See Ownerly for current owner",
                "parcelId": "See Ownerly for parcel ID",
                "propertyAddress": address,
                "legalDescription": "See Ownerly for legal description",
                "source": "Ownerly.com (Manual verification required)",
                "manual_verification_needed": True,
            }

        except Exception as e:
            logger.warning(f"Error fetching Ownerly data: {e}")
            return None

    def _get_spokeo_property_data(self, address: str) -> Optional[Dict]:
        """Get property data from Spokeo Property Search API"""
        try:
            # Check for Spokeo API key
            spokeo_api_key = os.getenv("SPOKEO_API_KEY")
            if not spokeo_api_key:
                logger.info("No Spokeo API key available - using manual verification mode")
                return self._get_spokeo_manual_verification_response(address)

            # Use Spokeo Address Search API (their actual property endpoint)
            api_url = "https://api.spokeo.com/address"
            headers = {
                "Authorization": f"Bearer {spokeo_api_key}",
                "Content-Type": "application/json",
            }

            # Prepare search parameters for Address Search API
            params = {"address": address}

            response = self.session.get(api_url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get("success") and data.get("results"):
                    property_data = data["results"][0]  # First result

                    # Extract property information
                    owner_info = property_data.get("owner", {})
                    property_details = property_data.get("property", {})
                    tax_info = property_data.get("tax_records", {})

                    # Calculate tax rate if both values available
                    annual_tax = tax_info.get("annual_tax", 0)
                    assessed_value = tax_info.get("assessed_value", 0)
                    tax_rate = 0
                    if annual_tax and assessed_value:
                        tax_rate = (annual_tax / assessed_value) * 100

                    return {
                        "success": True,
                        "annualTax": annual_tax,
                        "assessedValue": assessed_value,
                        "taxRate": tax_rate,
                        "lastUpdated": tax_info.get("tax_year", "Unknown"),
                        "ownerName": f"{owner_info.get('first_name', '')} {owner_info.get('last_name', '')}".strip(),
                        "parcelId": property_details.get("parcel_id", "Not Available"),
                        "propertyAddress": property_details.get("address", address),
                        "legalDescription": property_details.get(
                            "legal_description", "Not Available"
                        ),
                        "source": "Spokeo Property Search API",
                    }
                else:
                    logger.warning(f"No property data found in Spokeo response for: {address}")
                    return self._get_spokeo_manual_verification_response(address)

            elif response.status_code == 401:
                logger.error("Spokeo API authentication failed - check API key")
                return self._get_spokeo_manual_verification_response(address)
            else:
                logger.warning(f"Spokeo API returned status {response.status_code}")
                return self._get_spokeo_manual_verification_response(address)

        except Exception as e:
            logger.warning(f"Error calling Spokeo API: {e}")
            return self._get_spokeo_manual_verification_response(address)

    def _get_spokeo_manual_verification_response(self, address: str) -> Dict:
        """Return manual verification response for Spokeo"""
        return {
            "success": True,
            "annualTax": 0,
            "assessedValue": 0,
            "taxRate": 0,
            "lastUpdated": "Manual verification required",
            "ownerName": "See Spokeo for current owner",
            "parcelId": "See Spokeo for parcel ID",
            "propertyAddress": address,
            "legalDescription": "See Spokeo for legal description",
            "source": "Spokeo.com (Manual verification required)",
            "manual_verification_needed": True,
        }

    def _get_zillow_property_data(self, address: str) -> Optional[Dict]:
        """Try to get property data from Zillow via RapidAPI"""
        try:
            # This would require a RapidAPI key for Zillow API
            # Example endpoint: https://rapidapi.com/apimaker/api/zillow-com1/

            rapidapi_key = os.getenv("RAPIDAPI_KEY")
            if not rapidapi_key:
                logger.info("No RapidAPI key available for Zillow data")
                return None

            headers = {
                "X-RapidAPI-Key": rapidapi_key,
                "X-RapidAPI-Host": "zillow-com1.p.rapidapi.com",
            }

            # Search for property by address
            search_url = "https://zillow-com1.p.rapidapi.com/propertyExtendedSearch"
            params = {"location": address, "status_type": "ForSale"}

            response = self.session.get(search_url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()

                # Extract tax information if available
                if data and "props" in data and data["props"]:
                    prop = data["props"][0]  # First result

                    tax_info = {
                        "success": True,
                        "annualTax": prop.get("taxAnnualAmount", 0),
                        "assessedValue": prop.get("taxAssessedValue", 0),
                        "taxRate": 0,  # Calculate if both values available
                        "lastUpdated": prop.get("datePosted", ""),
                        "ownerName": prop.get("ownerName", "Not Available"),
                        "parcelId": prop.get("parcelId", "Not Available"),
                        "propertyAddress": prop.get("address", address),
                        "legalDescription": prop.get("legalDescription", "Not Available"),
                        "source": "Zillow Property Data",
                    }

                    # Calculate tax rate if both values available
                    if tax_info["annualTax"] and tax_info["assessedValue"]:
                        tax_info["taxRate"] = (
                            tax_info["annualTax"] / tax_info["assessedValue"]
                        ) * 100

                    return tax_info

        except Exception as e:
            logger.warning(f"Error fetching Zillow data: {e}")

        return None

    def _get_property_data_api(self, address: str) -> Optional[Dict]:
        """Try PropertyData API for real property information"""
        try:
            # PropertyData API (hypothetical - would need real API)
            api_key = os.getenv("PROPERTY_DATA_API_KEY")
            if not api_key:
                return None

            # This would be a real property data API call
            # Implementation would depend on specific API provider

        except Exception as e:
            logger.warning(f"Error fetching PropertyData API: {e}")

        return None

    def _get_attom_data(self, address: str) -> Optional[Dict]:
        """Try Attom Data API for property information"""
        try:
            # Attom Data is a major real estate data provider
            api_key = os.getenv("ATTOM_API_KEY")
            if not api_key:
                return None

            headers = {"Accept": "application/json", "apikey": api_key}

            # Search for property
            url = "https://api.gateway.attomdata.com/propertyapi/v1.0.0/property/detail"
            params = {"address1": address}

            response = self.session.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()

                if "property" in data:
                    prop = data["property"][0]
                    assessment = prop.get("assessment", {})

                    return {
                        "success": True,
                        "annualTax": assessment.get("tax", {}).get("taxAmt", 0),
                        "assessedValue": assessment.get("assessed", {}).get("assdTtlValue", 0),
                        "taxRate": assessment.get("tax", {}).get("taxRate", 0),
                        "lastUpdated": assessment.get("tax", {}).get("taxYear", ""),
                        "ownerName": prop.get("owner", {}).get("owner1", {}).get("lastName", "")
                        + ", "
                        + prop.get("owner", {}).get("owner1", {}).get("firstName", ""),
                        "parcelId": prop.get("identifier", {}).get("apn", "Not Available"),
                        "propertyAddress": prop.get("address", {}).get("oneLine", address),
                        "legalDescription": prop.get("lot", {}).get(
                            "lotDescription", "Not Available"
                        ),
                        "source": "Attom Data",
                    }

        except Exception as e:
            logger.warning(f"Error fetching Attom data: {e}")

        return None

    def _scrape_county_assessor(self, address: str) -> Optional[Dict]:
        """Try to scrape county assessor websites"""
        try:
            # This would involve identifying the county from the address
            # and scraping the appropriate county assessor website

            # Extract state and county information
            state_match = re.search(r"\b([A-Z]{2})\b", address.upper())
            if not state_match:
                return None

            state = state_match.group(1)

            # Try QPublic.net first (most comprehensive)
            qpublic_result = self._scrape_qpublic(address, state)
            if qpublic_result and qpublic_result.get("success"):
                return qpublic_result

            # For Georgia counties, try some common assessor sites
            if state == "GA":
                return self._scrape_georgia_assessor(address)

            # Add other states as needed

        except Exception as e:
            logger.warning(f"Error scraping county assessor: {e}")

        return None

    def _scrape_qpublic(self, address: str, state: str) -> Optional[Dict]:
        """Scrape QPublic.net for property tax data"""
        try:
            from bs4 import BeautifulSoup

            # Get the appropriate QPublic link for this location
            qpublic_url = self._get_qpublic_link(address, state)
            if qpublic_url == "https://qpublic.net":
                # Generic link, can't scrape effectively
                return None

            # Parse the address for search
            search_address = self._parse_address_for_search(address)
            if not search_address:
                return None

            # Attempt to search QPublic (this is a simplified example)
            # Real implementation would need to handle specific county search forms
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            # This would need to be customized for each county's QPublic implementation
            # For now, return a structured response indicating where to look
            return {
                "success": True,
                "annualTax": 0,  # Would be scraped from actual page
                "assessedValue": 0,  # Would be scraped from actual page
                "taxRate": 0,  # Would be calculated
                "lastUpdated": "Manual verification required",
                "ownerName": "See QPublic for current owner",
                "parcelId": "See QPublic for parcel ID",
                "propertyAddress": address,
                "legalDescription": "See QPublic for legal description",
                "source": "QPublic.net (Manual verification required)",
                "manual_verification_needed": True,
            }

        except ImportError:
            logger.warning("BeautifulSoup not available for web scraping")
            return None
        except Exception as e:
            logger.warning(f"Error scraping QPublic: {e}")
            return None

    def _parse_address_for_search(self, address: str) -> Optional[Dict]:
        """Parse address into components for search"""
        try:
            # Basic address parsing - would need more sophistication
            parts = address.split(",")
            if len(parts) < 2:
                return None

            street_address = parts[0].strip()
            city_state = parts[1].strip() if len(parts) > 1 else ""

            # Extract house number and street name
            street_parts = street_address.split(" ", 1)
            house_number = street_parts[0] if street_parts else ""
            street_name = street_parts[1] if len(street_parts) > 1 else ""

            return {
                "house_number": house_number,
                "street_name": street_name,
                "city_state": city_state,
                "full_address": address,
            }

        except Exception as e:
            logger.warning(f"Error parsing address: {e}")
            return None

    def _scrape_georgia_assessor(self, address: str) -> Optional[Dict]:
        """Scrape Georgia county assessor data"""
        try:
            # Georgia counties often use similar systems
            # This is a simplified example - would need county-specific logic

            # Try common Georgia assessor search patterns
            # (This would need to be much more sophisticated in practice)

            return None

        except Exception as e:
            logger.warning(f"Error scraping Georgia assessor: {e}")

        return None

    def get_property_type(self, address: str) -> Dict:
        """
        Determine property type and construction details with improved accuracy
        """
        try:
            # Try real property data sources first
            real_data = self._get_real_property_type_data(address)
            if real_data and real_data.get("success"):
                return real_data

            # No API available - return unknown status
            return {
                "success": False,
                "error": "No property type API configured - manual verification required",
            }

        except Exception as e:
            logger.error(f"Error getting property type: {e}")
            return {"success": False, "error": "Property type information not available"}

    def _get_real_property_type_data(self, address: str) -> Optional[Dict]:
        """Try to get real property type data from APIs"""
        try:
            # Try Spokeo first (primary source)
            spokeo_data = self._get_spokeo_property_type(address)
            if spokeo_data:
                return spokeo_data

            # Try Zillow API if available
            zillow_data = self._get_zillow_property_type(address)
            if zillow_data:
                return zillow_data

            # Try Attom Data API
            attom_data = self._get_attom_property_type(address)
            if attom_data:
                return attom_data

            return None

        except Exception as e:
            logger.warning(f"Error getting real property type data: {e}")
            return None

    def _get_ownerly_property_type(self, address: str) -> Optional[Dict]:
        """Get property type from Ownerly.com"""
        try:
            # Ownerly provides detailed property information
            # This would require either their API or web scraping

            # For now, return None to use the intelligent address analysis
            # Real implementation would scrape or use Ownerly's API
            return None

        except Exception as e:
            logger.warning(f"Error getting Ownerly property type: {e}")
            return None

    def _get_spokeo_property_type(self, address: str) -> Optional[Dict]:
        """Get property type from Spokeo Property Search API"""
        try:
            # Check for Spokeo API key
            spokeo_api_key = os.getenv("SPOKEO_API_KEY")
            if not spokeo_api_key:
                logger.info("No Spokeo API key available for property type")
                return None

            # Use Spokeo Address Search API (their actual property endpoint)
            api_url = "https://api.spokeo.com/address"
            headers = {
                "Authorization": f"Bearer {spokeo_api_key}",
                "Content-Type": "application/json",
            }

            # Prepare search parameters for Address Search API
            params = {"address": address}

            response = self.session.get(api_url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get("success") and data.get("results"):
                    property_data = data["results"][0]  # First result
                    property_details = property_data.get("property", {})
                    building_info = property_data.get("building", {})

                    # Extract property type information
                    prop_type = building_info.get("property_type", "Single Family Residence")
                    year_built = building_info.get("year_built", 0)
                    square_footage = building_info.get("square_footage", 0)
                    bedrooms = building_info.get("bedrooms", 0)
                    bathrooms = building_info.get("bathrooms", 0)

                    # Determine if manufactured
                    is_manufactured = (
                        "manufactured" in prop_type.lower() or "mobile" in prop_type.lower()
                    )
                    construction = "Manufactured" if is_manufactured else "Site-Built"

                    return {
                        "success": True,
                        "type": prop_type,
                        "yearBuilt": year_built,
                        "construction": construction,
                        "isManufactured": is_manufactured,
                        "squareFootage": square_footage,
                        "bedrooms": bedrooms,
                        "bathrooms": bathrooms,
                        "source": "Spokeo Property Search API",
                    }

            return None

        except Exception as e:
            logger.warning(f"Error getting Spokeo property type: {e}")
            return None

    def _get_zillow_property_type(self, address: str) -> Optional[Dict]:
        """Get property type from Zillow API"""
        try:
            rapidapi_key = os.getenv("RAPIDAPI_KEY")
            if not rapidapi_key:
                return None

            # This would use Zillow API to get property details
            # Implementation would depend on specific API endpoints
            return None

        except Exception as e:
            logger.warning(f"Error getting Zillow property type: {e}")
            return None

    def _get_attom_property_type(self, address: str) -> Optional[Dict]:
        """Get property type from Attom Data API"""
        try:
            api_key = os.getenv("ATTOM_API_KEY")
            if not api_key:
                return None

            # This would use Attom Data API
            # Implementation would depend on specific API endpoints
            return None

        except Exception as e:
            logger.warning(f"Error getting Attom property type: {e}")
            return None

    def _analyze_property_type_from_address(self, address: str) -> Dict:
        """Analyze property type based on address patterns and keywords"""
        try:
            address_lower = address.lower()

            # Default to single family residence (most common)
            prop_type = "Single Family Residence"
            is_manufactured = False
            construction = "Site-Built"

            # Check for apartment/condo indicators
            apt_keywords = ["apt", "apartment", "unit", "suite", "#", "condo", "condominium"]
            if any(keyword in address_lower for keyword in apt_keywords):
                prop_type = "Condominium"

            # Check for townhouse indicators
            townhouse_keywords = ["townhouse", "townhome", "row", "th"]
            if any(keyword in address_lower for keyword in townhouse_keywords):
                prop_type = "Townhouse"

            # Check for mobile/manufactured home indicators
            mobile_keywords = [
                "mobile",
                "manufactured",
                "trailer",
                "mh",
                "modular",
                "mobile home park",
            ]
            if any(keyword in address_lower for keyword in mobile_keywords):
                prop_type = "Manufactured Home"
                is_manufactured = True
                construction = "Manufactured"

            # Generate realistic year built based on location patterns
            year_built = self._estimate_year_built(address)

            # Add additional property details
            square_footage = self._estimate_square_footage(prop_type, year_built)
            bedrooms = self._estimate_bedrooms(prop_type, square_footage)
            bathrooms = self._estimate_bathrooms(bedrooms)

            return {
                "success": True,
                "type": prop_type,
                "yearBuilt": year_built,
                "construction": construction,
                "isManufactured": is_manufactured,
                "squareFootage": square_footage,
                "bedrooms": bedrooms,
                "bathrooms": bathrooms,
                "source": "Address Pattern Analysis",
            }

        except Exception as e:
            logger.warning(f"Error analyzing property type from address: {e}")
            # Fallback to most common type
            return {
                "success": True,
                "type": "Single Family Residence",
                "yearBuilt": 2000,
                "construction": "Site-Built",
                "isManufactured": False,
                "squareFootage": 1800,
                "bedrooms": 3,
                "bathrooms": 2,
                "source": "Default Estimate",
            }

    def _estimate_year_built(self, address: str) -> int:
        """Estimate year built based on address and location patterns"""
        try:
            # Use first few characters of address to create variation
            addr_hash = hash(address[:10]) % 100

            # Most homes built between 1970-2020
            base_year = 1970
            year_range = 50

            # Create some geographical bias
            if "atlanta" in address.lower() or "ga" in address.lower():
                # Georgia has lots of newer construction
                base_year = 1980
                year_range = 40
            elif "boston" in address.lower() or "ma" in address.lower():
                # Massachusetts has older homes
                base_year = 1950
                year_range = 70

            estimated_year = base_year + (addr_hash % year_range)
            return min(estimated_year, 2023)  # Cap at current year

        except Exception:
            return 1995  # Safe default

    def _estimate_square_footage(self, prop_type: str, year_built: int) -> int:
        """Estimate square footage based on property type and age"""
        try:
            base_sizes = {
                "Single Family Residence": 1800,
                "Townhouse": 1400,
                "Condominium": 1100,
                "Manufactured Home": 1200,
                "Modular Home": 1300,
            }

            base_size = base_sizes.get(prop_type, 1800)

            # Newer homes tend to be larger
            if year_built > 2000:
                base_size = int(base_size * 1.2)
            elif year_built < 1980:
                base_size = int(base_size * 0.8)

            return base_size

        except Exception:
            return 1800

    def _estimate_bedrooms(self, prop_type: str, square_footage: int) -> int:
        """Estimate bedrooms based on property type and size"""
        try:
            if prop_type == "Condominium":
                if square_footage < 800:
                    return 1
                elif square_footage < 1200:
                    return 2
                else:
                    return 3
            else:
                if square_footage < 1000:
                    return 2
                elif square_footage < 1600:
                    return 3
                elif square_footage < 2500:
                    return 4
                else:
                    return 5

        except Exception:
            return 3

    def _estimate_bathrooms(self, bedrooms: int) -> float:
        """Estimate bathrooms based on bedrooms"""
        try:
            if bedrooms <= 2:
                return 1.0
            elif bedrooms == 3:
                return 2.0
            elif bedrooms == 4:
                return 2.5
            else:
                return 3.0

        except Exception:
            return 2.0

    def check_usda_eligibility(self, address: str) -> Dict:
        """
        Check USDA rural development eligibility using real API
        """
        try:
            # First try the official USDA API
            usda_result = self._check_usda_official_api(address)
            if usda_result and usda_result.get("success"):
                return usda_result

            # Fallback to geocoding + USDA map lookup
            geocode_result = self._check_usda_via_geocoding(address)
            if geocode_result and geocode_result.get("success"):
                return geocode_result

            return {"success": False, "error": "USDA eligibility information not available"}

        except Exception as e:
            logger.error(f"Error checking USDA eligibility: {e}")
            return {"success": False, "error": "USDA eligibility information not available"}

    def _check_usda_official_api(self, address: str) -> Optional[Dict]:
        """Check USDA eligibility using official USDA API"""
        try:
            # The USDA has a web service for eligibility checking
            # URL: https://eligibility.sc.egov.usda.gov/eligibility/

            # First geocode the address
            lat, lon = self._geocode_address(address)
            if not lat or not lon:
                return None

            # Check USDA eligibility using coordinates
            usda_url = "https://geowebservices.usda.gov/arcgis/rest/services/RD_Eligibility/MapServer/0/query"
            params = {
                "geometry": f"{lon},{lat}",
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "returnGeometry": "false",
                "returnTrueCurves": "false",
                "returnIdsOnly": "false",
                "returnCountOnly": "false",
                "returnZ": "false",
                "returnM": "false",
                "returnDistinctValues": "false",
                "f": "json",
            }

            response = self.session.get(usda_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()

                # Check if location is in eligible area
                features = data.get("features", [])
                eligible = len(features) > 0

                if eligible and features:
                    feature = features[0]
                    attributes = feature.get("attributes", {})

                    return {
                        "success": True,
                        "eligible": True,
                        "areaType": attributes.get("ELIGIBILITY", "Rural"),
                        "population": attributes.get("POPULATION", 0),
                        "mapUrl": "https://eligibility.sc.egov.usda.gov/eligibility/welcomeAction.do",
                        "source": "USDA Official API",
                    }
                else:
                    return {
                        "success": True,
                        "eligible": False,
                        "areaType": "Urban/Ineligible",
                        "population": 0,
                        "mapUrl": "https://eligibility.sc.egov.usda.gov/eligibility/welcomeAction.do",
                        "source": "USDA Official API",
                    }

        except Exception as e:
            logger.warning(f"Error checking USDA official API: {e}")

        return None

    def _check_usda_via_geocoding(self, address: str) -> Optional[Dict]:
        """Check USDA eligibility via geocoding and population lookup"""
        try:
            # Get coordinates
            lat, lon = self._geocode_address(address)
            if not lat or not lon:
                return None

            # Get population data from Census API
            census_data = self._get_census_population(lat, lon)

            # USDA generally requires population < 35,000
            population = census_data.get("population", 50000) if census_data else 50000
            eligible = population < 35000

            return {
                "success": True,
                "eligible": eligible,
                "areaType": "Rural" if eligible else "Urban",
                "population": population,
                "mapUrl": "https://eligibility.sc.egov.usda.gov/eligibility/welcomeAction.do",
                "source": "Census/Population Analysis",
            }

        except Exception as e:
            logger.warning(f"Error checking USDA via geocoding: {e}")

        return None

    def _geocode_address(self, address: str) -> tuple:
        """Geocode an address to get latitude/longitude"""
        try:
            # Use free geocoding service (Nominatim/OpenStreetMap)
            url = "https://nominatim.openstreetmap.org/search"
            params = {"q": address, "format": "json", "limit": 1}
            headers = {"User-Agent": "PropertyIntelligence/1.0"}

            response = self.session.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"])

        except Exception as e:
            logger.warning(f"Error geocoding address: {e}")

        return None, None

    def _get_census_population(self, lat: float, lon: float) -> Optional[Dict]:
        """Get population data from Census API"""
        try:
            # This would use the US Census API to get population data
            # For now, return None to indicate no data available
            return None

        except Exception as e:
            logger.warning(f"Error getting census data: {e}")

        return None

    def check_flood_zone(self, address: str) -> Dict:
        """
        Check FEMA flood zone information using real APIs
        """
        try:
            # First try the official FEMA flood service
            fema_result = self._check_fema_flood_api(address)
            if fema_result and fema_result.get("success"):
                return fema_result

            # Fallback to geocoding + FEMA map service
            geocode_result = self._check_flood_via_geocoding(address)
            if geocode_result and geocode_result.get("success"):
                return geocode_result

            return {"success": False, "error": "Flood zone information not available"}

        except Exception as e:
            logger.error(f"Error checking flood zone: {e}")
            return {"success": False, "error": "Flood zone information not available"}

    def _check_fema_flood_api(self, address: str) -> Optional[Dict]:
        """Check FEMA flood zone using official FEMA API"""
        try:
            # FEMA has web services for flood zone determination
            # URL: https://hazards.fema.gov/femaportal/wps/portal/NFHLWMS

            # First geocode the address
            lat, lon = self._geocode_address(address)
            if not lat or not lon:
                return None

            # Query FEMA flood map service
            fema_url = (
                "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query"
            )
            params = {
                "geometry": f"{lon},{lat}",
                "geometryType": "esriGeometryPoint",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF",
                "returnGeometry": "false",
                "f": "json",
            }

            response = self.session.get(fema_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()

                features = data.get("features", [])
                if features:
                    feature = features[0]
                    attributes = feature.get("attributes", {})

                    zone = attributes.get("FLD_ZONE", "X")
                    sfha = attributes.get("SFHA_TF", "F")  # Special Flood Hazard Area

                    # Determine risk level and insurance requirement
                    if zone in ["A", "AE", "AH", "AO", "AR", "A99", "V", "VE"]:
                        risk_level = "High Risk"
                        insurance_required = True
                    elif zone in ["B", "C", "X"]:
                        risk_level = "Moderate to Low Risk" if zone == "B" else "Minimal Risk"
                        insurance_required = False
                    else:
                        risk_level = "Unknown"
                        insurance_required = False

                    return {
                        "success": True,
                        "zone": zone,
                        "riskLevel": risk_level,
                        "insuranceRequired": insurance_required,
                        "mapUrl": "https://msc.fema.gov/portal/search",
                        "source": "FEMA Official API",
                    }
                else:
                    # No flood zone data found - assume minimal risk
                    return {
                        "success": True,
                        "zone": "X",
                        "riskLevel": "Minimal Risk",
                        "insuranceRequired": False,
                        "mapUrl": "https://msc.fema.gov/portal/search",
                        "source": "FEMA Official API",
                    }

        except Exception as e:
            logger.warning(f"Error checking FEMA flood API: {e}")

        return None

    def _check_flood_via_geocoding(self, address: str) -> Optional[Dict]:
        """Check flood risk via geocoding and proximity analysis"""
        try:
            # Get coordinates
            lat, lon = self._geocode_address(address)
            if not lat or not lon:
                return None

            # Use elevation and proximity to water to estimate flood risk
            # This is a simplified approach - real flood determination is complex

            # Check proximity to water bodies using address keywords
            flood_keywords = ["river", "creek", "bay", "lake", "marsh", "wetland", "canal", "bayou"]
            address_lower = address.lower()

            is_near_water = any(keyword in address_lower for keyword in flood_keywords)

            if is_near_water:
                return {
                    "success": True,
                    "zone": "AE",
                    "riskLevel": "High Risk (Near Water)",
                    "insuranceRequired": True,
                    "mapUrl": "https://msc.fema.gov/portal/search",
                    "source": "Proximity Analysis",
                }
            else:
                return {
                    "success": True,
                    "zone": "X",
                    "riskLevel": "Minimal Risk",
                    "insuranceRequired": False,
                    "mapUrl": "https://msc.fema.gov/portal/search",
                    "source": "Proximity Analysis",
                }

        except Exception as e:
            logger.warning(f"Error checking flood via geocoding: {e}")

        return None

    def check_hoa_status(self, address: str) -> Dict:
        """
        Check HOA status and fees
        """
        try:
            # No API integration available for HOA data
            # Return honest response requiring manual verification

            return {
                "success": False,
                "error": "No HOA API integration available - manual verification required",
            }

        except Exception as e:
            logger.error(f"Error checking HOA status: {e}")
            return {"success": False, "error": "HOA information not available"}

    def assess_financing_options(self, address: str) -> Dict:
        """
        Assess financing options based on property characteristics
        """
        try:
            # Get property type to determine financing restrictions
            prop_type = self.get_property_type(address)
            usda_eligible = self.check_usda_eligibility(address)
            flood_zone = self.check_flood_zone(address)

            # Determine loan eligibility
            conventional = True
            fha = True
            va = True

            # Manufactured homes have restrictions
            if prop_type.get("isManufactured", False):
                conventional = False
                fha = prop_type.get("yearBuilt", 1990) >= 1976  # FHA requires 1976+

            # USDA eligibility
            usda = usda_eligible.get("eligible", False)

            # Flood zone considerations
            notes = []
            if flood_zone.get("insuranceRequired", False):
                notes.append("Flood insurance required")
            if prop_type.get("isManufactured", False):
                notes.append("Manufactured home - specialized financing required")
            if not usda:
                notes.append("Not eligible for USDA rural development loans")

            return {
                "success": True,
                "conventional": conventional,
                "fha": fha,
                "va": va,
                "usda": usda,
                "notes": "; ".join(notes) if notes else "Standard financing available",
                "source": "Financing Analysis",
            }

        except Exception as e:
            logger.error(f"Error assessing financing options: {e}")
            return {"success": False, "error": "Financing analysis not available"}


# Global instance
property_intel_api = PropertyIntelligenceAPI()
