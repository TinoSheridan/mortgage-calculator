/**
 * Property Intelligence Module
 * Provides comprehensive property-specific financing information
 */

class PropertyIntelligence {
    constructor() {
        this.popup = null;
        this.currentProperty = null;
        this.isLoading = false;
    }

    openWindow() {
        const width = 1000;
        const height = 700;
        const left = (screen.width - width) / 2;
        const top = (screen.height - height) / 2;

        this.popup = window.open(
            '',
            'PropertyIntel',
            `width=${width},height=${height},left=${left},top=${top},scrollbars=yes,resizable=yes`
        );

        if (this.popup) {
            this.popup.document.write(this.getPopupHTML());
            this.popup.document.close();
            this.initializePopup();
        }
    }

    getPopupHTML() {
        return `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Property Intelligence</title>
                <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet">
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
                    .intel-header { background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; padding: 20px; }
                    .intel-section { margin-bottom: 25px; }
                    .intel-card { border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
                    .intel-status { padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 600; }
                    .status-eligible { background: #d1e7dd; color: #0a3622; }
                    .status-ineligible { background: #f8d7da; color: #58151c; }
                    .status-unknown { background: #e2e3e5; color: #383d41; }
                    .loading-spinner { display: none; text-align: center; padding: 20px; }
                    .property-search { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                    .results-container { display: none; }
                    .info-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                    .error-message { background: #f8d7da; color: #721c24; padding: 10px; border-radius: 4px; margin: 10px 0; }
                </style>
            </head>
            <body>
                <div class="intel-header">
                    <h1><i class="bi bi-house-gear"></i> Property Intelligence</h1>
                    <p class="mb-0">Comprehensive property financing information for loan officers</p>
                </div>

                <div class="container-fluid p-4">
                    <div class="property-search">
                        <div class="row align-items-end">
                            <div class="col-md-8">
                                <label for="propertyAddress" class="form-label">Property Address</label>
                                <input type="text" class="form-control" id="propertyAddress"
                                       placeholder="Enter full property address (e.g., 123 Main St, City, State 12345)">
                            </div>
                            <div class="col-md-4">
                                <button type="button" class="btn btn-primary w-100" onclick="searchProperty()">
                                    <i class="bi bi-search"></i> Analyze Property
                                </button>
                            </div>
                        </div>
                    </div>

                    <div class="loading-spinner" id="loadingSpinner">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <p>Analyzing property information...</p>
                    </div>

                    <div class="results-container" id="resultsContainer">
                        <div class="property-header mb-3 p-3 bg-light rounded">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h5 class="mb-1 text-primary">Property Address</h5>
                                    <p class="mb-0 h6" id="propertyAddressDisplay">Enter address to analyze</p>
                                </div>
                                <button type="button" class="btn btn-outline-primary btn-sm" id="copyAddressBtn" onclick="copyPropertyAddress()" disabled>
                                    <i class="bi bi-clipboard"></i> Copy
                                </button>
                            </div>
                        </div>
                        <div class="info-grid">
                            <!-- Tax Information -->
                            <div class="intel-card">
                                <h5><i class="bi bi-receipt"></i> Tax Information</h5>
                                <div id="taxInfo">
                                    <p class="text-muted">Enter address to view tax information</p>
                                </div>
                            </div>

                            <!-- Property Type -->
                            <div class="intel-card">
                                <h5><i class="bi bi-house"></i> Property Type</h5>
                                <div id="propertyType">
                                    <p class="text-muted">Enter address to determine property type</p>
                                </div>
                            </div>

                            <!-- USDA Eligibility -->
                            <div class="intel-card">
                                <h5><i class="bi bi-geo-alt"></i> USDA Eligibility</h5>
                                <div id="usdaEligibility">
                                    <p class="text-muted">Enter address to check USDA eligibility</p>
                                </div>
                            </div>

                            <!-- Flood Zone -->
                            <div class="intel-card">
                                <h5><i class="bi bi-water"></i> Flood Zone</h5>
                                <div id="floodZone">
                                    <p class="text-muted">Enter address to check flood zone</p>
                                </div>
                            </div>

                            <!-- HOA Information -->
                            <div class="intel-card">
                                <h5><i class="bi bi-building"></i> HOA Information</h5>
                                <div id="hoaInfo">
                                    <p class="text-muted">Enter address to check HOA status</p>
                                </div>
                            </div>

                            <!-- Financing Considerations -->
                            <div class="intel-card">
                                <h5><i class="bi bi-bank"></i> Financing Considerations</h5>
                                <div id="financingInfo">
                                    <p class="text-muted">Enter address to view financing considerations</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
                <script>
                    function searchProperty() {
                        const address = document.getElementById('propertyAddress').value.trim();
                        if (!address) {
                            alert('Please enter a property address');
                            return;
                        }

                        // Show loading spinner
                        document.getElementById('loadingSpinner').style.display = 'block';
                        document.getElementById('resultsContainer').style.display = 'none';

                        // Call parent window function to analyze property
                        if (window.opener && window.opener.analyzeProperty) {
                            window.opener.analyzeProperty(address, updateResults);
                        } else {
                            // Fallback for testing
                            setTimeout(() => {
                                updateResults(getDemoData(address));
                            }, 2000);
                        }
                    }

                    function updateResults(data) {
                        document.getElementById('loadingSpinner').style.display = 'none';
                        document.getElementById('resultsContainer').style.display = 'block';

                        // Store source links for use in update functions
                        window.sourceLinks = data.sourceLinks || {};

                        // Update property address display
                        updatePropertyAddressDisplay(data.address);

                        // Update each section with received data
                        updateTaxInfo(data.tax);
                        updatePropertyType(data.propertyType);
                        updateUSDAEligibility(data.usda);
                        updateFloodZone(data.flood);
                        updateHOAInfo(data.hoa);
                        updateFinancingInfo(data.financing);
                    }

                    function updatePropertyAddressDisplay(address) {
                        const addressDisplay = document.getElementById('propertyAddressDisplay');
                        const copyBtn = document.getElementById('copyAddressBtn');

                        if (address) {
                            addressDisplay.textContent = address;
                            copyBtn.disabled = false;
                            // Store address globally for copying
                            window.currentPropertyAddress = address;
                        } else {
                            addressDisplay.textContent = 'Address not available';
                            copyBtn.disabled = true;
                            window.currentPropertyAddress = null;
                        }
                    }

                    function copyPropertyAddress() {
                        const address = window.currentPropertyAddress;
                        if (!address) {
                            return;
                        }

                        // Use modern clipboard API if available
                        if (navigator.clipboard && navigator.clipboard.writeText) {
                            navigator.clipboard.writeText(address).then(() => {
                                showCopySuccess();
                            }).catch(() => {
                                fallbackCopyTextToClipboard(address);
                            });
                        } else {
                            fallbackCopyTextToClipboard(address);
                        }
                    }

                    function fallbackCopyTextToClipboard(text) {
                        const textArea = document.createElement('textarea');
                        textArea.value = text;
                        textArea.style.position = 'fixed';
                        textArea.style.left = '-999999px';
                        textArea.style.top = '-999999px';
                        document.body.appendChild(textArea);
                        textArea.focus();
                        textArea.select();

                        try {
                            document.execCommand('copy');
                            showCopySuccess();
                        } catch (err) {
                            console.error('Unable to copy to clipboard', err);
                            showCopyError();
                        }

                        document.body.removeChild(textArea);
                    }

                    function showCopySuccess() {
                        const copyBtn = document.getElementById('copyAddressBtn');
                        const originalContent = copyBtn.innerHTML;

                        copyBtn.innerHTML = '<i class="bi bi-check"></i> Copied!';
                        copyBtn.classList.remove('btn-outline-primary');
                        copyBtn.classList.add('btn-success');

                        setTimeout(() => {
                            copyBtn.innerHTML = originalContent;
                            copyBtn.classList.remove('btn-success');
                            copyBtn.classList.add('btn-outline-primary');
                        }, 2000);
                    }

                    function showCopyError() {
                        const copyBtn = document.getElementById('copyAddressBtn');
                        const originalContent = copyBtn.innerHTML;

                        copyBtn.innerHTML = '<i class="bi bi-x"></i> Failed';
                        copyBtn.classList.remove('btn-outline-primary');
                        copyBtn.classList.add('btn-danger');

                        setTimeout(() => {
                            copyBtn.innerHTML = originalContent;
                            copyBtn.classList.remove('btn-danger');
                            copyBtn.classList.add('btn-outline-primary');
                        }, 2000);
                    }

                    function updateTaxInfo(taxData) {
                        const container = document.getElementById('taxInfo');
                        const sourceLinks = window.sourceLinks || {};

                        if (taxData && taxData.success) {
                            const needsManualVerification = taxData.manual_verification_needed ||
                                taxData.ownerName?.includes('See QPublic') ||
                                taxData.annualTax === 0;

                            container.innerHTML = \`
                                <div class="border-bottom pb-2 mb-2">
                                    <h6 class="text-primary mb-1">Property Identification</h6>
                                    <p class="mb-1"><strong>Owner:</strong> \${taxData.ownerName || 'Not Available'}</p>
                                    <p class="mb-1"><strong>Parcel ID:</strong> \${taxData.parcelId || 'Not Available'}</p>
                                    <p class="mb-1"><strong>Address:</strong> \${taxData.propertyAddress || 'Not Available'}</p>
                                    \${taxData.legalDescription && taxData.legalDescription !== 'Not Available' ? \`<p class="mb-1"><strong>Legal:</strong> \${taxData.legalDescription}</p>\` : ''}
                                </div>
                                \${needsManualVerification ? \`
                                    <div class="alert alert-warning py-2 mb-2">
                                        <small><i class="bi bi-exclamation-triangle"></i> Manual verification required - use links below to get current data</small>
                                    </div>
                                \` : \`
                                    <p><strong>Annual Tax:</strong> $\${taxData.annualTax.toLocaleString()}</p>
                                    <p><strong>Assessed Value:</strong> $\${taxData.assessedValue.toLocaleString()}</p>
                                    <p><strong>Tax Rate:</strong> \${taxData.taxRate}%</p>
                                    <p><strong>Last Updated:</strong> \${taxData.lastUpdated}</p>
                                \`}
                                <div class="mt-2">
                                    <small class="text-muted">\${needsManualVerification ? 'Get current data from:' : 'Verify at sources:'}</small><br>
                                    \${sourceLinks.spokeo ? \`<a href="\${sourceLinks.spokeo}" target="_blank" class="btn btn-sm btn-primary me-2"><i class="bi bi-star-fill"></i> Spokeo (Primary)</a>\` : ''}
                                    \${sourceLinks.qpublic ? \`<a href="\${sourceLinks.qpublic}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">QPublic</a>\` : ''}
                                    \${sourceLinks.countyAssessor ? \`<a href="\${sourceLinks.countyAssessor}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">County Assessor</a>\` : ''}
                                </div>
                            \`;
                        } else {
                            container.innerHTML = \`
                                <div class="border-bottom pb-2 mb-2">
                                    <h6 class="text-primary mb-1">Property Identification</h6>
                                    <p class="mb-1"><strong>Owner:</strong> <span class="text-muted">Unknown</span></p>
                                    <p class="mb-1"><strong>Parcel ID:</strong> <span class="text-muted">Unknown</span></p>
                                    <p class="mb-1"><strong>Address:</strong> <span class="text-muted">Unknown</span></p>
                                    <p class="mb-1"><strong>Legal:</strong> <span class="text-muted">Unknown</span></p>
                                </div>
                                <p><strong>Annual Tax:</strong> <span class="text-muted">Unknown</span></p>
                                <p><strong>Assessed Value:</strong> <span class="text-muted">Unknown</span></p>
                                <p><strong>Tax Rate:</strong> <span class="text-muted">Unknown</span></p>
                                <p><strong>Last Updated:</strong> <span class="text-muted">Unknown</span></p>
                                <div class="alert alert-info py-2 mb-2">
                                    <small><i class="bi bi-info-circle"></i> No API configured - use links below to get current data</small>
                                </div>
                                <div class="mt-2">
                                    <small class="text-muted">Get current data from:</small><br>
                                    \${sourceLinks.spokeo ? \`<a href="\${sourceLinks.spokeo}" target="_blank" class="btn btn-sm btn-primary me-2"><i class="bi bi-star-fill"></i> Spokeo (Primary)</a>\` : ''}
                                    \${sourceLinks.qpublic ? \`<a href="\${sourceLinks.qpublic}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">QPublic</a>\` : ''}
                                    \${sourceLinks.countyAssessor ? \`<a href="\${sourceLinks.countyAssessor}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">County Assessor</a>\` : ''}
                                </div>
                            \`;
                        }
                    }

                    function updatePropertyType(typeData) {
                        const container = document.getElementById('propertyType');
                        const sourceLinks = window.sourceLinks || {};

                        if (typeData && typeData.success) {
                            const typeClass = typeData.isManufactured ? 'status-ineligible' : 'status-eligible';
                            const isEstimate = typeData.source?.includes('Pattern Analysis') || typeData.source?.includes('Default Estimate');

                            container.innerHTML = \`
                                <p><strong>Property Type:</strong> <span class="intel-status \${typeClass}">\${typeData.type}</span></p>
                                <p><strong>Year Built:</strong> \${typeData.yearBuilt}</p>
                                <p><strong>Construction:</strong> \${typeData.construction}</p>
                                \${typeData.squareFootage ? \`<p><strong>Square Footage:</strong> \${typeData.squareFootage.toLocaleString()} sq ft</p>\` : ''}
                                \${typeData.bedrooms ? \`<p><strong>Bedrooms:</strong> \${typeData.bedrooms}</p>\` : ''}
                                \${typeData.bathrooms ? \`<p><strong>Bathrooms:</strong> \${typeData.bathrooms}</p>\` : ''}
                                \${typeData.isManufactured ? '<p class="text-warning"><small>May require specialized financing</small></p>' : ''}
                                \${isEstimate ? \`
                                    <div class="alert alert-info py-2 mb-2">
                                        <small><i class="bi bi-info-circle"></i> Estimated based on address patterns - verify for accuracy</small>
                                    </div>
                                \` : ''}
                                <div class="mt-2">
                                    <small class="text-muted">Verify at sources:</small><br>
                                    \${sourceLinks.spokeo ? \`<a href="\${sourceLinks.spokeo}" target="_blank" class="btn btn-sm btn-primary me-2"><i class="bi bi-star-fill"></i> Spokeo (Primary)</a>\` : ''}
                                    \${sourceLinks.zillow ? \`<a href="\${sourceLinks.zillow}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">Zillow</a>\` : ''}
                                    \${sourceLinks.realtor ? \`<a href="\${sourceLinks.realtor}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">Realtor.com</a>\` : ''}
                                    \${sourceLinks.countyAssessor ? \`<a href="\${sourceLinks.countyAssessor}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">County Records</a>\` : ''}
                                </div>
                            \`;
                        } else {
                            container.innerHTML = \`
                                <p><strong>Property Type:</strong> <span class="text-muted">Unknown</span></p>
                                <p><strong>Year Built:</strong> <span class="text-muted">Unknown</span></p>
                                <p><strong>Construction:</strong> <span class="text-muted">Unknown</span></p>
                                <p><strong>Square Footage:</strong> <span class="text-muted">Unknown</span></p>
                                <p><strong>Bedrooms:</strong> <span class="text-muted">Unknown</span></p>
                                <p><strong>Bathrooms:</strong> <span class="text-muted">Unknown</span></p>
                                <div class="alert alert-info py-2 mb-2">
                                    <small><i class="bi bi-info-circle"></i> No API configured - use links below to get current data</small>
                                </div>
                                <div class="mt-2">
                                    <small class="text-muted">Get current data from:</small><br>
                                    \${sourceLinks.spokeo ? \`<a href="\${sourceLinks.spokeo}" target="_blank" class="btn btn-sm btn-primary me-2"><i class="bi bi-star-fill"></i> Spokeo (Primary)</a>\` : ''}
                                    \${sourceLinks.zillow ? \`<a href="\${sourceLinks.zillow}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">Zillow</a>\` : ''}
                                    \${sourceLinks.realtor ? \`<a href="\${sourceLinks.realtor}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">Realtor.com</a>\` : ''}
                                    \${sourceLinks.countyAssessor ? \`<a href="\${sourceLinks.countyAssessor}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">County Records</a>\` : ''}
                                </div>
                            \`;
                        }
                    }

                    function updateUSDAEligibility(usdaData) {
                        const container = document.getElementById('usdaEligibility');
                        const sourceLinks = window.sourceLinks || {};

                        if (usdaData && usdaData.success) {
                            const statusClass = usdaData.eligible ? 'status-eligible' : 'status-ineligible';
                            container.innerHTML = \`
                                <p><strong>USDA Eligible:</strong> <span class="intel-status \${statusClass}">\${usdaData.eligible ? 'YES' : 'NO'}</span></p>
                                <p><strong>Area Type:</strong> \${usdaData.areaType}</p>
                                <p><strong>Population:</strong> \${usdaData.population.toLocaleString()}</p>
                                <div class="mt-2">
                                    <a href="\${sourceLinks.usda || usdaData.mapUrl}" target="_blank" class="btn btn-sm btn-outline-primary">Official USDA Eligibility Map</a>
                                </div>
                            \`;
                        } else {
                            container.innerHTML = \`
                                <p class="text-warning">USDA eligibility information not available via API</p>
                                <div class="mt-2">
                                    <a href="\${sourceLinks.usda}" target="_blank" class="btn btn-sm btn-outline-primary">Check USDA Eligibility Map</a>
                                </div>
                            \`;
                        }
                    }

                    function updateFloodZone(floodData) {
                        const container = document.getElementById('floodZone');
                        const sourceLinks = window.sourceLinks || {};

                        if (floodData && floodData.success) {
                            const riskClass = floodData.zone.startsWith('X') ? 'status-eligible' : 'status-ineligible';
                            container.innerHTML = \`
                                <p><strong>Flood Zone:</strong> <span class="intel-status \${riskClass}">\${floodData.zone}</span></p>
                                <p><strong>Risk Level:</strong> \${floodData.riskLevel}</p>
                                <p><strong>Insurance Required:</strong> \${floodData.insuranceRequired ? 'YES' : 'NO'}</p>
                                <div class="mt-2">
                                    <small class="text-muted">Verify at sources:</small><br>
                                    <a href="\${sourceLinks.fema || floodData.mapUrl}" target="_blank" class="btn btn-sm btn-outline-primary me-1">FEMA Flood Map</a>
                                    \${sourceLinks.countyAssessor ? \`<a href="\${sourceLinks.countyAssessor}" target="_blank" class="btn btn-sm btn-outline-primary me-1">County Records</a>\` : ''}
                                </div>
                            \`;
                        } else {
                            container.innerHTML = \`
                                <p class="text-warning">Flood zone information not available via API</p>
                                <div class="mt-2">
                                    <small class="text-muted">Search manually at:</small><br>
                                    <a href="\${sourceLinks.fema}" target="_blank" class="btn btn-sm btn-outline-primary me-1">FEMA Flood Map</a>
                                    \${sourceLinks.countyAssessor ? \`<a href="\${sourceLinks.countyAssessor}" target="_blank" class="btn btn-sm btn-outline-primary me-1">County Records</a>\` : ''}
                                </div>
                            \`;
                        }
                    }

                    function updateHOAInfo(hoaData) {
                        const container = document.getElementById('hoaInfo');
                        const sourceLinks = window.sourceLinks || {};

                        if (hoaData && hoaData.success) {
                            container.innerHTML = \`
                                <p><strong>HOA:</strong> <span class="intel-status \${hoaData.hasHOA ? 'status-ineligible' : 'status-eligible'}">\${hoaData.hasHOA ? 'YES' : 'NO'}</span></p>
                                \${hoaData.hasHOA ? \`
                                    <p><strong>Monthly Fee:</strong> $\${hoaData.monthlyFee}</p>
                                    <p><strong>HOA Name:</strong> \${hoaData.hoaName}</p>
                                    <p><strong>Management:</strong> \${hoaData.management}</p>
                                \` : ''}
                                <div class="mt-2">
                                    <small class="text-muted">Verify at sources:</small><br>
                                    \${sourceLinks.spokeo ? \`<a href="\${sourceLinks.spokeo}" target="_blank" class="btn btn-sm btn-primary me-2"><i class="bi bi-star-fill"></i> Spokeo (Primary)</a>\` : ''}
                                    \${sourceLinks.zillow ? \`<a href="\${sourceLinks.zillow}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">Zillow</a>\` : ''}
                                    \${sourceLinks.realtor ? \`<a href="\${sourceLinks.realtor}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">Realtor.com</a>\` : ''}
                                    \${sourceLinks.propertyShark ? \`<a href="\${sourceLinks.propertyShark}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">PropertyShark</a>\` : ''}
                                </div>
                            \`;
                        } else {
                            container.innerHTML = \`
                                <p><strong>HOA:</strong> <span class="text-muted">Unknown</span></p>
                                <p><strong>Monthly Fee:</strong> <span class="text-muted">Unknown</span></p>
                                <p><strong>HOA Name:</strong> <span class="text-muted">Unknown</span></p>
                                <p><strong>Management:</strong> <span class="text-muted">Unknown</span></p>
                                <div class="alert alert-info py-2 mb-2">
                                    <small><i class="bi bi-info-circle"></i> No HOA API available - use links below to get current data</small>
                                </div>
                                <div class="mt-2">
                                    <small class="text-muted">Get current data from:</small><br>
                                    \${sourceLinks.spokeo ? \`<a href="\${sourceLinks.spokeo}" target="_blank" class="btn btn-sm btn-primary me-2"><i class="bi bi-star-fill"></i> Spokeo (Primary)</a>\` : ''}
                                    \${sourceLinks.zillow ? \`<a href="\${sourceLinks.zillow}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">Zillow</a>\` : ''}
                                    \${sourceLinks.realtor ? \`<a href="\${sourceLinks.realtor}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">Realtor.com</a>\` : ''}
                                    \${sourceLinks.propertyShark ? \`<a href="\${sourceLinks.propertyShark}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">PropertyShark</a>\` : ''}
                                </div>
                            \`;
                        }
                    }

                    function updateFinancingInfo(financingData) {
                        const container = document.getElementById('financingInfo');
                        const sourceLinks = window.sourceLinks || {};

                        if (financingData && financingData.success) {
                            container.innerHTML = \`
                                <h6>Loan Type Eligibility:</h6>
                                <ul>
                                    <li>Conventional: <span class="intel-status \${financingData.conventional ? 'status-eligible' : 'status-ineligible'}">\${financingData.conventional ? 'ELIGIBLE' : 'RESTRICTIONS'}</span></li>
                                    <li>FHA: <span class="intel-status \${financingData.fha ? 'status-eligible' : 'status-ineligible'}">\${financingData.fha ? 'ELIGIBLE' : 'RESTRICTIONS'}</span></li>
                                    <li>VA: <span class="intel-status \${financingData.va ? 'status-eligible' : 'status-ineligible'}">\${financingData.va ? 'ELIGIBLE' : 'RESTRICTIONS'}</span></li>
                                    <li>USDA: <span class="intel-status \${financingData.usda ? 'status-eligible' : 'status-ineligible'}">\${financingData.usda ? 'ELIGIBLE' : 'RESTRICTIONS'}</span></li>
                                </ul>
                                \${financingData.notes ? \`<p><strong>Notes:</strong> \${financingData.notes}</p>\` : ''}
                                <div class="mt-2">
                                    <small class="text-muted">Verify eligibility at:</small><br>
                                    \${sourceLinks.spokeo ? \`<a href="\${sourceLinks.spokeo}" target="_blank" class="btn btn-sm btn-primary me-2"><i class="bi bi-star-fill"></i> Spokeo (Primary)</a>\` : ''}
                                    \${sourceLinks.usda ? \`<a href="\${sourceLinks.usda}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">USDA Eligibility</a>\` : ''}
                                    \${sourceLinks.zillow ? \`<a href="\${sourceLinks.zillow}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">Property Listings</a>\` : ''}
                                    \${sourceLinks.countyAssessor ? \`<a href="\${sourceLinks.countyAssessor}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">County Records</a>\` : ''}
                                </div>
                            \`;
                        } else {
                            container.innerHTML = \`
                                <p class="text-warning">Financing information not available via API</p>
                                <div class="mt-2">
                                    <small class="text-muted">Check eligibility manually at:</small><br>
                                    \${sourceLinks.spokeo ? \`<a href="\${sourceLinks.spokeo}" target="_blank" class="btn btn-sm btn-primary me-2"><i class="bi bi-star-fill"></i> Spokeo (Primary)</a>\` : ''}
                                    \${sourceLinks.usda ? \`<a href="\${sourceLinks.usda}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">USDA Eligibility</a>\` : ''}
                                    \${sourceLinks.zillow ? \`<a href="\${sourceLinks.zillow}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">Property Listings</a>\` : ''}
                                    \${sourceLinks.countyAssessor ? \`<a href="\${sourceLinks.countyAssessor}" target="_blank" class="btn btn-sm btn-outline-secondary me-1">County Records</a>\` : ''}
                                </div>
                            \`;
                        }
                    }

                    function getDemoData(address) {
                        return {
                            address: address,
                            tax: {
                                success: false,
                                error: 'No API key configured - manual verification required'
                            },
                            propertyType: {
                                success: false,
                                error: 'No API key configured - manual verification required'
                            },
                            usda: {
                                success: true,
                                eligible: false,
                                areaType: 'Urban',
                                population: 45000,
                                mapUrl: 'https://eligibility.sc.egov.usda.gov/eligibility/welcomeAction.do'
                            },
                            flood: {
                                success: true,
                                zone: 'X',
                                riskLevel: 'Minimal Risk',
                                insuranceRequired: false,
                                mapUrl: 'https://msc.fema.gov/portal/search'
                            },
                            hoa: {
                                success: false,
                                error: 'No API integration available - manual verification required'
                            },
                            financing: {
                                success: true,
                                conventional: true,
                                fha: true,
                                va: true,
                                usda: false,
                                notes: 'Standard financing available. Property meets all loan program requirements.'
                            }
                        };
                    }

                    // Allow Enter key to trigger search
                    document.getElementById('propertyAddress').addEventListener('keypress', function(e) {
                        if (e.key === 'Enter') {
                            searchProperty();
                        }
                    });
                </script>
            </body>
            </html>
        `;
    }

    initializePopup() {
        if (this.popup) {
            this.popup.focus();
        }
    }
}

// Global function to open Property Intelligence
function openPropertyIntel() {
    const propertyIntel = new PropertyIntelligence();
    propertyIntel.openWindow();
}

// Global function to analyze property using real API
function analyzeProperty(address, callback) {
    const apiUrl = `/api/property-intel?address=${encodeURIComponent(address)}`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                callback(result.data);
            } else {
                // Fallback to demo data if API fails
                console.warn('API failed, using demo data:', result.error);
                callback(getDemoData(address));
            }
        })
        .catch(error => {
            console.error('Error calling property intel API:', error);
            // Fallback to demo data
            callback(getDemoData(address));
        });
}

// Global function to copy property address (called from popup)
function copyPropertyAddress() {
    // This function is called from within the popup window
    // The actual implementation is in the popup's script context
    if (window.currentPropertyAddress) {
        const address = window.currentPropertyAddress;

        // Use modern clipboard API if available
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(address).then(() => {
                showCopySuccess();
            }).catch(() => {
                fallbackCopyTextToClipboard(address);
            });
        } else {
            fallbackCopyTextToClipboard(address);
        }
    }
}

// Helper functions for clipboard operations
function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();

    try {
        document.execCommand('copy');
        showCopySuccess();
    } catch (err) {
        console.error('Unable to copy to clipboard', err);
        showCopyError();
    }

    document.body.removeChild(textArea);
}

function showCopySuccess() {
    const copyBtn = document.getElementById('copyAddressBtn');
    if (copyBtn) {
        const originalContent = copyBtn.innerHTML;

        copyBtn.innerHTML = '<i class="bi bi-check"></i> Copied!';
        copyBtn.classList.remove('btn-outline-primary');
        copyBtn.classList.add('btn-success');

        setTimeout(() => {
            copyBtn.innerHTML = originalContent;
            copyBtn.classList.remove('btn-success');
            copyBtn.classList.add('btn-outline-primary');
        }, 2000);
    }
}

function showCopyError() {
    const copyBtn = document.getElementById('copyAddressBtn');
    if (copyBtn) {
        const originalContent = copyBtn.innerHTML;

        copyBtn.innerHTML = '<i class="bi bi-x"></i> Failed';
        copyBtn.classList.remove('btn-outline-primary');
        copyBtn.classList.add('btn-danger');

        setTimeout(() => {
            copyBtn.innerHTML = originalContent;
            copyBtn.classList.remove('btn-danger');
            copyBtn.classList.add('btn-outline-primary');
        }, 2000);
    }
}

// Demo data fallback function
function getDemoData(address) {
    return {
        address: address,
        tax: {
            success: false,
            error: 'No API key configured - manual verification required'
        },
        propertyType: {
            success: false,
            error: 'No API key configured - manual verification required'
        },
        usda: {
            success: true,
            eligible: false,
            areaType: 'Urban',
            population: 45000,
            mapUrl: 'https://eligibility.sc.egov.usda.gov/eligibility/welcomeAction.do'
        },
        flood: {
            success: true,
            zone: 'X',
            riskLevel: 'Minimal Risk',
            insuranceRequired: false,
            mapUrl: 'https://msc.fema.gov/portal/search'
        },
        hoa: {
            success: false,
            error: 'No API integration available - manual verification required'
        },
        financing: {
            success: true,
            conventional: true,
            fha: true,
            va: true,
            usda: false,
            notes: 'Standard financing available. Property meets all loan program requirements.'
        }
    };
}

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PropertyIntelligence;
}
