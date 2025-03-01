// Define the main Bracket component
function MarchMadnessBracket() {
    // Initialize the auto-fill flag
    window.lastActionWasAutoFill = false;

    const [teams, setTeams] = React.useState({
        west: [],
        east: [],
        south: [],
        midwest: []
    });
    const [bracket, setBracket] = React.useState({
        west: Array(4).fill().map(() => Array(8).fill(null)),
        east: Array(4).fill().map(() => Array(8).fill(null)),
        south: Array(4).fill().map(() => Array(8).fill(null)),
        midwest: Array(4).fill().map(() => Array(8).fill(null)),
        finalFour: [null, null, null, null],
        championship: [null, null],
        champion: null
    });

    // Fetch teams data from Flask backend
    React.useEffect(() => {
        fetch('/api/teams')
            .then(response => response.json())
            .then(data => {
                setTeams(data);

                // Initialize first round with teams
                const newBracket = { ...bracket };
                Object.keys(data).forEach(region => {
                    // Set initial matchups in first round (0-indexed)
                    // Game 0: 1 vs 16
                    newBracket[region][0][0] = data[region][0]; // 1 seed
                    newBracket[region][0][1] = data[region][1]; // 16 seed

                    // Game 1: 8 vs 9
                    newBracket[region][0][2] = data[region][2]; // 8 seed
                    newBracket[region][0][3] = data[region][3]; // 9 seed

                    // Game 2: 5 vs 12
                    newBracket[region][0][4] = data[region][4]; // 5 seed
                    newBracket[region][0][5] = data[region][5]; // 12 seed

                    // Game 3: 4 vs 13
                    newBracket[region][0][6] = data[region][6]; // 4 seed
                    newBracket[region][0][7] = data[region][7]; // 13 seed

                    // Game 4: 6 vs 11
                    newBracket[region][0][8] = data[region][8]; // 6 seed
                    newBracket[region][0][9] = data[region][9]; // 11 seed

                    // Game 5: 3 vs 14
                    newBracket[region][0][10] = data[region][10]; // 3 seed
                    newBracket[region][0][11] = data[region][11]; // 14 seed

                    // Game 6: 7 vs 10
                    newBracket[region][0][12] = data[region][12]; // 7 seed
                    newBracket[region][0][13] = data[region][13]; // 10 seed

                    // Game 7: 2 vs 15
                    newBracket[region][0][14] = data[region][14]; // 2 seed
                    newBracket[region][0][15] = data[region][15]; // 15 seed
                });

                setBracket(newBracket);
            })
            .catch(error => console.error('Error fetching teams:', error));
    }, []);

    // Function to handle team selection and advancement
    const handleTeamSelect = (region, round, gameIndex, teamIndex) => {
        // Create a deep copy of the bracket to avoid direct mutation
        const newBracket = JSON.parse(JSON.stringify(bracket));

        // Get the selected team
        const selectedTeam = newBracket[region][round][gameIndex * 2 + teamIndex];

        // Ensure a team was selected
        if (!selectedTeam) return;

        // Determine next round and game position
        const nextRound = round + 1;
        const nextGameIndex = Math.floor(gameIndex / 2);
        const nextTeamIndex = gameIndex % 2;
        const nextSlot = nextGameIndex * 2 + nextTeamIndex;

        // Check what team is currently in the next round's slot
        let teamInNextSlot = null;
        if (round < 3) {
            teamInNextSlot = bracket[region][nextRound][nextSlot];
        }

        // Handle regular bracket rounds (not Elite Eight)
        if (round < 3) {
            // If clicking the same team that's already in the next round, do nothing
            if (teamInNextSlot === selectedTeam) {
                return;
            }

            // Set the selected team in the next round
            newBracket[region][nextRound][nextSlot] = selectedTeam;

            // Debug statement to track team replacement
            console.log(`Setting ${selectedTeam && selectedTeam.name || 'TBD'} in ${region} round ${nextRound} slot ${nextSlot}, replacing ${teamInNextSlot && teamInNextSlot.name || 'TBD'}`);

            // If we're replacing a different team, we need to reset all instances of that team
            if (teamInNextSlot !== null && teamInNextSlot !== selectedTeam) {
                // Full reset cascade for the replaced team
                console.log(`RESETTING ${teamInNextSlot.name} from all subsequent rounds`);

                // This is a complete reset approach - check all later rounds in this region for the team
                resetTeamCompletely(newBracket, region, teamInNextSlot, nextRound);
            }
        }
        // Handle Elite Eight selections (to Final Four)
        else if (round === 3) {
            // Get the Final Four slot index for this region
            const ffIndex = getRegionFinalFourIndex(region);

            // Get current team in this Final Four slot
            const currentFinalFourTeam = bracket.finalFour[ffIndex];

            // If same team is already in Final Four, no need to change
            if (currentFinalFourTeam === selectedTeam) {
                return;
            }

            // Set the new Elite Eight winner in the Final Four
            newBracket.finalFour[ffIndex] = selectedTeam;

            console.log(`Setting ${selectedTeam && selectedTeam.name || 'TBD'} in Final Four slot ${ffIndex}, replacing ${currentFinalFourTeam && currentFinalFourTeam.name || 'TBD'}`);

            // If we're replacing a different team in the Final Four, we need to reset it from Championship and possibly the champion
            if (currentFinalFourTeam !== null && currentFinalFourTeam !== selectedTeam) {
                // Determine which Championship slot this affects
                const champIndex = ffIndex < 2 ? 0 : 1;

                // Check if the replaced team was in Championship
                if (bracket.championship[champIndex] === currentFinalFourTeam) {
                    console.log(`RESETTING ${currentFinalFourTeam.name} from Championship slot ${champIndex}`);
                    // Clear the Championship slot
                    newBracket.championship[champIndex] = null;

                    // Clear champion if needed
                    if (bracket.champion === currentFinalFourTeam) {
                        console.log(`RESETTING ${currentFinalFourTeam.name} from Champion`);
                        newBracket.champion = null;
                    }
                }
            }
        }

        // Update the bracket state
        setBracket(newBracket);
    };

    // Completely reset a team from all subsequent rounds - much more thorough approach
    const resetTeamCompletely = (bracketState, region, teamToReset, startRound) => {
        // Track all changes for debugging
        const changes = [];

        // Save the team name and seed for comparison
        const teamName = teamToReset.name;
        const teamSeed = teamToReset.seed;

        // Helper function to check if a team matches our target team
        const isMatchingTeam = (team) => {
            return team && team.name === teamName && team.seed === teamSeed;
        };

        // 1. Check all subsequent rounds in this region
        for (let round = startRound; round <= 3; round++) {
            // Scan every possible slot in this round
            for (let slot = 0; slot < bracketState[region][round].length; slot++) {
                if (isMatchingTeam(bracketState[region][round][slot])) {
                    // Found the team, clear it
                    bracketState[region][round][slot] = null;
                    changes.push(`Cleared ${teamName} from ${region} round ${round} slot ${slot}`);

                    // If this is the Elite Eight round, we also need to check Final Four
                    if (round === 3) {
                        const ffIndex = getRegionFinalFourIndex(region);

                        // Check if this team made it to Final Four
                        if (isMatchingTeam(bracketState.finalFour[ffIndex])) {
                            // Clear from Final Four
                            bracketState.finalFour[ffIndex] = null;
                            changes.push(`Cleared ${teamName} from Final Four slot ${ffIndex}`);

                            // Now check Championship
                            const champIndex = ffIndex < 2 ? 0 : 1;
                            if (isMatchingTeam(bracketState.championship[champIndex])) {
                                // Clear from Championship
                                bracketState.championship[champIndex] = null;
                                changes.push(`Cleared ${teamName} from Championship slot ${champIndex}`);

                                // Finally check if it was the champion
                                if (isMatchingTeam(bracketState.champion)) {
                                    bracketState.champion = null;
                                    changes.push(`Cleared ${teamName} from Champion`);
                                }
                            }
                        }
                    }
                }
            }
        }

        // 2. Also check Final Four directly
        for (let i = 0; i < bracketState.finalFour.length; i++) {
            if (isMatchingTeam(bracketState.finalFour[i])) {
                bracketState.finalFour[i] = null;
                changes.push(`Cleared ${teamName} from Final Four slot ${i}`);

                // Check Championship
                const champIndex = i < 2 ? 0 : 1;
                if (isMatchingTeam(bracketState.championship[champIndex])) {
                    bracketState.championship[champIndex] = null;
                    changes.push(`Cleared ${teamName} from Championship slot ${champIndex}`);

                    // Check Champion
                    if (isMatchingTeam(bracketState.champion)) {
                        bracketState.champion = null;
                        changes.push(`Cleared ${teamName} from Champion`);
                    }
                }
            }
        }

        // 3. Check Championship directly
        for (let i = 0; i < bracketState.championship.length; i++) {
            if (isMatchingTeam(bracketState.championship[i])) {
                bracketState.championship[i] = null;
                changes.push(`Cleared ${teamName} from Championship slot ${i}`);

                // Check Champion
                if (isMatchingTeam(bracketState.champion)) {
                    bracketState.champion = null;
                    changes.push(`Cleared ${teamName} from Champion`);
                }
            }
        }

        // 4. Finally check Champion directly
        if (isMatchingTeam(bracketState.champion)) {
            bracketState.champion = null;
            changes.push(`Cleared ${teamName} from Champion`);
        }

        // Log all the changes made for debugging
        if (changes.length > 0) {
            console.log("RESET CASCADE:", changes);
        } else {
            console.log(`No instances of ${teamName} found in later rounds`);
        }
    };

    // Find a team in a specific round and return its slot position (-1 if not found)
    const findTeamInRound = (regionBracket, round, team) => {
        for (let i = 0; i < regionBracket[round].length; i++) {
            if (regionBracket[round][i] === team) {
                return i;
            }
        }
        return -1;
    };

    // Helper function to get the Final Four index for a region
    const getRegionFinalFourIndex = (region) => {
        switch (region) {
            case 'west': return 0;
            case 'east': return 1;
            case 'south': return 2;
            case 'midwest': return 3;
            default: return -1;
        }
    };

    // Handle Final Four team selection
    const handleFinalFourSelect = (semifinalIndex, teamIndex) => {
        // Create a deep copy of the bracket state
        const newBracket = JSON.parse(JSON.stringify(bracket));

        // Determine which Final Four team is being selected and championship slot
        let finalFourIndex;
        let champIndex;

        if (semifinalIndex === 0) {
            // Left semifinal (South/East)
            finalFourIndex = teamIndex === 0 ? 2 : 1; // South or East
            champIndex = 0;
        } else {
            // Right semifinal (Midwest/West)
            finalFourIndex = teamIndex === 0 ? 3 : 0; // Midwest or West
            champIndex = 1;
        }

        // Get the selected team from the Final Four array
        const selectedTeam = bracket.finalFour[finalFourIndex];

        // Exit if no team available to select (prevent errors on empty slots)
        if (!selectedTeam) return;

        // Get the current team in the championship slot
        const currentChampionshipTeam = bracket.championship[champIndex];

        // Toggle behavior - if clicking the same team that's already in championship, clear it
        if (currentChampionshipTeam === selectedTeam) {
            // Clear the championship slot
            newBracket.championship[champIndex] = null;

            // If the champion was from this championship slot, clear it too
            if (bracket.champion === currentChampionshipTeam) {
                newBracket.champion = null;
            }
        } else {
            // Set the new team in the championship slot
            newBracket.championship[champIndex] = selectedTeam;

            // If the champion was from this championship slot, clear it since we've changed the team
            if (bracket.champion === currentChampionshipTeam) {
                newBracket.champion = null;
            }
        }

        // Update the bracket state
        setBracket(newBracket);
    };

    // Handle Championship team selection
    const handleChampionshipSelect = (teamIndex) => {
        // Create a deep copy of the bracket state
        const newBracket = JSON.parse(JSON.stringify(bracket));

        // Get the selected team from the championship array
        const selectedTeam = bracket.championship[teamIndex];

        // Exit if no team available to select
        if (!selectedTeam) return;

        // Get the current champion
        const currentChampion = bracket.champion;

        // Toggle behavior - if clicking the same team that's already champion, clear it
        if (currentChampion === selectedTeam) {
            // Clear the champion
            newBracket.champion = null;
        } else {
            // Set the new champion
            newBracket.champion = selectedTeam;
        }

        // Update the bracket state
        setBracket(newBracket);
    };

    // Render a single team box
    const renderTeam = (team, onClick, isWinner = false, isRightRegion = false, teamName = '') => {
        // Create a stable onClick handler even for TBD teams to help debugging
        const handleClick = (e) => {
            // Stop propagation to prevent parent elements from capturing the click
            e.stopPropagation();

            // Log the click for debugging
            if (team) {
                console.log(`Team clicked: ${team.name} (${team.seed})`);
            } else {
                console.log(`Empty team clicked (${teamName || 'TBD'})`);
                return; // Don't execute onClick for empty teams
            }

            // Execute the provided onClick handler
            if (onClick && typeof onClick === 'function') {
                onClick();
            }
        };

        if (!team) {
            return (
                <div
                    className="team tbd"
                    style={{
                        cursor: 'default',
                        padding: '4px 8px',
                        margin: '2px 0',
                        border: '1px dashed #ccc',
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        backgroundColor: '#f9f9f9',
                        color: '#999',
                        pointerEvents: 'auto'
                    }}
                    onClick={handleClick}
                >
                    <span className="seed"></span>
                    <span className="team-name">{teamName || 'TBD'}</span>
                </div>
            );
        }

        // Apply the winner class only if manually selected (not during auto-fill)
        // Check the global flag to determine if we're in an auto-fill operation
        const winnerClass = isWinner ? 'winner' : '';

        // Style to ensure all teams are clearly clickable
        const teamStyle = {
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            border: '1px solid #ccc',
            borderRadius: '4px',
            padding: '4px 8px',
            margin: '2px 0',
            display: 'flex',
            alignItems: 'center',
            backgroundColor: winnerClass ? '#e3f2fd' : '#fff',
            borderLeft: winnerClass ? '3px solid #2196F3' : '1px solid #ccc',
            boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
            pointerEvents: 'auto',
            position: 'relative',
            zIndex: 10  // Ensure team is above other elements
        };

        return (
            <div
                className={`team ${winnerClass}`}
                onClick={handleClick}
                style={teamStyle}
                onMouseOver={(e) => {
                    e.currentTarget.style.backgroundColor = '#f0f7ff';
                    e.currentTarget.style.borderColor = '#99c2ff';
                    e.currentTarget.style.boxShadow = '0 2px 5px rgba(0,0,0,0.1)';
                    e.currentTarget.style.transform = 'translateY(-1px)';
                }}
                onMouseOut={(e) => {
                    e.currentTarget.style.backgroundColor = winnerClass ? '#e3f2fd' : '#fff';
                    e.currentTarget.style.borderColor = winnerClass ? '#2196F3' : '#ccc';
                    e.currentTarget.style.borderLeftWidth = winnerClass ? '3px' : '1px';
                    e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.08)';
                    e.currentTarget.style.transform = 'translateY(0)';
                }}
            >
                <span className="seed">{team.seed}</span>
                <span className="team-name">{team.name}</span>
            </div>
        );
    };

    // Render a single game matchup
    const renderGame = (region, round, gameIndex, topTeam, bottomTeam, isRightRegion = false) => {
        const isWinnerTop = round < 3 && bracket[region][round + 1] &&
            bracket[region][round + 1][Math.floor(gameIndex / 2) * 2 + gameIndex % 2] === topTeam;

        const isWinnerBottom = round < 3 && bracket[region][round + 1] &&
            bracket[region][round + 1][Math.floor(gameIndex / 2) * 2 + gameIndex % 2] === bottomTeam;

        return (
            <div className="game">
                {renderTeam(
                    topTeam,
                    () => handleTeamSelect(region, round, gameIndex, 0),
                    isWinnerTop,
                    isRightRegion
                )}
                {renderTeam(
                    bottomTeam,
                    () => handleTeamSelect(region, round, gameIndex, 1),
                    isWinnerBottom,
                    isRightRegion
                )}
            </div>
        );
    };

    // Calculate the appropriate spacing for games in each round
    const getGameWrapperStyle = (round, alignment) => {
        // Base style for all game wrappers
        const baseStyle = {
            position: 'relative',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center'
        };

        // Specific margin adjustments for each round
        if (round === 0) {
            // First round needs minimal spacing
            return {
                ...baseStyle,
                marginBottom: '2px',
                marginTop: '2px'
            };
        }

        // Use the same spacing values for all regions for consistency
        const spacingMap = {
            1: 20, // 2nd round
            2: 60, // Sweet 16
            3: 140 // Elite 8
        };

        // Return style with appropriate vertical margins
        return {
            ...baseStyle,
            marginBottom: `${spacingMap[round]}px`,
            marginTop: `${spacingMap[round]}px`
        };
    };

    // Render a full round of games for a region
    const renderRound = (region, round, alignment) => {
        const games = [];
        const gamesInRound = Math.pow(2, 3 - round);
        const isRightRegion = alignment === 'right';

        for (let i = 0; i < gamesInRound; i++) {
            const gameIndex = i;
            const topTeamIndex = gameIndex * 2;
            const bottomTeamIndex = gameIndex * 2 + 1;

            games.push(
                <div key={`${region}-${round}-${i}`} className="game-wrapper" style={getGameWrapperStyle(round, alignment)}>
                    {renderGame(
                        region,
                        round,
                        gameIndex,
                        bracket[region][round][topTeamIndex],
                        bracket[region][round][bottomTeamIndex],
                        isRightRegion
                    )}
                </div>
            );
        }

        return (
            <div className={`round round-${alignment}`} data-round={round}>
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

        // Create distinct onClick handlers for each position to aid debugging
        const handleSouthClick = () => {
            console.log("South team clicked!");
            handleFinalFourSelect(0, 0);
        };

        const handleEastClick = () => {
            console.log("East team clicked!");
            handleFinalFourSelect(0, 1);
        };

        const handleMidwestClick = () => {
            console.log("Midwest team clicked!");
            handleFinalFourSelect(1, 0);
        };

        const handleWestClick = () => {
            console.log("West team clicked!");
            handleFinalFourSelect(1, 1);
        };

        const handleChampionship1Click = () => {
            console.log("Championship team 1 clicked!");
            handleChampionshipSelect(0);
        };

        const handleChampionship2Click = () => {
            console.log("Championship team 2 clicked!");
            handleChampionshipSelect(1);
        };

        return (
            <div className="final-four" style={{ position: 'relative', zIndex: 1 }}>
                <div className="final-four-content">
                    {/* Display the Final Four matchups side by side in a pyramid structure */}
                    <div className="semifinal-container">
                        {/* Left side semifinal - South vs East */}
                        <div className="semifinal-matchup left-semifinal" style={semifinalStyle}>
                            <div style={{ textAlign: 'center', fontWeight: 'bold', marginBottom: '10px', fontSize: '14px' }}>South/East Semifinal</div>
                            <div style={{ pointerEvents: 'auto' }}>
                                {/* Wrap each team in its own div with explicit pointer-events */}
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        bracket.finalFour[2], // South champion
                                        handleSouthClick,
                                        bracket.championship[0] === bracket.finalFour[2],
                                        false,
                                        "South Champion"
                                    )}
                                </div>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        bracket.finalFour[1], // East champion
                                        handleEastClick,
                                        bracket.championship[0] === bracket.finalFour[1],
                                        false,
                                        "East Champion"
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
                                        bracket.championship[0], // Winner of South/East
                                        handleChampionship1Click,
                                        bracket.champion === bracket.championship[0],
                                        false,
                                        "South/East Winner"
                                    )}
                                </div>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        bracket.championship[1], // Winner of Midwest/West
                                        handleChampionship2Click,
                                        bracket.champion === bracket.championship[1],
                                        false,
                                        "Midwest/West Winner"
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Right side semifinal - Midwest vs West */}
                        <div className="semifinal-matchup right-semifinal" style={semifinalStyle}>
                            <div style={{ textAlign: 'center', fontWeight: 'bold', marginBottom: '10px', fontSize: '14px' }}>Midwest/West Semifinal</div>
                            <div style={{ pointerEvents: 'auto' }}>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        bracket.finalFour[3], // Midwest champion
                                        handleMidwestClick,
                                        bracket.championship[1] === bracket.finalFour[3],
                                        false,
                                        "Midwest Champion"
                                    )}
                                </div>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        bracket.finalFour[0], // West champion
                                        handleWestClick,
                                        bracket.championship[1] === bracket.finalFour[0],
                                        false,
                                        "West Champion"
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
                {/* Left side headers (South & East) - left to right flow */}
                <div className="round-header round-header-left" data-round="0">1st Round</div>
                <div className="round-header round-header-left" data-round="1">2nd Round</div>
                <div className="round-header round-header-left" data-round="2">Sweet 16</div>
                <div className="round-header round-header-left" data-round="3">Elite Eight</div>

                {/* Center section */}
                <div className="round-header round-header-center">Final Four</div>
                <div className="round-header round-header-center">Championship</div>
                <div className="round-header round-header-center">Final Four</div>

                {/* Right side headers (Midwest & West) - right to left flow */}
                <div className="round-header round-header-right" data-round="3">Elite Eight</div>
                <div className="round-header round-header-right" data-round="2">Sweet 16</div>
                <div className="round-header round-header-right" data-round="1">2nd Round</div>
                <div className="round-header round-header-right" data-round="0">1st Round</div>
            </div>
        );
    };

    // Render the right regions (Midwest and West) with rounds in reverse order
    const renderRightRegion = (region, regionName) => {
        return (
            <div className="region-rounds" style={{ width: '100%', display: 'flex', justifyContent: 'flex-end' }}>
                {/* Render Elite 8 (Round 3) first - leftmost */}
                {renderRound(region, 3, 'right')}

                {/* Then Sweet 16 (Round 2) */}
                {renderRound(region, 2, 'right')}

                {/* Then 2nd Round (Round 1) */}
                {renderRound(region, 1, 'right')}

                {/* Then 1st Round (Round 0) last - rightmost */}
                {renderRound(region, 0, 'right')}
            </div>
        );
    };

    // Function to auto-fill the bracket selecting teams with lower seeds (or random if seeds are the same)
    const autoFillBracket = () => {
        // Set a flag to indicate this is an auto-fill action
        window.lastActionWasAutoFill = true;

        // Create a deep copy of the current bracket
        const newBracket = JSON.parse(JSON.stringify(bracket));

        // Process each region separately
        Object.keys(teams).forEach(region => {
            // Process rounds 0-3 (First Round through Elite Eight)
            for (let round = 0; round < 4; round++) {
                const gamesInRound = Math.pow(2, 3 - round);

                for (let gameIndex = 0; gameIndex < gamesInRound; gameIndex++) {
                    // Get the two teams in this matchup
                    let team1, team2;

                    if (round === 0) {
                        // First round - teams are already set
                        team1 = newBracket[region][round][gameIndex * 2];
                        team2 = newBracket[region][round][gameIndex * 2 + 1];
                    } else {
                        // Later rounds - need to get teams from previous round's winners
                        const prevRound = round - 1;
                        const team1Index = gameIndex * 2;
                        const team2Index = gameIndex * 2 + 1;

                        team1 = newBracket[region][round][team1Index];
                        team2 = newBracket[region][round][team2Index];
                    }

                    // Skip if either team is missing
                    if (!team1 || !team2) continue;

                    // Determine the winner based on seed
                    let winner;

                    if (parseInt(team1.seed) < parseInt(team2.seed)) {
                        // Team 1 has a lower seed (better)
                        winner = team1;
                    } else if (parseInt(team2.seed) < parseInt(team1.seed)) {
                        // Team 2 has a lower seed (better)
                        winner = team2;
                    } else {
                        // Seeds are the same, select randomly
                        winner = Math.random() < 0.5 ? team1 : team2;
                    }

                    // Set the winner in the next round
                    if (round < 3) {
                        // For rounds 0-2, advance to the next round in the same region
                        const nextRound = round + 1;
                        const nextGameIndex = Math.floor(gameIndex / 2);
                        const nextTeamIndex = gameIndex % 2;

                        newBracket[region][nextRound][nextGameIndex * 2 + nextTeamIndex] = winner;
                    } else {
                        // For Elite Eight (round 3), advance to Final Four
                        const ffIndex = getRegionFinalFourIndex(region);
                        newBracket.finalFour[ffIndex] = winner;
                    }
                }
            }
        });

        // Process Final Four (semifinal matchups)
        for (let semifinalIndex = 0; semifinalIndex < 2; semifinalIndex++) {
            let team1, team2;

            if (semifinalIndex === 0) {
                // South vs East
                team1 = newBracket.finalFour[0]; // South
                team2 = newBracket.finalFour[1]; // East
            } else {
                // Midwest vs West
                team1 = newBracket.finalFour[2]; // Midwest
                team2 = newBracket.finalFour[3]; // West
            }

            // Make sure we have both teams before determining a winner
            if (team1 && team2) {
                // Determine the winner based on seed
                let winner;

                if (parseInt(team1.seed) < parseInt(team2.seed)) {
                    winner = team1;
                } else if (parseInt(team2.seed) < parseInt(team1.seed)) {
                    winner = team2;
                } else {
                    // Seeds are the same, select randomly
                    winner = Math.random() < 0.5 ? team1 : team2;
                }

                // Set the winner in the championship
                newBracket.championship[semifinalIndex] = winner;
            }
        }

        // Process Championship
        const team1 = newBracket.championship[0];
        const team2 = newBracket.championship[1];

        // Make sure we have both teams before determining a champion
        if (team1 && team2) {
            // Determine the winner based on seed
            let winner;

            if (parseInt(team1.seed) < parseInt(team2.seed)) {
                winner = team1;
            } else if (parseInt(team2.seed) < parseInt(team1.seed)) {
                winner = team2;
            } else {
                // Seeds are the same, select randomly
                winner = Math.random() < 0.5 ? team1 : team2;
            }

            // Set the champion
            newBracket.champion = winner;
        }

        // Update the bracket state all at once
        setBracket(newBracket);

        // Reset the flag after a delay
        setTimeout(() => {
            window.lastActionWasAutoFill = false;
        }, 300); // Increased from 200ms to 300ms to ensure it catches all renders
    };

    // Debug function to help troubleshoot and verify bracket state
    const debugBracket = () => {
        console.log("=== BRACKET DEBUG INFO ===");
        console.log("Final Four Teams:", bracket.finalFour.map(t => t ? `${t.name} (${t.seed})` : 'null'));
        console.log("Championship Teams:", bracket.championship.map(t => t ? `${t.name} (${t.seed})` : 'null'));
        console.log("Champion:", bracket.champion ? `${bracket.champion.name} (${bracket.champion.seed})` : 'null');

        // Get a specific team to use for path testing
        console.log("\n--- TEAM PATH TEST ---");
        const testTeam = {
            name: prompt("Enter team name to trace (e.g., Alabama):") || "Alabama",
            seed: parseInt(prompt("Enter team seed (e.g., 1):") || "1")
        };

        console.log(`Tracing all instances of ${testTeam.name} (${testTeam.seed}):`);

        // Helper to check if a team matches our test team
        const isMatchingTeam = (team) => {
            return team && team.name === testTeam.name && team.seed === testTeam.seed;
        };

        let foundLocations = [];

        // Check all regions and rounds
        Object.keys(bracket).forEach(region => {
            // Skip non-region properties
            if (!Array.isArray(bracket[region]) || !Array.isArray(bracket[region][0])) return;

            // Check each round in this region
            for (let round = 0; round <= 3; round++) {
                for (let slot = 0; slot < bracket[region][round].length; slot++) {
                    if (isMatchingTeam(bracket[region][round][slot])) {
                        foundLocations.push(`Region: ${region}, Round: ${round}, Slot: ${slot}`);
                    }
                }
            }
        });

        // Check Final Four
        for (let i = 0; i < bracket.finalFour.length; i++) {
            if (isMatchingTeam(bracket.finalFour[i])) {
                foundLocations.push(`Final Four slot ${i} (${getRegionNameFromFinalFourIndex(i)})`);
            }
        }

        // Check Championship
        for (let i = 0; i < bracket.championship.length; i++) {
            if (isMatchingTeam(bracket.championship[i])) {
                foundLocations.push(`Championship slot ${i}`);
            }
        }

        // Check Champion
        if (isMatchingTeam(bracket.champion)) {
            foundLocations.push('Champion');
        }

        // Display results
        if (foundLocations.length > 0) {
            console.log(`Found ${testTeam.name} at the following locations:`);
            foundLocations.forEach(loc => console.log(` - ${loc}`));

            // Test what would happen with a reset
            console.log("\nIf we changed this team in round 1, these locations would be reset:");
            foundLocations.forEach(loc => console.log(` - ${loc}`));
        } else {
            console.log(`No instances of ${testTeam.name} found in the bracket`);
        }

        // Now test an actual reset scenario
        console.log("\n--- RESET SIMULATION TEST ---");
        // Get a team from the first round that we want to replace
        const testRegion = 'south';
        const testRound = 0; // First round
        const testGameIndex = 0;
        const testTeamIndex = 0;
        const oldTeam = bracket[testRegion][testRound][testGameIndex * 2 + testTeamIndex];

        if (oldTeam) {
            console.log(`Testing reset cascade if we change ${oldTeam.name} (${oldTeam.seed}) in ${testRegion} round ${testRound}...`);

            // Helper to check if a team matches our old team
            const matchesOldTeam = (team) => {
                return team && team.name === oldTeam.name && team.seed === oldTeam.seed;
            };

            // Find all instances of the old team in later rounds
            let oldTeamLocations = [];

            // Check later rounds in this region
            for (let round = testRound + 1; round <= 3; round++) {
                for (let slot = 0; slot < bracket[testRegion][round].length; slot++) {
                    if (matchesOldTeam(bracket[testRegion][round][slot])) {
                        oldTeamLocations.push(`Region: ${testRegion}, Round: ${round}, Slot: ${slot}`);
                    }
                }
            }

            // Check Final Four if applicable
            const ffIndex = getRegionFinalFourIndex(testRegion);
            if (matchesOldTeam(bracket.finalFour[ffIndex])) {
                oldTeamLocations.push(`Final Four slot ${ffIndex} (${getRegionNameFromFinalFourIndex(ffIndex)})`);

                // Check Championship
                const champIndex = ffIndex < 2 ? 0 : 1;
                if (matchesOldTeam(bracket.championship[champIndex])) {
                    oldTeamLocations.push(`Championship slot ${champIndex}`);

                    // Check Champion
                    if (matchesOldTeam(bracket.champion)) {
                        oldTeamLocations.push('Champion');
                    }
                }
            }

            // Display reset results
            if (oldTeamLocations.length > 0) {
                console.log(`The reset would clear ${oldTeam.name} from these locations:`);
                oldTeamLocations.forEach(loc => console.log(` - ${loc}`));
            } else {
                console.log(`${oldTeam.name} was not found in any later rounds`);
            }
        } else {
            console.log("No team found in test position");
        }

        console.log("=== END DEBUG INFO ===");
    };

    // Helper function to get a region name from Final Four index
    const getRegionNameFromFinalFourIndex = (index) => {
        switch (index) {
            case 0: return 'West';
            case 1: return 'East';
            case 2: return 'South';
            case 3: return 'Midwest';
            default: return 'Unknown';
        }
    };

    // Main render method
    return (
        <div className="bracket-container">
            <div className="bracket-content">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
                    <div>
                        <button
                            onClick={autoFillBracket}
                            style={{
                                padding: '8px 16px',
                                backgroundColor: '#003478',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontWeight: 'bold',
                                fontSize: '14px',
                                marginRight: '10px'
                            }}
                        >
                            Auto-Fill Bracket (Lower Seeds Win)
                        </button>

                        <button
                            onClick={debugBracket}
                            style={{
                                padding: '8px 16px',
                                backgroundColor: '#6c757d',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontWeight: 'bold',
                                fontSize: '14px'
                            }}
                        >
                            Debug Bracket
                        </button>
                    </div>
                </div>

                {renderRoundHeaders()}

                <div className="brackets-wrapper" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <div className="bracket">
                        <div className="bracket-left">
                            <div className="region south">
                                <div className="region-rounds">
                                    {renderRound('south', 0, 'left')}
                                    {renderRound('south', 1, 'left')}
                                    <div style={{ display: 'flex', flexDirection: 'column', minWidth: '140px', maxWidth: '140px', padding: '0 5px' }}>
                                        <div className="region-label" style={{ marginBottom: '15px', marginTop: '15px' }}>South</div>
                                        {renderRound('south', 2, 'left')}
                                    </div>
                                    {renderRound('south', 3, 'left')}
                                </div>
                            </div>
                        </div>

                        <div className="bracket-center" style={{
                            flex: '1',
                            minWidth: '400px',
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
                            <div className="region midwest">
                                <div className="region-rounds" style={{ width: '100%', display: 'flex', justifyContent: 'flex-end' }}>
                                    {renderRound('midwest', 3, 'right')}
                                    <div style={{ display: 'flex', flexDirection: 'column', minWidth: '140px', maxWidth: '140px', padding: '0 5px', alignItems: 'flex-start' }}>
                                        <div className="region-label" style={{ marginBottom: '15px', marginTop: '15px' }}>Midwest</div>
                                        {renderRound('midwest', 2, 'right')}
                                    </div>
                                    {renderRound('midwest', 1, 'right')}
                                    {renderRound('midwest', 0, 'right')}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="bracket">
                        <div className="bracket-left">
                            <div className="region east">
                                <div className="region-rounds">
                                    {renderRound('east', 0, 'left')}
                                    {renderRound('east', 1, 'left')}
                                    <div style={{ display: 'flex', flexDirection: 'column', minWidth: '140px', maxWidth: '140px', padding: '0 5px' }}>
                                        <div className="region-label" style={{ marginBottom: '15px', marginTop: '15px' }}>East</div>
                                        {renderRound('east', 2, 'left')}
                                    </div>
                                    {renderRound('east', 3, 'left')}
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
                            <div className="region west">
                                <div className="region-rounds" style={{ width: '100%', display: 'flex', justifyContent: 'flex-end' }}>
                                    {renderRound('west', 3, 'right')}
                                    <div style={{ display: 'flex', flexDirection: 'column', minWidth: '140px', maxWidth: '140px', padding: '0 5px', alignItems: 'flex-start' }}>
                                        <div className="region-label" style={{ marginBottom: '15px', marginTop: '15px' }}>West</div>
                                        {renderRound('west', 2, 'right')}
                                    </div>
                                    {renderRound('west', 1, 'right')}
                                    {renderRound('west', 0, 'right')}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Render the component to the DOM
ReactDOM.createRoot(document.getElementById('root')).render(<MarchMadnessBracket />); 