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

        // Get the previously selected team at this position (if any)
        const previousTeam = bracket[region][round][gameIndex * 2 + teamIndex];

        // If we're selecting the same team that's already selected, no need to change anything
        if (previousTeam === selectedTeam) return;

        // Determine next round and game position
        const nextRound = round + 1;
        const nextGameIndex = Math.floor(gameIndex / 2);
        const nextTeamIndex = gameIndex % 2;
        const nextSlot = nextGameIndex * 2 + nextTeamIndex;

        // Check if this team is already selected in the next round
        // If the same team is already in the next round, don't make any changes
        if (round < 3 && bracket[region][nextRound][nextSlot] === selectedTeam) {
            return; // Already selected this team to win, so don't change anything
        }

        // STEP 1: Set the selected team in the next round
        if (round < 3) { // If not yet at Elite Eight
            // Get the team that was previously in the next round (if any)
            const prevNextRoundTeam = bracket[region][nextRound][nextSlot];

            // Set the selected team in the next round
            newBracket[region][nextRound][nextSlot] = selectedTeam;

            // STEP 2: Only clear subsequent rounds if the team in the next round is changing
            if (prevNextRoundTeam !== selectedTeam) {
                // We only need to check subsequent rounds if we changed a team
                for (let r = nextRound + 1; r < 4; r++) {
                    // Calculate which position in each subsequent round would be affected
                    const affectedGameIdx = Math.floor(nextGameIndex / Math.pow(2, r - nextRound));
                    const affectedTeamIdx = (nextGameIndex / Math.pow(2, r - nextRound)) % 1 > 0 ? 1 : 0;
                    const affectedSlot = affectedGameIdx * 2 + affectedTeamIdx;

                    // Only clear if the team in that position is the one that's no longer advancing
                    if (bracket[region][r][affectedSlot] === prevNextRoundTeam) {
                        newBracket[region][r][affectedSlot] = null;
                    } else if (bracket[region][r][affectedSlot] !== null) {
                        // If some other team is already there, we don't need to continue clearing
                        // because the bracket has already been modified to have a different path
                        break;
                    }
                }

                // STEP 3: Check if this affects the Final Four
                // Only check if we've changed a team in the Elite Eight (round 3)
                if (nextRound === 3 && bracket[region][3][nextSlot] !== selectedTeam) {
                    // Get the Final Four index for this region
                    const ffIndex = getRegionFinalFourIndex(region);

                    // Only clear the Final Four slot if it contains the previous team
                    if (bracket.finalFour[ffIndex] === bracket[region][3][nextSlot]) {
                        const finalFourTeam = bracket.finalFour[ffIndex];

                        // Clear the Final Four slot
                        newBracket.finalFour[ffIndex] = null;

                        // STEP 4: Check if this affects the Championship
                        // Determine which half of the bracket this region belongs to
                        const champIndex = ffIndex < 2 ? 0 : 1;

                        // Only clear the championship slot if it contains the team being removed
                        if (bracket.championship[champIndex] === finalFourTeam) {
                            // Clear the championship slot
                            newBracket.championship[champIndex] = null;

                            // If the champion was this team, clear it too
                            if (bracket.champion === finalFourTeam) {
                                newBracket.champion = null;
                            }
                        }
                    }
                }
            }
        }
        // STEP 6: Handle Elite Eight (round 3) to Final Four advancement
        else if (round === 3) {
            // Get the Final Four slot index for this region
            const ffIndex = getRegionFinalFourIndex(region);

            // Get the current team in this Final Four slot (if any)
            const currentFinalFourTeam = bracket.finalFour[ffIndex];

            // Update the Final Four with the selected Elite Eight winner
            newBracket.finalFour[ffIndex] = selectedTeam;

            // If there was a team in this Final Four slot and it's different from the new selection
            if (currentFinalFourTeam && currentFinalFourTeam !== selectedTeam) {
                // Determine which side of the Championship bracket this affects
                const champIndex = ffIndex < 2 ? 0 : 1;

                // If the team being replaced was in the Championship, clear it
                if (bracket.championship[champIndex] === currentFinalFourTeam) {
                    // Clear the Championship slot
                    newBracket.championship[champIndex] = null;

                    // If the Champion is the team being replaced, clear that too
                    if (bracket.champion === currentFinalFourTeam) {
                        newBracket.champion = null;
                    }
                }
            }
        }

        // Update the bracket state
        setBracket(newBracket);
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

        // Get the selected team
        const selectedTeam = bracket.finalFour[finalFourIndex];

        // Exit if no team available to select
        if (!selectedTeam) return;

        // Get the current team in the championship slot
        const currentChampionshipTeam = bracket.championship[champIndex];

        // ALWAYS clear the championship slot when making a new selection
        newBracket.championship[champIndex] = null;

        // If the champion was the team that was in this championship slot, clear it too
        if (bracket.champion === currentChampionshipTeam) {
            newBracket.champion = null;
        }

        // If the user clicked the same team that's already selected, don't set it again
        // This effectively toggles the selection off if clicking the same team
        if (currentChampionshipTeam === selectedTeam) {
            // Keep it cleared
        } else {
            // Set the new team in the championship slot
            newBracket.championship[champIndex] = selectedTeam;
        }

        setBracket(newBracket);
    };

    // Handle Championship team selection
    const handleChampionshipSelect = (teamIndex) => {
        // Create a deep copy of the bracket state
        const newBracket = JSON.parse(JSON.stringify(bracket));

        // Get the selected team
        const selectedTeam = bracket.championship[teamIndex];

        // Exit if no team available to select
        if (!selectedTeam) return;

        // Get the current champion
        const currentChampion = bracket.champion;

        // ALWAYS clear the champion first
        newBracket.champion = null;

        // If the user clicked the same team that's already the champion, don't set it again
        // This effectively toggles the selection off if clicking the same team
        if (currentChampion !== selectedTeam) {
            // Set the new champion
            newBracket.champion = selectedTeam;
        }

        setBracket(newBracket);
    };

    // Render a single team box
    const renderTeam = (team, onClick, isWinner = false, isRightRegion = false) => {
        if (!team) {
            return (
                <div className="team tbd">
                    <span className="seed"></span>
                    <span className="team-name">TBD</span>
                </div>
            );
        }

        // Apply the winner class only if manually selected (not during auto-fill)
        // Check the global flag to determine if we're in an auto-fill operation
        const winnerClass = isWinner && !window.lastActionWasAutoFill ? 'winner' : '';

        return (
            <div
                className={`team ${winnerClass}`}
                onClick={onClick}
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
        return (
            <div className="final-four">
                <div className="final-four-content">
                    {/* Display the Final Four matchups side by side in a pyramid structure */}
                    <div className="semifinal-container">
                        {/* Left side semifinal - South vs East */}
                        <div className="semifinal-matchup left-semifinal">
                            {renderTeam(
                                bracket.finalFour[2], // South champion
                                () => handleFinalFourSelect(0, 0),
                                bracket.championship[0] === bracket.finalFour[2]
                            )}
                            {renderTeam(
                                bracket.finalFour[1], // East champion
                                () => handleFinalFourSelect(0, 1),
                                bracket.championship[0] === bracket.finalFour[1]
                            )}
                        </div>

                        {/* Championship in the middle */}
                        <div className="championship-matchup">
                            {renderTeam(
                                bracket.championship[0], // Winner of South/East
                                () => handleChampionshipSelect(0),
                                bracket.champion === bracket.championship[0]
                            )}
                            {renderTeam(
                                bracket.championship[1], // Winner of Midwest/West
                                () => handleChampionshipSelect(1),
                                bracket.champion === bracket.championship[1]
                            )}
                        </div>

                        {/* Right side semifinal - Midwest vs West */}
                        <div className="semifinal-matchup right-semifinal">
                            {renderTeam(
                                bracket.finalFour[3], // Midwest champion
                                () => handleFinalFourSelect(1, 0),
                                bracket.championship[1] === bracket.finalFour[3]
                            )}
                            {renderTeam(
                                bracket.finalFour[0], // West champion
                                () => handleFinalFourSelect(1, 1),
                                bracket.championship[1] === bracket.finalFour[0]
                            )}
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
                    const team1Index = gameIndex * 2;
                    const team2Index = gameIndex * 2 + 1;

                    const team1 = round === 0 ?
                        newBracket[region][round][team1Index] :
                        newBracket[region][round - 1][team1Index * 2];

                    const team2 = round === 0 ?
                        newBracket[region][round][team2Index] :
                        newBracket[region][round - 1][team2Index * 2];

                    // Make sure we have both teams before determining a winner
                    if (team1 && team2) {
                        // Determine the winner based on seed
                        let winner;

                        if (team1.seed < team2.seed) {
                            // Team 1 has a lower seed
                            winner = team1;
                        } else if (team2.seed < team1.seed) {
                            // Team 2 has a lower seed
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
            }
        });

        // Process Final Four (semifinal matchups)
        for (let semifinalIndex = 0; semifinalIndex < 2; semifinalIndex++) {
            let team1, team2;

            if (semifinalIndex === 0) {
                // South vs East
                team1 = newBracket.finalFour[2]; // South
                team2 = newBracket.finalFour[1]; // East
            } else {
                // Midwest vs West
                team1 = newBracket.finalFour[3]; // Midwest
                team2 = newBracket.finalFour[0]; // West
            }

            // Make sure we have both teams before determining a winner
            if (team1 && team2) {
                // Determine the winner based on seed
                let winner;

                if (team1.seed < team2.seed) {
                    winner = team1;
                } else if (team2.seed < team1.seed) {
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

            if (team1.seed < team2.seed) {
                winner = team1;
            } else if (team2.seed < team1.seed) {
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

        // Reset the flag after a short delay to ensure the current render completes
        // This is important for subsequent manual selections to be properly highlighted
        setTimeout(() => {
            window.lastActionWasAutoFill = false;
        }, 100);
    };

    // Main render method
    return (
        <div className="bracket-container">
            <div className="bracket-content">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
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
                            fontSize: '14px'
                        }}
                    >
                        Auto-Fill Bracket (Lower Seeds Win)
                    </button>

                    {/* Champion display at the top */}
                    {bracket.champion && (
                        <div style={{
                            padding: '8px 16px',
                            backgroundColor: '#f5f5f5',
                            border: '1px solid #ddd',
                            borderRadius: '4px',
                            fontWeight: 'bold',
                            fontSize: '14px',
                            color: '#003478'
                        }}>
                            Champion: {bracket.champion.name} ({bracket.champion.seed})
                        </div>
                    )}
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
                            minWidth: '340px',
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
                                position: 'absolute',
                                top: '50%',  // Position from the middle of the container
                                transform: 'translateY(0)', // Change from 25% to 0 to truly center it
                                left: 0,
                                right: 0
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