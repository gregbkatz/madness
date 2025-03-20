// Comprehensive mobile scrolling fixes
if ('scrollRestoration' in history) {
    history.scrollRestoration = 'manual';
}

// iOS Safari specific fixes
document.addEventListener('touchend', function () {
    // Delay to ensure any momentum scrolling has finished
    setTimeout(function () {
        // Prevent scroll bounce by checking if we're near the bottom
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 100) {
            // Force scroll to bottom to prevent snap-back
            window.scrollTo(0, document.body.offsetHeight);
        }
    }, 100);
});

// Listen for orientation changes
window.addEventListener('orientationchange', function () {
    // Scroll to current position after orientation change
    setTimeout(function () {
        window.scrollTo(0, window.scrollY);
    }, 300);
});

// Define the main Bracket component
function MarchMadnessBracket() {
    // Map of long team names to shortened display names
    const teamNameShortcuts = {
        "UNC Wilmington": "UNC Wilm.",
        "Texas/Xavier": "Xavier",
        "AL St/St Francis U": "AL St",
        "AU/Mt St Mary's": "Mt St Mary's",
        "San Diego St/NC": "UNC",
        "Mississppi St": "Miss. St",
    };

    const [teams, setTeams] = React.useState({
        midwest: [],
        west: [],
        south: [],
        east: []
    });

    const [bracket, setBracket] = React.useState({
        midwest: Array(4).fill().map(() => Array(8).fill(null)),
        west: Array(4).fill().map(() => Array(8).fill(null)),
        south: Array(4).fill().map(() => Array(8).fill(null)),
        east: Array(4).fill().map(() => Array(8).fill(null)),
        finalFour: [null, null, null, null],
        championship: [null, null],
        champion: null
    });

    // State for saved brackets modal
    const [showModal, setShowModal] = React.useState(false);
    const [savedBrackets, setSavedBrackets] = React.useState([]);
    const [loadingBrackets, setLoadingBrackets] = React.useState(false);
    // Track bracket completion status
    const [completionStatus, setCompletionStatus] = React.useState({ complete: false, remainingPicks: 63 });
    // Add read-only mode state
    const [readOnly, setReadOnly] = React.useState(false);
    // Track bracket status
    const [bracketStatus, setBracketStatus] = React.useState(null);

    // Function to calculate how many games still need to be picked
    const calculateCompletionStatus = (bracketData) => {
        // In a 64-team tournament bracket structure:
        // - First round (round 0): Teams are pre-populated, no picks needed
        // - 2nd round (round 1): 16 games (4 per region * 4 regions)
        // - Sweet 16 (round 2): 8 games (2 per region * 4 regions)
        // - Elite 8 (round 3): 4 games (1 per region * 4 regions)
        // - Final Four: 2 games
        // - Championship: 1 game
        // Total: 31 picks needed (16 + 8 + 4 + 2 + 1)

        let totalPicks = 63; // Total picks needed to complete a bracket
        let completedPicks = 0;
        const regions = ['midwest', 'west', 'south', 'east'];

        try {
            // Count regional picks (Rounds 1-3, which represent 2nd round through Elite 8)
            regions.forEach(region => {
                if (!bracketData[region]) return;

                for (let round = 1; round < 4; round++) {
                    if (!bracketData[region][round]) continue;

                    // Count actual team selections (non-null entries) in this round
                    for (let i = 0; i < bracketData[region][round].length; i++) {
                        if (bracketData[region][round][i]) {
                            completedPicks++;
                        }
                    }
                }
            });

            // Count Final Four picks (4 slots)
            if (bracketData.finalFour) {
                for (let i = 0; i < bracketData.finalFour.length; i++) {
                    if (bracketData.finalFour[i]) {
                        completedPicks++;
                    }
                }
            }

            // Count Championship picks (2 slots)
            if (bracketData.championship) {
                for (let i = 0; i < bracketData.championship.length; i++) {
                    if (bracketData.championship[i]) {
                        completedPicks++;
                    }
                }
            }

            // Count Champion pick (1 slot)
            if (bracketData.champion) {
                completedPicks++;
            }

            // Ensure we don't go negative
            const remainingPicks = Math.max(0, totalPicks - completedPicks);

            return {
                complete: remainingPicks === 0,
                remainingPicks
            };
        } catch (error) {
            console.error("Error calculating completion status:", error);
            return {
                complete: false,
                remainingPicks: totalPicks
            };
        }
    };

    // Function to update the bracket completion status in the UI
    const updateCompletionStatus = (status) => {
        const completionStatusElement = document.getElementById('completion-status');
        if (completionStatusElement) {
            if (status.complete) {
                completionStatusElement.textContent = "✅ Bracket Complete!";
                completionStatusElement.classList.add('complete');
                completionStatusElement.classList.remove('incomplete');
            } else {
                completionStatusElement.textContent = `⚠️ ${status.remainingPicks} picks remaining`;
                completionStatusElement.classList.add('incomplete');
                completionStatusElement.classList.remove('complete');
            }
        }
    };

    // Function to update the save status indicator
    const updateSaveStatus = () => {
        const saveStatus = document.getElementById('save-status');
        if (saveStatus) {
            const now = new Date();
            const timeString = now.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            saveStatus.textContent = `📝 Bracket last saved at: ${timeString}`;

            // Add animation class
            saveStatus.classList.add('saving');

            // Remove animation class after animation completes
            setTimeout(() => {
                saveStatus.classList.remove('saving');
            }, 2000);
        }
    };

    // Fetch initial data
    React.useEffect(() => {
        // Fetch teams
        fetch('/api/teams')
            .then(response => response.json())
            .then(data => {
                setTeams(data);
            })
            .catch(error => console.error('Error fetching teams:', error));

        // Fetch bracket status
        fetch('/api/bracket-status')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    setBracketStatus(data.status);

                    // Get read-only state from API response instead of URL
                    if (data.read_only) {
                        setReadOnly(true);
                        console.log('Bracket is in read-only mode (server-controlled)');
                    }

                    // Update save status based on bracket status
                    const saveStatus = document.getElementById('save-status');
                    if (saveStatus && data.status) {
                        // Get the username from the User info display in the header
                        const userInfoElement = document.querySelector('.user-info');
                        let username = "there";
                        if (userInfoElement) {
                            // Extract username from "User: username" format
                            const userText = userInfoElement.textContent;
                            username = userText.replace('User:', '').trim();
                        }

                        if (data.status.type === 'new') {
                            saveStatus.textContent = `📋 Welcome ${username}! Thanks for creating a new bracket!`;
                        } else if (data.status.type === 'loaded') {
                            saveStatus.textContent = `📋 Welcome back ${username}! Your bracket from ${data.status.timestamp} has been loaded`;
                        }

                        // Add animation class for visual feedback
                        saveStatus.classList.add('saving');

                        // Remove animation class after animation completes
                        setTimeout(() => {
                            saveStatus.classList.remove('saving');
                        }, 2000);
                    }

                    // Show the status banner notification
                    const statusBanner = document.getElementById('status-banner');
                    if (statusBanner && data.status) {
                        // Reuse the same username we got earlier
                        if (data.status.type === 'new') {
                            statusBanner.textContent = `🌟 Welcome ${username}! Thanks for creating a new bracket!`;
                            statusBanner.className = 'status-banner new-bracket';
                        } else if (data.status.type === 'loaded') {
                            statusBanner.textContent = `📂 Welcome back ${username}! Your bracket from ${data.status.timestamp} has been loaded`;
                            statusBanner.className = 'status-banner loaded-bracket';
                        }

                        // Make the banner visible
                        setTimeout(() => {
                            statusBanner.classList.add('visible');
                        }, 500);

                        // Hide the banner after 8 seconds
                        setTimeout(() => {
                            statusBanner.classList.remove('visible');
                        }, 8000);
                    }
                }
            })
            .catch(error => console.error('Error fetching bracket status:', error));

        // Fetch current bracket state
        fetch('/api/bracket')
            .then(response => response.json())
            .then(data => {
                console.log('Bracket fetched:', data);
                setBracket(data);

                // Calculate and update completion status
                const status = calculateCompletionStatus(data);
                setCompletionStatus(status);
                updateCompletionStatus(status);
            })
            .catch(error => console.error('Error fetching bracket:', error));
    }, []);

    // Function to handle team selection in regular rounds
    const handleTeamSelect = (region, round, gameIndex, teamIndex) => {
        console.log(`Team select: region=${region}, round=${round}, game=${gameIndex}, team=${teamIndex}`);

        // Exit if in read-only mode
        if (readOnly) {
            console.log('Cannot make changes in read-only mode');
            return;
        }

        fetch('/api/bracket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'update',
                region: region,
                roundIndex: round,
                gameIndex: gameIndex,
                teamIndex: teamIndex
            })
        })
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Updated bracket:', data);
                setBracket(data);

                // Calculate and update completion status after selection
                const status = calculateCompletionStatus(data);
                setCompletionStatus(status);
                updateCompletionStatus(status);

                // Update save status when bracket changes (auto-save occurs)
                updateSaveStatus();
            })
            .catch(error => console.error('Error updating bracket:', error));
    };

    // Save bracket to server
    const saveBracket = () => {
        console.log('Saving bracket to file...');

        // Exit if in read-only mode
        if (readOnly) {
            console.log('Cannot save changes in read-only mode');
            return;
        }

        fetch('/api/save-bracket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Bracket saved successfully!');
                    console.log('Save success:', data.message);
                    updateSaveStatus();
                } else {
                    alert('Error saving bracket: ' + data.error);
                    console.error('Save error:', data.error);
                }
            })
            .catch(error => {
                alert('Error saving bracket. Please try again.');
                console.error('Error saving bracket:', error);
            });
    };

    // Load bracket - show modal with saved brackets
    const openLoadBracketModal = () => {
        console.log('Fetching saved brackets...');
        setLoadingBrackets(true);

        fetch('/api/saved-brackets')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    setSavedBrackets(data.brackets);
                    setShowModal(true);
                    console.log('Retrieved saved brackets:', data.brackets);
                } else {
                    alert('Error retrieving saved brackets: ' + data.error);
                    console.error('Error:', data.error);
                }
                setLoadingBrackets(false);
            })
            .catch(error => {
                alert('Error retrieving saved brackets. Please try again.');
                console.error('Error retrieving saved brackets:', error);
                setLoadingBrackets(false);
            });
    };

    // Load a specific bracket
    const loadBracket = (filename) => {
        console.log(`Loading bracket from ${filename}...`);

        fetch(`/api/load-bracket/${filename}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    setBracket(data.bracket);
                    setShowModal(false);

                    // Calculate and update completion status
                    const status = calculateCompletionStatus(data.bracket);
                    setCompletionStatus(status);
                    updateCompletionStatus(status);

                    // Update save status with 'loaded' message
                    const saveStatus = document.getElementById('save-status');
                    if (saveStatus) {
                        const now = new Date();
                        const timeString = now.toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit'
                        });
                        saveStatus.textContent = `📋 Loaded at: ${timeString}`;

                        // Add animation class for visual feedback
                        saveStatus.classList.add('saving');

                        // Remove animation class after animation completes
                        setTimeout(() => {
                            saveStatus.classList.remove('saving');
                        }, 2000);
                    }

                    alert('Bracket loaded successfully!');
                    console.log('Load success:', data.message);
                } else {
                    alert('Error loading bracket: ' + data.error);
                    console.error('Load error:', data.error);
                }
            })
            .catch(error => {
                alert('Error loading bracket. Please try again.');
                console.error('Error loading bracket:', error);
            });
    };

    // Handle Final Four Selection
    const handleFinalFourSelect = (semifinalIndex, teamIndex, region) => {
        console.log(`Final Four select: semifinalIndex=${semifinalIndex}, teamIndex=${teamIndex}, region=${region}`);

        // Exit if in read-only mode
        if (readOnly) {
            console.log('Cannot make changes in read-only mode');
            return;
        }

        // If the team is already in the finalFour array at the correct slot index, then we should be updating the Championship
        const slotIndex = getRegionFinalFourIndex(region);
        const currentTeam = bracket.finalFour[slotIndex];

        if (currentTeam) {
            // Determine which Championship slot this team should go to
            // South/west teams go to Championship slot 0, midwest/east go to slot 1
            const championshipSlot = (slotIndex === 1 || slotIndex === 2) ? 0 : 1;

            console.log(`Team already in Final Four, updating Championship: championshipSlot=${championshipSlot}, team=${currentTeam.name}`);

            // Call the update_championship action instead
            fetch('/api/bracket', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: 'update_championship',
                    ffIndex: slotIndex,
                    slotIndex: championshipSlot
                })
            })
                .then(response => {
                    console.log('Championship update response status:', response.status);
                    return response.json();
                })
                .then(data => {
                    console.log('Updated bracket after Championship selection:', data);
                    setBracket(data);

                    // Calculate and update completion status
                    const status = calculateCompletionStatus(data);
                    setCompletionStatus(status);
                    updateCompletionStatus(status);

                    // Update save status when Final Four changes (auto-save occurs)
                    updateSaveStatus();
                })
                .catch(error => console.error('Error updating bracket:', error));

            return;
        }

        // Otherwise, proceed with the Final Four update
        fetch('/api/bracket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'update_final_four',
                region: region,
                slotIndex: slotIndex,
                semifinalIndex: semifinalIndex,
                teamIndex: teamIndex
            })
        })
            .then(response => {
                console.log('Final Four update response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Updated bracket after Final Four selection:', data);
                setBracket(data);

                // Calculate and update completion status
                const status = calculateCompletionStatus(data);
                setCompletionStatus(status);
                updateCompletionStatus(status);

                // Update save status when Final Four changes (auto-save occurs)
                updateSaveStatus();
            })
            .catch(error => console.error('Error updating Final Four selection:', error));
    };

    // Handle Champion selection
    const handleChampionSelect = (slotIndex) => {
        console.log(`Champion select: slotIndex=${slotIndex}`);

        // Exit if in read-only mode
        if (readOnly) {
            console.log('Cannot make changes in read-only mode');
            return;
        }

        fetch('/api/bracket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'select_champion',
                slotIndex: slotIndex
            })
        })
            .then(response => {
                console.log('Champion selection response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Updated champion selection:', data);
                setBracket(data);

                // Calculate and update completion status
                const status = calculateCompletionStatus(data);
                setCompletionStatus(status);
                updateCompletionStatus(status);

                // Update save status when Champion changes (auto-save occurs)
                updateSaveStatus();
            })
            .catch(error => console.error('Error updating champion selection:', error));
    };

    // Handle Championship team selection
    const handleChampionshipSelect = (teamIndex) => {
        console.log(`Championship select: teamIndex=${teamIndex}`);

        // Exit if in read-only mode
        if (readOnly) {
            console.log('Cannot make changes in read-only mode');
            return;
        }

        // Check if there's already a team in this Championship slot
        const teamInSlot = bracket.championship[teamIndex];

        if (!teamInSlot) {
            console.log("No team in this Championship slot yet");
            return;
        }

        // If there is a team, check if it's already the champion
        if (bracket.champion === teamInSlot) {
            console.log("This team is already the champion, deselecting");
            // Call select_champion to toggle/deselect the champion
            fetch('/api/bracket', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: 'select_champion',
                    slotIndex: teamIndex
                })
            })
                .then(response => {
                    console.log('Champion selection response status:', response.status);
                    return response.json();
                })
                .then(data => {
                    console.log('Updated bracket after Champion deselection:', data);
                    setBracket(data);

                    // Calculate and update completion status
                    const status = calculateCompletionStatus(data);
                    setCompletionStatus(status);
                    updateCompletionStatus(status);

                    // Update save status when Championship changes (auto-save occurs)
                    updateSaveStatus();
                })
                .catch(error => console.error('Error selecting champion:', error));
        } else {
            // This team is not the champion yet, so select it
            console.log("Selecting this team as the champion");
            fetch('/api/bracket', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    action: 'select_champion',
                    slotIndex: teamIndex
                })
            })
                .then(response => {
                    console.log('Champion selection response status:', response.status);
                    return response.json();
                })
                .then(data => {
                    console.log('Updated bracket after Champion selection:', data);
                    setBracket(data);

                    // Calculate and update completion status
                    const status = calculateCompletionStatus(data);
                    setCompletionStatus(status);
                    updateCompletionStatus(status);

                    // Update save status when Championship changes (auto-save occurs)
                    updateSaveStatus();
                })
                .catch(error => console.error('Error selecting champion:', error));
        }
    };

    // Auto-fill the bracket
    const autoFillBracket = () => {
        // Exit if in read-only mode
        if (readOnly) {
            console.log('Cannot auto-fill in read-only mode');
            return;
        }

        fetch('/api/bracket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'auto_fill'
            })
        })
            .then(response => response.json())
            .then(data => {
                console.log('Auto-filled bracket:', data);
                setBracket(data);

                // Calculate and update completion status
                const status = calculateCompletionStatus(data);
                setCompletionStatus(status);
                updateCompletionStatus(status);

                updateSaveStatus();
            })
            .catch(error => console.error('Error auto-filling bracket:', error));
    };

    // Random-fill the bracket (completely random picks)
    const randomFillBracket = () => {
        // Exit if in read-only mode
        if (readOnly) {
            console.log('Cannot random-fill in read-only mode');
            return;
        }

        fetch('/api/bracket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'random_fill'
            })
        })
            .then(response => response.json())
            .then(data => {
                console.log('Random-filled bracket:', data);
                setBracket(data);

                // Calculate and update completion status
                const status = calculateCompletionStatus(data);
                setCompletionStatus(status);
                updateCompletionStatus(status);

                updateSaveStatus();
            })
            .catch(error => console.error('Error randomly filling bracket:', error));
    };

    // Reset the bracket
    const resetBracket = () => {
        // Exit if in read-only mode
        if (readOnly) {
            console.log('Cannot reset in read-only mode');
            return;
        }

        fetch('/api/bracket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'reset'
            })
        })
            .then(response => response.json())
            .then(data => {
                console.log('Reset bracket:', data);
                setBracket(data);

                // Calculate and update completion status
                const status = calculateCompletionStatus(data);
                setCompletionStatus(status);
                updateCompletionStatus(status);

                // Update save status for reset action
                const saveStatus = document.getElementById('save-status');
                if (saveStatus) {
                    const now = new Date();
                    const timeString = now.toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    });
                    saveStatus.textContent = `🔄 Reset at: ${timeString}`;

                    // Add animation class
                    saveStatus.classList.add('saving');

                    // Remove animation class after animation completes
                    setTimeout(() => {
                        saveStatus.classList.remove('saving');
                    }, 2000);
                }
            })
            .catch(error => console.error('Error resetting bracket:', error));
    };

    // Helper function to get the Final Four index for a region
    const getRegionFinalFourIndex = (region) => {
        switch (region) {
            case 'midwest': return 0;
            case 'west': return 1;
            case 'south': return 2;
            case 'east': return 3;
            default: return -1;
        }
    };

    // Render a team box
    const renderTeam = (team, isWinner, onClick, isTBD = false) => {
        // If no team data, return empty box with noticeable styling
        if (!team) {
            // Empty slot style with light red background and dashed red border
            const emptySlotStyle = {
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                padding: '4px 8px',
                margin: '1px 0',
                minHeight: '24px',
                width: '140px',
                fontSize: '11px',
                fontWeight: '400',
                backgroundColor: '#FFEBEE', // Light red background
                border: '1px dashed #EF9A9A', // Dashed red border
                borderRadius: '2px',
                cursor: onClick ? 'pointer' : 'default',
                color: '#D32F2F', // Deeper red text
                transition: 'all 0.2s ease'
            };

            return (
                <div style={emptySlotStyle} className="team tbd" onClick={onClick}>
                    <span style={{ fontStyle: 'italic' }}>&nbsp;</span>
                </div>
            );
        }

        // Get any server-provided classes for truth comparison
        const serverClasses = team.classes || '';

        // Check for bonus points - only show if greater than 0
        const hasBonus = team.bonus !== undefined && team.bonus > 0;
        const bonusValue = team.bonus;
        const bonusType = typeof team.bonus;
        const bonusText = hasBonus ? `+${team.bonus}` : '';
        const isReadOnly = readOnly || bracket.read_only === true;
        const showBonus = isReadOnly && serverClasses.includes('correct') && hasBonus;

        // Get shortened team name if available, otherwise use original name
        const displayName = teamNameShortcuts[team.name] || team.name;

        // Debug logging
        if (serverClasses.includes('correct')) {
            console.log('Correct team found:', team.name);
            console.log('  - hasBonus:', hasBonus);
            console.log('  - bonus value:', bonusValue);
            console.log('  - bonus type:', bonusType);
            console.log('  - bonus === undefined:', team.bonus === undefined);
            console.log('  - bonus == null:', team.bonus == null);
            console.log('  - isReadOnly:', isReadOnly);
            console.log('  - showBonus:', showBonus);
            console.log('  - complete team object:', JSON.stringify(team));
        }

        // Style for team boxes
        const teamStyle = {
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '4px 8px',
            margin: '1px 0',
            minHeight: '24px',
            width: '140px',
            fontSize: '11px',
            fontWeight: isTBD ? '300' : '400',
            backgroundColor: isTBD ? '#f0f0f0' : isWinner ? '#f0f8ff' : 'white',
            border: isWinner ? '1px solid #d0e0f0' : '1px solid #ddd',
            borderRadius: '2px',
            cursor: onClick ? 'pointer' : 'default',
            color: isTBD ? '#888' : '#333',
            boxShadow: isWinner ? '0 1px 2px rgba(0, 0, 100, 0.05)' : 'none',
            transition: 'all 0.2s ease',
            // Hover effect
            ':hover': onClick ? {
                backgroundColor: isWinner ? '#e8f4ff' : '#f5f5f5',
                borderColor: isWinner ? '#c0d8f0' : '#ccc',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            } : {}
        };

        // If it's a TBD placeholder
        if (isTBD) {
            return (
                <div style={teamStyle} className={`team tbd ${serverClasses}`}>
                    TBD
                </div>
            );
        }

        return (
            <div
                style={teamStyle}
                className={`team ${isWinner ? 'winner' : ''} ${serverClasses}`}
                onClick={onClick}
            >
                <div style={{ display: 'flex', alignItems: 'center' }}>
                    <div style={{
                        width: '16px',
                        height: '16px',
                        borderRadius: '50%',
                        backgroundColor: '#f2f2f2',
                        border: '1px solid #ddd',
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        marginRight: '6px',
                        fontSize: '9px',
                        fontWeight: 'bold'
                    }}>
                        {team.seed}
                    </div>
                    <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '100px' }}>
                        {displayName}
                        {showBonus && (
                            <span style={{ color: '#F9A825', fontWeight: 'bold', marginLeft: '3px' }}>
                                {bonusText}
                            </span>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    // Helper function to check if a team is a winner (using the backend data)
    const isTeamWinner = (region, round, teamIndex) => {
        if (!bracket.winners) return false;

        if (round < 4) {
            // Regular rounds (region-specific)
            return bracket.winners[region][round].includes(teamIndex);
        } else if (round === 4) {
            // Final Four
            return bracket.winners.finalFour.includes(teamIndex);
        } else if (round === 5) {
            // Championship
            return bracket.winners.championship.includes(teamIndex);
        }

        return false;
    };

    // Render a single game matchup
    const renderGame = (region, round, gameIndex, topTeam, bottomTeam, isRightRegion = false) => {
        // Get winner information from the backend data
        const topTeamIndex = gameIndex * 2;
        const bottomTeamIndex = gameIndex * 2 + 1;

        const isWinnerTop = isTeamWinner(region, round, topTeamIndex);
        const isWinnerBottom = isTeamWinner(region, round, bottomTeamIndex);

        // Add alternating background colors for first round games only
        const gameStyle = {};
        if (round === 0) {
            gameStyle.borderLeft = '6px solid #e0e0e0';  // Subtle border for visual indication
        }

        return (
            <div className="game" key={`game-${region}-${round}-${gameIndex}`} style={gameStyle}>
                {renderTeam(
                    topTeam,
                    isWinnerTop,
                    () => handleTeamSelect(region, round, gameIndex, 0),
                    false
                )}
                {renderTeam(
                    bottomTeam,
                    isWinnerBottom,
                    () => handleTeamSelect(region, round, gameIndex, 1),
                    false
                )}
            </div>
        );
    };

    // Calculate the appropriate spacing for games in each round
    const getGameWrapperStyle = (round, alignment, gameIndex) => {
        // Use CSS classes for spacing instead of absolute positioning
        return {
            position: 'relative',
            margin: '2px 0'
        };
    };

    // Render a full round of games for a region
    const renderRound = (region, round, alignment) => {
        const games = [];
        const gamesInRound = Math.pow(2, 3 - round);
        const isRightRegion = alignment === 'right';

        // Create a container style for proper positioning of rounds
        const roundContainerStyle = {
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
            width: '100%',
            justifyContent: 'space-around',
            height: round === 0 ? '600px' : '600px',  // consistent height for all rounds
        };

        // Defensive check to make sure bracket[region] and bracket[region][round] exist
        if (!bracket[region] || !bracket[region][round]) {
            console.error(`Missing data for ${region} region, round ${round}`);
            return (
                <div key={`round-${region}-${round}`} className={`round round-${alignment}`} data-round={round} style={roundContainerStyle}>
                    <div>Error: Missing data</div>
                </div>
            );
        }

        for (let i = 0; i < gamesInRound; i++) {
            const gameIndex = i;
            const topTeamIndex = gameIndex * 2;
            const bottomTeamIndex = gameIndex * 2 + 1;

            // Ensure these indices exist in the bracket data
            const topTeam = bracket[region][round][topTeamIndex] || null;
            const bottomTeam = bracket[region][round][bottomTeamIndex] || null;

            games.push(
                <div key={`${region}-${round}-${i}`} className="game-wrapper">
                    {renderGame(
                        region,
                        round,
                        gameIndex,
                        topTeam,
                        bottomTeam,
                        isRightRegion
                    )}
                </div>
            );
        }

        return (
            <div key={`round-${region}-${round}`} className={`round round-${alignment}`} data-round={round} style={roundContainerStyle}>
                {games}
            </div>
        );
    };

    // Render Final Four and Championship
    const renderFinalFour = () => {
        // Add more distinct styling and explicit z-indexing to ensure proper click handling
        const semifinalStyle = {
            position: 'relative',
            margin: '10px',
            padding: '10px',
            backgroundColor: '#f8f9fa',
            borderRadius: '6px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
            zIndex: 2
        };

        const championshipStyle = {
            position: 'relative',
            margin: '10px 20px',
            padding: '12px',
            backgroundColor: '#fff8e1',
            borderRadius: '6px',
            boxShadow: '0 3px 6px rgba(0,0,0,0.1)',
            border: '1px solid #ffe082',
            zIndex: 3
        };

        // Champion display box styling
        const championDisplayStyle = {
            margin: '0 auto 15px auto',
            padding: '15px',
            backgroundColor: '#f8f9fa', // Light gray background instead of green
            borderRadius: '8px',
            boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
            border: '2px solid #ccc', // Gray border instead of green
            textAlign: 'center',
            maxWidth: '200px'
        };

        // Create distinct onClick handlers for each position to aid debugging
        const handleSouthClick = () => {
            console.log("South team clicked in Final Four!");
            // South team will be in finalFour[2]
            if (bracket.finalFour && bracket.finalFour[2]) {
                // If team already exists, this should update the championship
                handleFinalFourSelect(0, 0, 'south');
            } else {
                // Otherwise, get the team from the Elite Eight
                handleFinalFourSelect(0, 0, 'south');
            }
        };

        const handlewestClick = () => {
            console.log("west team clicked in Final Four!");
            // west team will be in finalFour[1]
            if (bracket.finalFour && bracket.finalFour[1]) {
                // If team already exists, this should update the championship
                handleFinalFourSelect(0, 0, 'west');
            } else {
                // Otherwise, get the team from the Elite Eight
                handleFinalFourSelect(0, 0, 'west');
            }
        };

        const handleeastClick = () => {
            console.log("east team clicked in Final Four!");
            // east team will be in finalFour[3]
            if (bracket.finalFour && bracket.finalFour[3]) {
                // If team already exists, this should update the championship
                handleFinalFourSelect(1, 0, 'east');
            } else {
                // Otherwise, get the team from the Elite Eight
                handleFinalFourSelect(1, 0, 'east');
            }
        };

        const handlemidwestClick = () => {
            console.log("midwest team clicked in Final Four!");
            // midwest team will be in finalFour[0]
            if (bracket.finalFour && bracket.finalFour[0]) {
                // If team already exists, this should update the championship
                handleFinalFourSelect(1, 0, 'midwest');
            } else {
                // Otherwise, get the team from the Elite Eight
                handleFinalFourSelect(1, 0, 'midwest');
            }
        };

        const handleChampionship1Click = () => {
            console.log("Championship team 1 clicked!");
            handleChampionshipSelect(0);
        };

        const handleChampionship2Click = () => {
            console.log("Championship team 2 clicked!");
            handleChampionshipSelect(1);
        };

        const handleChampion1Select = () => {
            console.log("Champion slot 0 selected!");
            handleChampionSelect(0);
        };

        const handleChampion2Select = () => {
            console.log("Champion slot 1 selected!");
            handleChampionSelect(1);
        };

        // Get winner information from the backend data
        const isSouthWinner = bracket.winners && bracket.winners.finalFour && bracket.winners.finalFour.includes(2);
        const iswestWinner = bracket.winners && bracket.winners.finalFour && bracket.winners.finalFour.includes(1);
        const iseastWinner = bracket.winners && bracket.winners.finalFour && bracket.winners.finalFour.includes(3);
        const ismidwestWinner = bracket.winners && bracket.winners.finalFour && bracket.winners.finalFour.includes(0);

        // Check if teams are winners in Championship
        const isChamp1Winner = bracket.winners && bracket.winners.championship && bracket.winners.championship.includes(0);
        const isChamp2Winner = bracket.winners && bracket.winners.championship && bracket.winners.championship.includes(1);

        // Safely access Final Four and Championship data with fallbacks
        const finalFour = bracket.finalFour || [null, null, null, null];
        const championship = bracket.championship || [null, null];

        return (
            <div className="final-four" style={{ position: 'relative', zIndex: 1, top: 100 }}>
                <div className="final-four-content">
                    {/* Champion Display Box - Now positioned ABOVE the championship */}
                    <div style={championDisplayStyle}>
                        <div style={{ marginBottom: '10px' }}>
                            <span role="img" aria-label="trophy" style={{ fontSize: '24px' }}>🏆</span>
                            <div style={{ fontWeight: 'bold', fontSize: '16px', color: '#333' }}>Champion</div>
                        </div>
                        {bracket.champion ? (
                            <div style={{
                                padding: '10px',
                                backgroundColor: 'white',
                                borderRadius: '4px',
                                border: '1px solid #ccc', // Neutral gray border instead of green
                                cursor: 'pointer'
                            }}
                                className={bracket.champion.classes || ''}
                            >
                                <div style={{ fontWeight: 'bold', fontSize: '16px' }}>
                                    {teamNameShortcuts[bracket.champion.name] || bracket.champion.name} ({bracket.champion.seed})
                                </div>
                            </div>
                        ) : (
                            <div style={{
                                padding: '10px',
                                backgroundColor: '#FFEBEE', // Light red background
                                borderRadius: '4px',
                                border: '1px dashed #EF9A9A', // Dashed red border
                                minHeight: '24px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}>
                                <div style={{ fontSize: '16px', color: '#689F38', fontStyle: 'italic' }}>&nbsp;</div>
                            </div>
                        )}
                    </div>

                    {/* Display the Final Four matchups side by side in a pyramid structure */}
                    <div className="semifinal-container">
                        {/* Left side semifinal - South vs west */}
                        <div className="semifinal-matchup left-semifinal" style={semifinalStyle}>
                            <div style={{ textAlign: 'center', fontWeight: 'bold', marginBottom: '10px', fontSize: '14px' }}></div>
                            <div style={{ pointerEvents: 'auto' }}>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        finalFour[2], // South champion
                                        isSouthWinner,
                                        handleSouthClick,
                                        false
                                    )}
                                </div>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        finalFour[1], // west champion
                                        iswestWinner,
                                        handlewestClick,
                                        false
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Championship in the middle */}
                        <div className="championship-matchup" style={championshipStyle}>
                            <div style={{ textAlign: 'center', fontWeight: 'bold', marginBottom: '10px', color: '#bf8c00', fontSize: '16px' }}>Championship</div>
                            <div style={{ pointerEvents: 'auto' }}>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        championship[0], // Winner of South/west
                                        isChamp1Winner,
                                        handleChampionship1Click,
                                        false
                                    )}
                                </div>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        championship[1], // Winner of east/midwest
                                        isChamp2Winner,
                                        handleChampionship2Click,
                                        false
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Right side semifinal - east vs midwest */}
                        <div className="semifinal-matchup right-semifinal" style={semifinalStyle}>
                            <div style={{ textAlign: 'center', fontWeight: 'bold', marginBottom: '10px', fontSize: '14px' }}></div>
                            <div style={{ pointerEvents: 'auto' }}>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        finalFour[3], // east champion
                                        iseastWinner,
                                        handleeastClick,
                                        false
                                    )}
                                </div>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        finalFour[0], // midwest champion
                                        ismidwestWinner,
                                        handlemidwestClick,
                                        false
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    // Render the Round Headers
    const renderRoundHeaders = () => {
        return (
            <div className="round-headers">
                {/* Left side headers (South & west) - left to right flow */}
                <div className="round-header round-header-left" data-round="0">1st Round</div>
                <div className="round-header round-header-left" data-round="1">2nd Round</div>
                <div className="round-header round-header-left" data-round="2">Sweet 16</div>
                <div className="round-header round-header-left" data-round="3">Elite Eight</div>

                {/* Center section */}
                <div className="round-header round-header-center">Final Four</div>
                <div className="round-header round-header-center">Championship</div>
                <div className="round-header round-header-center">Final Four</div>

                {/* Right side headers (east & midwest) - right to left flow */}
                <div className="round-header round-header-right" data-round="3">Elite Eight</div>
                <div className="round-header round-header-right" data-round="2">Sweet 16</div>
                <div className="round-header round-header-right" data-round="1">2nd Round</div>
                <div className="round-header round-header-right" data-round="0">1st Round</div>
            </div>
        );
    };

    // Render the modal for loading brackets
    const renderSavedBracketsModal = () => {
        // Modal disabled as requested, but functionality code kept intact
        return null;

        // Original modal code below (kept for reference but won't execute)
        /* 
        if (!showModal) return null;

        // Styles for the modal
        const modalOverlayStyle = {
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            zIndex: 1000
        };
        */
        // ... existing code ...
    };

    // Main render method
    return (
        <div className="bracket-container">
            <div className="bracket-content">
                <div className="brackets-wrapper" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <div className="bracket">
                        <div className="bracket-left">
                            <div className="region south">
                                <div className="region-rounds">
                                    {renderRound('south', 0, 'left')}
                                    {renderRound('south', 1, 'left')}
                                    <div style={{ display: 'flex', flexDirection: 'column', minWidth: '140px', maxWidth: '140px', padding: '0 5px' }}>
                                        <div className="region-label-styled">South</div>
                                        {renderRound('south', 2, 'left')}
                                    </div>
                                    {renderRound('south', 3, 'left')}
                                </div>
                            </div>
                        </div>

                        <div className="bracket-center" style={{
                            flex: '1',
                            minWidth: '320px',
                            display: 'flex',
                            justifyContent: 'center',
                            position: 'relative'
                        }}>
                            <div className="center-wrapper" style={{
                                display: 'flex',
                                flexDirection: 'column',
                                justifyContent: 'center',
                                alignItems: 'center',
                                width: '100%',
                                height: '100%',
                                position: 'relative',
                                padding: '20px',
                                pointerEvents: 'all'
                            }}>
                                {renderFinalFour()}
                            </div>
                        </div>

                        <div className="bracket-right">
                            <div className="region east">
                                <div className="region-rounds" style={{ width: '100%', display: 'flex', justifyContent: 'flex-end' }}>
                                    {renderRound('east', 3, 'right')}
                                    <div style={{ display: 'flex', flexDirection: 'column', minWidth: '140px', maxWidth: '140px', padding: '0 5px', alignItems: 'flex-start' }}>
                                        <div className="region-label-styled">east</div>
                                        {renderRound('east', 2, 'right')}
                                    </div>
                                    {renderRound('east', 1, 'right')}
                                    {renderRound('east', 0, 'right')}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="bracket">
                        <div className="bracket-left">
                            <div className="region west">
                                <div className="region-rounds">
                                    {renderRound('west', 0, 'left')}
                                    {renderRound('west', 1, 'left')}
                                    <div style={{ display: 'flex', flexDirection: 'column', minWidth: '140px', maxWidth: '140px', padding: '0 5px' }}>
                                        <div className="region-label-styled">west</div>
                                        {renderRound('west', 2, 'left')}
                                    </div>
                                    {renderRound('west', 3, 'left')}
                                </div>
                            </div>
                        </div>

                        <div className="bracket-center" style={{
                            flex: '1',
                            minWidth: '340px',
                            display: 'flex',
                            justifyContent: 'center',
                            position: 'relative'
                        }}>
                            {/* Empty center space to align with top bracket */}
                        </div>

                        <div className="bracket-right">
                            <div className="region midwest">
                                <div className="region-rounds" style={{ width: '100%', display: 'flex', justifyContent: 'flex-end' }}>
                                    {renderRound('midwest', 3, 'right')}
                                    <div style={{ display: 'flex', flexDirection: 'column', minWidth: '140px', maxWidth: '140px', padding: '0 5px', alignItems: 'flex-start' }}>
                                        <div className="region-label-styled">midwest</div>
                                        {renderRound('midwest', 2, 'right')}
                                    </div>
                                    {renderRound('midwest', 1, 'right')}
                                    {renderRound('midwest', 0, 'right')}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {renderSavedBracketsModal()}
        </div>
    );
}

// Render the component to the DOM
ReactDOM.createRoot(document.getElementById('root')).render(<MarchMadnessBracket />); 