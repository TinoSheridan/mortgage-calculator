// Simple test script to verify abbreviation functionality
document.addEventListener('DOMContentLoaded', function() {
    // Create test output element
    const testOutputDiv = document.createElement('div');
    testOutputDiv.id = 'abbreviationTest';
    testOutputDiv.style.position = 'fixed';
    testOutputDiv.style.bottom = '10px';
    testOutputDiv.style.right = '10px';
    testOutputDiv.style.backgroundColor = '#f8f9fa';
    testOutputDiv.style.border = '1px solid #ddd';
    testOutputDiv.style.padding = '10px';
    testOutputDiv.style.zIndex = '9999';
    testOutputDiv.style.maxWidth = '50%';
    testOutputDiv.style.maxHeight = '50%';
    testOutputDiv.style.overflow = 'auto';

    // Add a close button
    const closeButton = document.createElement('button');
    closeButton.textContent = 'Close';
    closeButton.style.marginBottom = '10px';
    closeButton.addEventListener('click', function() {
        testOutputDiv.style.display = 'none';
    });
    testOutputDiv.appendChild(closeButton);

    // Add a title
    const title = document.createElement('h4');
    title.textContent = 'Abbreviation Tests';
    testOutputDiv.appendChild(title);

    // Create test content
    const testCases = [
        'Total Monthly Payment',
        'Owners Title Insurance',
        'Total Closing Cost',
        'Total Cash to Close',
        'Principal and Interest',
        'Private Mortgage Insurance',
        'Processing Fee',
        'This is a very long label that should be truncated'
    ];

    // Wait a moment to ensure calculator.js is fully loaded
    setTimeout(() => {
        // Add test results
        const resultsList = document.createElement('ul');
        testCases.forEach(testCase => {
            try {
                // Use the global abbreviateMortgageLabel function from calculator.js
                const abbreviated = window.abbreviateMortgageLabel(testCase, 25);
                const listItem = document.createElement('li');
                listItem.innerHTML = `<strong>${testCase}</strong> → "${abbreviated}"`;
                resultsList.appendChild(listItem);
            } catch (e) {
                const listItem = document.createElement('li');
                listItem.innerHTML = `<strong>${testCase}</strong> → ERROR: ${e.message}`;
                listItem.style.color = 'red';
                resultsList.appendChild(listItem);
            }
        });

        testOutputDiv.appendChild(resultsList);
        document.body.appendChild(testOutputDiv);
    }, 500); // Wait 500ms to ensure calculator.js is loaded
});
