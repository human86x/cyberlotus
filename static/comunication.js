
        // Placeholder for adding actions

        function logMessage(message) {
            const output = document.getElementById('consoleOutput');
            output.value += `\n${message}`;
            output.scrollTop = output.scrollHeight;
        }



        function calibrate() {
    const sequence = document.getElementById('sequence').value;
    logMessage(`Starting calibration for: ${sequence}`);

    if (sequence === "LOW") {
        fetch('/calibrate_ph_low')
        .then(response => response.json())
        .then(data => {
            console.log('pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching pH readings for LOW:', error);
        });
    } else if (sequence === "HIGH") {
        fetch('/calibrate_ph_high')
        .then(response => response.json())
        .then(data => {
            console.log('pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching pH readings for HIGH:', error);
        });
    } else {
        console.error('Invalid calibration sequence selected.');
    }

    // Send calibration command (implement backend communication here)
}


function simple_cal_low_Ph() {
    fetch('/simple_calibrate_ph_low')
        .then(response => response.json())
        .then(data => {
            console.log('raw pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching raw pH readings:', error);
        });
}
function simple_cal_high_Ph() {
    fetch('/simple_calibrate_ph_high')
        .then(response => response.json())
        .then(data => {
            console.log('raw pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching raw pH readings:', error);
        });
}

function solutionPh() {
    fetch('/ph_solution_test')
        .then(response => response.json())
        .then(data => {
            console.log('raw pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching raw pH readings:', error);
        });
}


function baselinePh() {
    fetch('/ph_baseline_test')
        .then(response => response.json())
        .then(data => {
            console.log('raw pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching raw pH readings:', error);
        });
}


        
function rawPh() {
    fetch('/get_raw_ph')
        .then(response => response.json())
        .then(data => {
            console.log('raw pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching raw pH readings:', error);
        });
}


        
        function testPh() {
    fetch('/get_ph')
        .then(response => response.json())
        .then(data => {
            console.log('pH Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching pH readings:', error);
        });
}

        function fetchValue() {
            logMessage('Fetching current pH value...');
            // Fetch current pH value (implement backend communication here)
        }

        function saveConfig() {
            logMessage('Saving pH configuration...');
            // Save configuration to file or backend (implement here)
        }

        function loadConfig() {
            logMessage('Loading pH configuration...');
            // Load configuration from file or backend (implement here)
        }




        //////////////////////EC///////////////////



        const eventSource = new EventSource('/stream');
            eventSource.onmessage = function(event) {
                document.getElementById('content').innerText = event.data;
            };

// Function to trigger EC sensor calibration
async function calibrateECSensor() {
    try {
        const response = await fetch('/calibrate_ec_sensor', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const result = await response.json();

        if (response.ok) {
            alert(result.message);
        } else {
            alert(`Error: ${result.error}`);
        }
    } catch (error) {
        console.error('Request failed:', error);
        alert('An error occurred while trying to calibrate the EC sensor.');
    }
}


function loadCalibrationData() {
    fetch('/get_calibration_data')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const calibrationData = JSON.stringify(data.data, null, 2); // Pretty print JSON
                document.getElementById('calibrationData').value = calibrationData;
            } else {
                alert('Failed to load calibration data.');
            }
        })
        .catch(error => console.error('Error fetching calibration data:', error));
}

// Load calibration data on page load
document.addEventListener('DOMContentLoaded', loadCalibrationData);

let currentStep = 0;
        const totalSteps = 4;
        const progressBar = document.getElementById('progressBar');
        const ecValueElement = document.getElementById('ecValue');
        const temperatureElement = document.getElementById('temperature');

        function updateProgressBar() {
            let progress = (currentStep / totalSteps) * 100;
            progressBar.style.width = progress + '%';
        }

        function fetchECValue() {
            fetch('/get_ec')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        ecValueElement.textContent = data.ec_value;
                    } else {
                        ecValueElement.textContent = "Error fetching EC value";
                    }
                });
        }



        function get_complex_ec(){
        fetch('/get_complex_ec')
            .then(response => response.json())
            .then(data => {
                console.log('EC Readings:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching EC readings:', error);
        });
    }
    function get_ec_baseline(){
        fetch('/get_ec_baseline')
            .then(response => response.json())
            .then(data => {
                console.log('EC baseline:', data.readings);
        })
        .catch(error => {
            console.error('Error fetching EC baseline:', error);
        });
    }




        function fetchTemperature() {
            fetch('/get_temperature')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        temperatureElement.textContent = data.temperature;
                    } else {
                        temperatureElement.textContent = "Error fetching temperature";
                    }
                });
        }

        function loadSequenceFiles() {
            fetch('/list_sequences')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        const calibrationDropdown = document.getElementById('calibrationSequence');
                        const testDropdown = document.getElementById('testSequence');
                        const baselineDropdown = document.getElementById('baselineSequence');
                        calibrationDropdown.innerHTML = '';
                        testDropdown.innerHTML = '';
                        baselineDropdown.innerHTML = '';
                        data.files.forEach(file => {
                            const option = document.createElement('option');
                            option.value = file;
                            option.textContent = file;

                            // Add options to both dropdowns
                            calibrationDropdown.appendChild(option.cloneNode(true));
                            testDropdown.appendChild(option.cloneNode(true));
                            baselineDropdown.appendChild(option.cloneNode(true));
                            
                        });
                    } else {
                        alert(data.message);
                    }
                })
                .catch(error => console.error('Error fetching sequence files:', error));
        }

        function startCalibration() {
            currentStep = 0;
            updateProgressBar();
            runCalibrationStep();
        }

        function runCalibrationStep() {
            if (currentStep >= totalSteps) return;

            setTimeout(() => {
                currentStep++;
                updateProgressBar();
                runCalibrationStep();
            }, 3000);
        }

        function startTestSequence() {
            const selectedTestSequence = document.getElementById('testSequence').value;
            fetch(`/start_callback_sequence/${selectedTestSequence}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        fetchECValue();
                    }
                });
        }
        function loadSystemState() {
            //const selectedTestSequence = document.getElementById('testSequence').value;
            fetch(`/load_sys_state`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        //fetchECValue();
                    }
                });
        }



// Load configuration on page load
function loadAppConfig() {
            fetch('/get_app_config')
                .then(response => response.json())
                .then(config => {
                    if (config.EC_calibration_sequence) {
                        document.getElementById('calibrationSequence').value = config.EC_calibration_sequence;
                    }
                    if (config.EC_test_sequence) {
                        document.getElementById('testSequence').value = config.EC_test_sequence;
                    }
                    if (config.EC_baseline_sequence) {
                        document.getElementById('baselineSequence').value = config.EC_baseline_sequence;
                    }
                })
                .catch(error => console.error('Error loading app config:', error));
        }

        // Save selected values to config
        function saveConfig() {
            const configData = {
                EC_calibration_sequence: document.getElementById('calibrationSequence').value,
                EC_test_sequence: document.getElementById('testSequence').value,
                EC_baseline_sequence: document.getElementById('baselineSequence').value
            };

            fetch('/save_app_config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(configData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('Configuration saved successfully.');
                } else {
                    alert('Error saving configuration.');
                }
            })
            .catch(error => console.error('Error saving config:', error));
        }

        // Call this function to save the configuration when needed (e.g., on form submit)
        // saveConfig();

        // Fetch initial data and load sequences
        
        
        ///////////////////////////////////////////

        /////////////////////TANKS/////////////////

function adjustTankLevel() {
    // Show the progress bar
    document.getElementById("progress-container").style.display = "block";
    var progressBar = document.getElementById("progress-bar");
    var width = 0;

    // Simulate progress
    var progressInterval = setInterval(function() {
        if (width >= 100) {
            clearInterval(progressInterval);
            
            // Refresh tank information after adjustment is complete
            fetch('/refresh_tank_info')  // Replace with actual endpoint
                .then(response => response.json())
                .then(data => updateTankDisplay(data))  // Define this function to update UI
                .catch(error => console.error('Error:', error));

            // Hide progress bar after a delay
            setTimeout(() => {
                document.getElementById("progress-container").style.display = "none";
                progressBar.style.width = "0%";
            }, 1000);
        } else {
            width++;
            progressBar.style.width = width + "%";
        }
    }, 50);  // Adjust speed if necessary
}





function drainWaste() {
    let resultDisplay = document.getElementById("drain-result");
    resultDisplay.textContent = "Starting waste drain...";

    fetch("/drain_waste", {
        method: "POST",
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "success") {
            resultDisplay.textContent = `Waste drained successfully using ${data.pump_used}!`;
        } else {
            resultDisplay.textContent = `Error: ${data.message}`;
        }
    })
    .catch(error => {
        console.error("Error draining waste:", error);
        resultDisplay.textContent = "Error starting drain process.";
    });
}





function savePumpAssignments() {
    // Get the selected values from the dropdowns
    const fillPump = document.getElementById('fill_pump').value;
    const drainPump = document.getElementById('drain_pump').value;

    if (!fillPump || !drainPump) {
        alert("Please select both filling and draining pumps.");
        return;
    }

    // Send the selected pump assignments to the server via POST request
    fetch("/save_pump_assignment", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            fill_pump: fillPump,
            drain_pump: drainPump
        })
    })
    .then(response => response.json())
    .then(data => {
        // Handle the response from the server
        alert("Pump assignments saved successfully!");
    })
    .catch(error => {
        console.error('Error saving pump assignments:', error);
    });
}

// Function to load the solution level on page load
function loadSolutionLevel() {
    fetch("/get_solution_level")
        .then(response => response.json())
        .then(data => {
            if (data.solution_level !== undefined) {
                solution_level = data.solution_level;
                document.getElementById("solution-level-slider").value = solution_level;
                document.getElementById("solution-level-display").textContent = solution_level + "%";
            }
        })
        .catch(error => {
            console.error("Error loading solution level:", error);
        });
}

// Load pump names dynamically into dropdowns
function loadPumpNames() {
    fetch("/pumps")
        .then(response => response.json())
        .then(data => {
            let drainingPumpSelect = document.getElementById("drain_pump");
            let fillingPumpSelect = document.getElementById("fill_pump");

            data.pump_names.forEach(pump => {
                let drainingOption = document.createElement("option");
                drainingOption.value = pump;
                drainingOption.textContent = pump;
                drainingPumpSelect.appendChild(drainingOption);

                let fillingOption = document.createElement("option");
                fillingOption.value = pump;
                fillingOption.textContent = pump;
                fillingPumpSelect.appendChild(fillingOption);
            });

            // Load saved pump selections from app_config.json
            loadSavedPumpSelections();
        })
        .catch(error => {
            console.error("Error loading pump names:", error);
        });
}

function loadSavedPumpSelections() {
    fetch("/get_saved_pumps")
        .then(response => response.json())
        .then(data => {
            if (data.fill_pump && data.drain_pump) {
                document.getElementById('fill_pump').value = data.fill_pump;
                document.getElementById('drain_pump').value = data.drain_pump;
            }
        })
        .catch(error => {
            console.error("Error loading saved pump selections:", error);
        });
}

// Function to fetch and display tank data
function fetchTankData() {
    fetch("/test_tanks_route")
        .then(response => response.json())
        .then(data => {
            let tanksDisplay = document.getElementById("tanks-display");
            tanksDisplay.innerHTML = '';
            
            Object.keys(data).forEach(tank => {
                let result = data[tank];
                let tankDiv = document.createElement("div");
                tankDiv.className = "tank-card";
                tankDiv.style = "text-align: center; margin: 10px; display: inline-block;";
                tankDiv.innerHTML = `
                    <div style="height: 200px; width: 50px; background-color: #ddd; border: 1px solid #333; position: relative;">
                        <div id="${tank}-fill-bar" style="position: absolute; bottom: 0; width: 100%; background-color: green; height: ${result.fill_percentage}%;"></div>
                    </div>
                    <h4>${tank}</h4>
                    <p>Arduino Code: ${result.arduino_code}</p>
                    <p>Total Volume: ${result.total_volume} L</p>
                    <p>Full: ${result.full_cm} cm</p>
                    <p>Empty: ${result.empty_cm} cm</p>
                    <p>Fill Level: ${result.fill_percentage}%</p>
                `;
                tanksDisplay.appendChild(tankDiv);
            });
        })
        .catch(error => {
            console.error("Error fetching tank data:", error);
        });
}

// Load tank data and pump names on page load
window.onload = function() {
    fetchTankData();
    loadSolutionLevel();
    loadPumpNames();
    loadSavedPumpSelections();
};

// Save pump assignments on form submission
document.getElementById('pumpForm').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const fillPump = document.getElementById('fill_pump').value;
    const drainPump = document.getElementById('drain_pump').value;

    fetch('/save_pump_assignment', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ fill_pump: fillPump, drain_pump: drainPump })
    })
    .then(response => response.json())
    .then(data => alert(data.message))
    .catch(error => console.error('Error saving pump assignments:', error));
});





function compareSolutionLevel() {
    // Show the progress bar container
    let progressContainer = document.getElementById("progress-container");
    let progressBar = document.getElementById("progress-bar");
    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';  // Reset progress

    // Simulate progress for 5 seconds (adjust as needed)
    let duration = 5000;  // 5 seconds
    let intervalTime = 100;  // Update every 100ms
    let elapsedTime = 0;

    // Start the progress animation
    let progressInterval = setInterval(() => {
        elapsedTime += intervalTime;
        let progress = Math.min((elapsedTime / duration) * 100, 100);
        progressBar.style.width = progress + '%';

        if (progress >= 100) {
            clearInterval(progressInterval);
        }
    }, intervalTime);

    // Fetch solution level comparison data
    fetch("/compare_solution_level")
        .then(response => response.json())
        .then(data => {
            let resultsDisplay = document.getElementById("adjustment-results");
            resultsDisplay.innerHTML = '';  // Clear previous results

            // Display only the 'solution' tank results
            if (data.solution) {
                let result = data.solution;
                let resultDiv = document.createElement("div");
                resultDiv.className = "tank-result";
                resultDiv.style = "margin: 10px; padding: 10px; border: 1px solid #ccc;";
                resultDiv.innerHTML = `
                    <h4>Solution Tank</h4>
                    <p>Action: ${result.action}</p>
                    <p>Volume to ${result.action === 'drain' ? 'drain' : 'add'}: ${result.volume_liters.toFixed(2)} L</p>
                `;
                resultsDisplay.appendChild(resultDiv);
            }

            // Hide the progress bar after completion
            setTimeout(() => {
                progressContainer.style.display = 'none';
            }, 500);  // Slight delay for smooth transition
        })
        .catch(error => {
            console.error("Error fetching solution level comparison:", error);
            
            // Hide the progress bar on error
            progressContainer.style.display = 'none';
        });
}

document.getElementById("solution-level-slider").addEventListener("input", function(event) {
    solution_level = event.target.value;
    document.getElementById("solution-level-display").textContent = solution_level + "%";
});

document.getElementById("save-solution-level-button").addEventListener("click", function() {
    const drainingPump = document.getElementById("drain_pump").value;
    const fillingPump = document.getElementById("fill_pump").value;

    if (!drainingPump || !fillingPump) {
        alert("Please select both draining and filling pumps.");
        return;
    }

    // Send the current solution level and pump selections to the server to save to JSON
    fetch("/save_solution_level", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ 
            solution_level: solution_level,
            draining_pump: drainingPump,
            filling_pump: fillingPump
        })
    })
    .then(response => response.json())
    .then(data => {
        alert("Solution level and pump settings saved successfully!");
    })
    .catch(error => {
        console.error("Error saving solution level:", error);
    });
});

        document.getElementById('adjustTankButton').addEventListener('click', function() {
    // Show the progress bar
    const progressContainer = document.getElementById("progress-container");
    const progressBar = document.getElementById("progress-bar");
    progressContainer.style.display = "block";
    progressBar.style.width = "0%";

    // Simulate progress while waiting for the server response
    let width = 0;
    const progressInterval = setInterval(() => {
        if (width < 90) {  // Simulate up to 90% until server responds
            width += 1;
            progressBar.style.width = width + "%";
        }
    }, 100);  // Adjust speed if needed

    // Send a POST request to the '/adjust_solution_tank' route
    fetch("/adjust_solution_tank", {
        method: "POST"
    })
    .then(response => response.json())
    .then(data => {
        clearInterval(progressInterval);  // Stop the simulated progress

        // Instantly complete the progress bar
        progressBar.style.width = "100%";

        // Display the result message
        const responseMessageDiv = document.getElementById("responseMessage");
        if (data.status === "success") {
            responseMessageDiv.innerHTML = `<p>✅ Success: ${data.message}</p>`;
        } else {
            responseMessageDiv.innerHTML = `<p>❌ Error: ${data.message}</p>`;
        }

        // Hide the progress bar after a short delay
        setTimeout(() => {
            progressContainer.style.display = "none";
            progressBar.style.width = "0%";
        }, 1000);  // 1-second delay before hiding
    })
    .catch(error => {
        clearInterval(progressInterval);
        console.error("Error calling adjust_tank_level:", error);

        // Show error feedback
        const responseMessageDiv = document.getElementById("responseMessage");
        responseMessageDiv.innerHTML = `<p>❌ Error: Failed to adjust tank level.</p>`;

        // Hide the progress bar after a short delay
        setTimeout(() => {
            progressContainer.style.display = "none";
            progressBar.style.width = "0%";
        }, 1000);
    });
});

 

        ///////////////////////////////////////////

        ///////////////////DASHBOARD///////////////
 
        function getSystemStats() {
            fetch("/sys_state")
                .then(response => response.json())
                .then(data => {
                    updateDashboard(data);
                    return data
                })
                .catch(error => {
                    console.error('Error:', error);
                });
        }

        function updateDashboard(data) {
            document.getElementById("ecLevel").textContent = data.ec_solution?.value || "N/A";
            document.getElementById("phLevel").textContent = data.ph_solution?.value || "N/A";
            document.getElementById("temperature").textContent = data.temperature?.value || "N/A";

            updateBarChart(solutionTankBar, [
                data.solution_tank?.value || 0,
                data.fresh_tank?.value || 0,
                data.waste_tank?.value || 0
            ]);

            updatePieChart(relayStatesPie, Object.values(data.relay_states || {}).map(r => r.state ? 1 : 0));
        }

        let solutionTankBar = createBarChart("solutionTankBar", "Tank Levels", ["Solution", "Fresh", "Waste"], [0, 0, 0]);
        let relayStatesPie = createPieChart("relayStatesPie", "Relay States", ["On", "Off"], [1, 0]);
  
        function createBarChart(canvasId, title, labels, data) {
            const ctx = document.getElementById(canvasId).getContext("2d");
            return new Chart(ctx, {
                type: "bar",
                data: {
                    labels: labels,
                    datasets: [{
                        label: title,
                        data: data,
                        backgroundColor: ["#007bff", "#28a745", "#dc3545"],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        function createPieChart(canvasId, title, labels, data) {
            const ctx = document.getElementById(canvasId).getContext("2d");
            return new Chart(ctx, {
                type: "pie",
                data: {
                    labels: labels,
                    datasets: [{
                        label: title,
                        data: data,
                        backgroundColor: ["#007bff", "#dc3545"],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true
                }
            });
        }

        function updateBarChart(chart, data) {
            chart.data.datasets[0].data = data;
            chart.update();
        }

        function updatePieChart(chart, data) {
            chart.data.datasets[0].data = data;
            chart.update();
        }

        setInterval(getSystemStats, 1000);

        ///////////////////////////////////////////


        loadCalibrationData();
        // Fetch initial data and load sequences
        //fetchECValue();
        //fetchTemperature();
        loadSequenceFiles();
        loadAppConfig();

   
