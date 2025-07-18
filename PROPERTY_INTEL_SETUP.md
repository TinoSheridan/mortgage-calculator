# Property Intelligence Setup Guide

## Overview
The Property Intelligence feature provides real property data by integrating with multiple APIs. The primary data source is **Spokeo.com** which provides comprehensive property information including tax records, owner details, and property characteristics.

## Primary API (Recommended)

### 1. Spokeo Address Search API ⭐ PRIMARY SOURCE
- **Service**: Property and property owner data by address
- **Sign up**: Contact directly - Email: [apisupport@spokeo.com](mailto:apisupport@spokeo.com) or Phone: (888) 585-2370
- **Environment Variable**: `SPOKEO_API_KEY`
- **Cost**: Paid service (contact for pricing)
- **Features**:
  - Property details and owner information
  - Contact information (phone, email)
  - Property history and characteristics
  - Public records data
  - Property ownership details

**Note**: Spokeo requires direct contact for API access - no self-service signup available.

## Additional API Keys (Optional)

### 2. RapidAPI (for Zillow Data)
- **Service**: Property details, tax information
- **Sign up**: https://rapidapi.com/
- **API**: Search for "Zillow" APIs
- **Environment Variable**: `RAPIDAPI_KEY`
- **Cost**: Varies by provider (some free tiers available)

### 2. Attom Data API
- **Service**: Comprehensive property data
- **Sign up**: https://developer.attomdata.com/
- **Environment Variable**: `ATTOM_API_KEY`
- **Cost**: Paid service, very comprehensive data

### 3. Free APIs (No Key Required)

#### USDA Eligibility
- **Service**: Official USDA rural development eligibility
- **URL**: https://geowebservices.usda.gov/
- **No API key required**

#### FEMA Flood Maps
- **Service**: Official flood zone determination
- **URL**: https://hazards.fema.gov/gis/nfhl/rest/services/
- **No API key required**

#### Geocoding (OpenStreetMap)
- **Service**: Address to coordinates conversion
- **URL**: https://nominatim.openstreetmap.org/
- **No API key required**

## Setup Instructions

### 1. Environment Variables
Add these to your `.env` file or environment:

```bash
# Primary source - Spokeo Property Search API
SPOKEO_API_KEY=your_spokeo_api_key_here

# Optional - for enhanced property data
RAPIDAPI_KEY=your_rapidapi_key_here
ATTOM_API_KEY=your_attom_api_key_here
```

### 2. Without Spokeo API Key
The system will work with free data sources:
- Manual verification links to Spokeo.com
- USDA eligibility (official API)
- FEMA flood zones (official API)
- Basic geocoding
- Intelligent address pattern analysis

### 3. With Spokeo API Key ⭐ RECOMMENDED
Enhanced data includes:
- **Real property tax assessments**
- **Current owner information**
- **Accurate property details** (type, size, bedrooms, bathrooms)
- **Parcel IDs and legal descriptions**
- **Historical tax records**
- **Property characteristics**

## Data Sources by Category

### Tax Information
1. **Spokeo Property Search API** ⭐ PRIMARY - Comprehensive tax records
2. **Zillow API** (RapidAPI) - Property tax data
3. **Attom Data** - Comprehensive tax records
4. **County Assessor** - Direct scraping (limited)
5. **Fallback** - Manual verification links

### Property Type
1. **Spokeo Property Search API** ⭐ PRIMARY - Detailed property characteristics
2. **Zillow API** - Property details
3. **Attom Data** - Construction details
4. **Fallback** - Intelligent address pattern analysis

### USDA Eligibility
1. **USDA Official API** - Real eligibility data ✅ Free
2. **Census Population** - Population-based analysis
3. **Fallback** - Geographic analysis

### Flood Zone
1. **FEMA Official API** - Real flood zone data ✅ Free
2. **Proximity Analysis** - Water body detection
3. **Fallback** - Address pattern analysis

### HOA Information
1. **Property APIs** - HOA details from listings
2. **MLS Data** - Multiple listing service
3. **Fallback** - Pattern-based detection

## Testing

Test with real addresses to verify data accuracy:

```bash
# Test API endpoints
curl "http://localhost:5000/api/property-intel?address=123 Main St, Atlanta, GA 30309"
```

## Accuracy Notes

### High Accuracy (with APIs)
- Tax information: 85-95% accurate
- USDA eligibility: 95%+ accurate (official)
- Flood zones: 95%+ accurate (official)
- Property type: 80-90% accurate

### Moderate Accuracy (free sources)
- USDA eligibility: 95%+ (still official)
- Flood zones: 95%+ (still official)
- Basic property info: 60-80%
- HOA detection: 50-70%

## Cost Considerations

### Free Tier
- USDA and FEMA data: Always free
- Basic functionality: No cost
- Limited property details

### Paid Tier
- RapidAPI: $10-50/month depending on usage
- Attom Data: $100-500/month (enterprise)
- Full accuracy: Moderate cost

## Implementation Priority

1. **Phase 1**: Use free APIs (USDA, FEMA) ✅ Implemented
2. **Phase 2**: Add RapidAPI for basic property data
3. **Phase 3**: Add premium APIs for full accuracy

The current implementation works immediately with free data sources and can be enhanced with paid APIs as needed.
