// static/app.js

document.addEventListener('DOMContentLoaded', () => {
    // BILLING DASHBOARD

    const customerSelect = document.getElementById('customer-select');

    async function populateCustomerDropdown() {
        try {
            const response = await fetch('/api/customers');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const customers = await response.json();
            console.log("Fetched customers:", customers);

            customerSelect.innerHTML = '<option value="">-- Select a Customer --</option>';
            customers.forEach(customerId => {
                const option = document.createElement('option');
                option.value = customerId;
                option.textContent = customerId;
                customerSelect.appendChild(option);
            });
        } catch (error) {
            console.error("Failed to fetch customers:", error);
            customerSelect.innerHTML = '<option value="">Error loading customers</option>';
        }
    }

    // Initialize the webapp
    populateCustomerDropdown();
});