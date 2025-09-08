// static/app.js

// THEME SWITCHER LOGIC

document.addEventListener('DOMContentLoaded', () => {
    const themeSwitcher = document.querySelector('.theme-switcher');
    if (!themeSwitcher) return;

    const themeIcon = document.getElementById('theme-icon');
    const sunIcon = "/static/icons/sun.svg";
    const moonIcon = "/static/icons/moon.svg";
    const footerLogo = document.getElementById('footer-logo');
    const whiteLogo = "/static/icons/emitsolar_white.png";
    const blackLogo = "/static/icons/emitsolar_black.png";

    const setTheme = (isDark) => {
        document.body.classList.toggle('dark-mode', isDark);
        themeIcon.src = isDark ? sunIcon : moonIcon;
        if (footerLogo) {
            footerLogo.src = isDark ? whiteLogo : blackLogo;
        }
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    };

    // Initialize on landing
    const savedTheme = localStorage.getItem('theme');
    const isDarkMode = savedTheme ? savedTheme === 'dark' : false;
    setTheme(isDarkMode);

    themeSwitcher.addEventListener('click', () => {
        setTheme(!document.body.classList.contains('dark-mode'));
    });
});

// BILLING CALCULATOR LOGIC

$(document).ready(function() {
    console.log("DOM fully loaded and parsed.");

    // STATE MANAGEMENT

    let currentReadings = {};
    let loadedMonths = new Set();
    let startDate = null;
    let endDate = null;

    // CALCULATOR FIELDS

    const customerSelect = $('#customer-select');
    const dateRangePicker = $('#date-range-picker');
    const calculateBtn = $('#calculate-btn');
    const importKwhDisplay = $('#import-kwh-display');
    const exportKwhInput = $('#export-kwh');
    const importRateInput = $('#import-rate');
    const exportRateInput = $('#export-rate');
    const resultPeriod = $('#result-period');
    const resultStartKwh = $('#result-start-kwh');
    const resultEndKwh = $('#result-end-kwh');
    const resultTotalKwh = $('#result-total-kwh');
    const resultImportKwh = $('#result-import-kwh');
    const resultExportKwh = $('#result-export-kwh');
    const resultImportCost = $('#result-import-cost');
    const resultExportCost = $('#result-export-cost');
    const resultTotalBill = $('#result-total-bill');

    // DATA FETCHING

    async function fetchReadingsForMonth(customerId, year, month) {
        const monthKey = `${year}-${String(month).padStart(2, '0')}`;
        if (!customerId || loadedMonths.has(monthKey)) return false;
        console.log(`Fetching data for: ${monthKey}`);

        try {
            const response = await fetch(`/api/daily-readings?customer_id=${customerId}&year=${year}&month=${month}`);
            if (!response.ok) throw new Error('Network response not ok');

            const newReadings = await response.json();
            currentReadings = { ...currentReadings, ...newReadings };
            loadedMonths.add(monthKey);
            console.log(`Data received for ${monthKey}. Total readings stored: ${Object.keys(currentReadings).length}`);
            return true;
        } catch (error) {
            console.error('Failed to fetch daily readings:', error);
            return false;
        }
    }

    function updatePreliminaryCalculations() {
        if (!startDate || !endDate) {
            return;
        }

        const startReading = currentReadings[startDate.format('YYYY-MM-DD')];
        const endReading = currentReadings[endDate.format('YYYY-MM-DD')];
        const exportKwh = parseFloat(exportKwhInput.val()) || 0;

        if (endReading < startReading) {
            importKwhDisplay.val('0.00');
            resultImportKwh.text('0.00');
            resultTotalKwh.text('Error');
            return;
        }

        const totalGeneratedKwh = endReading - startReading;
        const importKwh = totalGeneratedKwh - exportKwh;

        // Update calculator fields
        resultStartKwh.text(startReading.toFixed(2));
        resultEndKwh.text(endReading.toFixed(2));
        resultTotalKwh.text(totalGeneratedKwh.toFixed(2));
        importKwhDisplay.val(importKwh.toFixed(2));
        resultImportKwh.text(importKwh.toFixed(2));
        resultExportKwh.text(exportKwh.toFixed(2));
    }

    // CALENDAR PICKER

    function setupDateRangePicker() {
        // Reset existing picker instance
        dateRangePicker.data('daterangepicker')?.remove();

        // Initialize the date range picker
        dateRangePicker.daterangepicker({
            autoUpdateInput: false,
            locale: { cancelLabel: 'Clear' },
            isInvalidDate: (date) => !currentReadings.hasOwnProperty(date.format('YYYY-MM-DD'))
        });

        // Event handler for date range selection
        dateRangePicker.on('apply.daterangepicker', function(ev, picker) {
            startDate = picker.startDate;
            endDate = picker.endDate;
            const startStr = startDate.format('DD MMM YYYY');
            const endStr = endDate.format('DD MMM YYYY');
            $(this).val(`${startStr} - ${endStr}`);
            resultPeriod.text(`${startStr} to ${endStr}`);

            // Update calculation fields
            updatePreliminaryCalculations();
        });

        // Event handler for selection cancellation
        dateRangePicker.on('cancel.daterangepicker', function(ev, picker) {
            startDate = null;
            endDate = null;
            $(this).val('');
        });

        // Month navigation handler
        const handleMonthChange = async (ev, picker) => {
            const customerId = customerSelect.val();
            const monthToFetch = picker.leftCalendar.calendar[1][1]; 
            const newDataFetched = await fetchReadingsForMonth(customerId, monthToFetch.year(), monthToFetch.month() + 1);

            // Update calendar if new data was fetched
            if (newDataFetched) {
                const drp = dateRangePicker.data('daterangepicker');
                drp.updateCalendars();
            }
        };
        dateRangePicker.on('next.daterangepicker', handleMonthChange);
        dateRangePicker.on('prev.daterangepicker', handleMonthChange);
    }

    // BILLING CALCULATION

    function calculateAndDisplayBill() {
        if (!startDate || !endDate) {
            alert('Please select a start and end date.');
            return;
        }
        const startReading = currentReadings[startDate.format('YYYY-MM-DD')];
        const endReading = currentReadings[endDate.format('YYYY-MM-DD')];
        const exportKwh = parseFloat(exportKwhInput.val()) || 0;
        const importRate = parseFloat(importRateInput.val()) || 0;
        const exportRate = parseFloat(exportRateInput.val()) || 0;

        if (endReading < startReading) {
            alert("Error: End reading is lower than start reading. Please check the meter data.");
            return;
        }
        const totalGeneratedKwh = endReading - startReading;
        const importKwh = totalGeneratedKwh - exportKwh;
        const importCost = importKwh * importRate;
        const exportRevenue = exportKwh * exportRate;
        const totalBill = importCost + exportRevenue;

        resultStartKwh.text(startReading.toFixed(2));
        resultEndKwh.text(endReading.toFixed(2));
        resultTotalKwh.text(totalGeneratedKwh.toFixed(2));
        importKwhDisplay.val(importKwh.toFixed(2));
        resultImportKwh.text(importKwh.toFixed(2));
        resultExportKwh.text(exportKwh.toFixed(2));
        resultImportCost.text(`RM ${importCost.toFixed(2)}`);
        resultExportCost.text(`RM ${exportRevenue.toFixed(2)}`);
        resultTotalBill.text(`RM ${totalBill.toFixed(2)}`);
    }

    // EVENT LISTENERS

    customerSelect.on('change', async function() {
        const customerId = $(this).val();
        currentReadings = {};
        loadedMonths.clear();
        startDate = null;
        endDate = null;
        dateRangePicker.val('');
        dateRangePicker.prop('disabled', true);

        if (customerId) {
            const now = moment();
            await Promise.all([
                fetchReadingsForMonth(customerId, now.clone().subtract(1, 'month').year(), now.clone().subtract(1, 'month').month() + 1),
                fetchReadingsForMonth(customerId, now.year(), now.month() + 1),
                fetchReadingsForMonth(customerId, now.clone().add(1, 'month').year(), now.clone().add(1, 'month').month() + 1)
            ]);

            // Reinitialize calendar picker
            setupDateRangePicker();
            dateRangePicker.prop('disabled', false);
        }
    });
    exportKwhInput.on('input', updatePreliminaryCalculations);
    calculateBtn.on('click', calculateAndDisplayBill);

    // FETCH CUSTOMERS

    async function populateCustomerDropdown() {
        try {
            const response = await fetch('/api/customers');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const customers = await response.json();
            customerSelect.html('<option value="">Select Customer</option>');
            customers.forEach(customerId => {
                customerSelect.append($('<option>', { value: customerId, text: customerId }));
            });
        } catch (error) {
            console.error("Failed to fetch customers:", error);
            customerSelect.html('<option value="">Error loading customers</option>');
        }
    }

    populateCustomerDropdown();
    dateRangePicker.prop('disabled', true);
});