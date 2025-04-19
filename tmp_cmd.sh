#!/bin/bash
# Extract the form fields section
sed -n '/class="form-group mb-3"/,/<div class="row mt-4">/p' templates/index.html.bak >> templates/index.html

# Add the calculate button
cat >> templates/index.html << 'INNER'
                        <!-- Calculate Button -->
                        <div class="row mt-4">
                            <div class="col-12">
                                <button id="calculateBtn" type="submit" class="btn btn-primary w-100">Calculate</button>
                            </div>
                        </div>
                    </div>
                </div>
            </form>
        </div>

        <!-- Results Column -->
        <div class="results-column">
            <!-- Monthly Payment Breakdown Card -->
            <div class="card results-card mb-4">
                <div class="card-header">
                    <h4 class="mb-0">Monthly Payment Breakdown</h4>
                </div>
                <div class="card-body">
                    <table class="table table-hover">
                        <tbody>
                            <tr>
                                <td>Principal & Interest</td>
                                <td class="text-end" id="monthlyPayment">$0.00</td>
                            </tr>
                            <tr>
                                <td>Property Tax</td>
                                <td class="text-end" id="monthlyTax">$0.00</td>
                            </tr>
                            <tr>
                                <td>Homeowners Insurance</td>
                                <td class="text-end" id="monthlyInsurance">$0.00</td>
                            </tr>
                            <tr>
                                <td>HOA Fees</td>
                                <td class="text-end" id="monthlyHoa">$0.00</td>
                            </tr>
                            <tr>
                                <td>Mortgage Insurance</td>
                                <td class="text-end" id="monthlyPmi">$0.00</td>
                            </tr>
                            <tr class="total-row">
                                <td><strong>Total Monthly Payment</strong></td>
                                <td class="text-end" id="totalMonthlyPayment"><strong>$0.00</strong></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Loan Details Card -->
            <div class="card results-card mb-4">
                <div class="card-header">
                    <h4 class="mb-0">Loan Details</h4>
                </div>
                <div class="card-body">
                    <table class="table table-hover">
                        <tbody>
                            <tr>
                                <td>Purchase Price</td>
                                <td class="text-end" id="purchasePrice">$0.00</td>
                            </tr>
                            <tr>
                                <td>Down Payment</td>
                                <td class="text-end" id="downPaymentAmount">$0.00</td>
                            </tr>
                            <tr>
                                <td>Base Loan Amount</td>
                                <td class="text-end" id="baseLoanAmount">$0.00</td>
                            </tr>
                            <tr id="upfrontMipRow" style="display: none;">
                                <td>Upfront MIP</td>
                                <td class="text-end" id="upfrontMip">$0.00</td>
                            </tr>
                            <tr>
                                <td>Total Loan Amount</td>
                                <td class="text-end" id="loanAmount">$0.00</td>
                            </tr>
                            <tr>
                                <td>Interest Rate</td>
                                <td class="text-end" id="interestRate">0%</td>
                            </tr>
                            <tr>
                                <td>Loan Term</td>
                                <td class="text-end" id="loanTermDisplay">30 years</td>
                            </tr>
                            <tr>
                                <td>LTV (Loan-to-Value)</td>
                                <td class="text-end" id="ltvDisplay">0%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Cash Needed at Closing Card -->
            <div class="card results-card mb-4">
                <div class="card-header">
                    <h4 class="mb-0">Cash Needed at Closing</h4>
                </div>
                <div class="card-body">
                    <h5 class="section-title">Down Payment</h5>
                    <table class="table table-sm">
                        <tbody>
                            <tr>
                                <td>Down Payment</td>
                                <td class="text-end" id="downPayment">$0.00</td>
                            </tr>
                        </tbody>
                    </table>

                    <h5 class="section-title">Closing Costs</h5>
                    <table class="table table-sm">
                        <tbody id="closingCostsTable">
                            <!-- Populated by JavaScript -->
                        </tbody>
                        <tfoot class="total-row">
                            <tr>
                                <td><strong>Total Closing Costs</strong></td>
                                <td class="text-end" id="totalClosingCosts"><strong>$0.00</strong></td>
                            </tr>
                        </tfoot>
                    </table>

                    <h5 class="section-title">Prepaid Items</h5>
                    <table class="table table-sm">
                        <tbody id="prepaidsTable">
                            <!-- Populated by JavaScript -->
                        </tbody>
                        <tfoot class="total-row">
                            <tr>
                                <td><strong>Total Prepaid Items</strong></td>
                                <td class="text-end" id="totalPrepaids"><strong>$0.00</strong></td>
                            </tr>
                        </tfoot>
                    </table>

                    <h5 class="section-title">Total Cash Needed</h5>
                    <table class="table table-sm">
                        <tbody>
                            <tr class="total-row">
                                <td><strong>Total Cash Needed at Closing</strong></td>
                                <td class="text-end" id="totalCashNeeded"><strong>$0.00</strong></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Loading Spinner and Error Alert -->
            <div class="my-4 text-center">
                <div id="loadingSpinner" class="spinner-border text-primary mx-auto d-none" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div id="errorAlert" class="alert alert-danger" style="display: none;" role="alert">
                    Error message goes here.
                </div>
            </div>
        </div>
    </div>

    <!-- Debug Section -->
    <div class="mt-5 mb-3">
        <p id="debugToggle" class="text-center">Show/Hide Debug Information</p>
        <div id="debugSection" style="display: none;">
            <div class="card">
                <div class="card-header">
                    <h5 class="mb-0">Debug Output</h5>
                </div>
                <div class="card-body p-0">
                    <div id="debugOutput" class="p-3"></div>
                </div>
            </div>
        </div>
    </div>
{% endblock %}
INNER
