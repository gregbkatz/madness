// Define the main Bracket component
function MarchMadnessBracket() {
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
        // Create a deep copy of the bracket
        const newBracket = JSON.parse(JSON.stringify(bracket));

        // Get the selected team
        const selectedTeam = newBracket[region][round][gameIndex * 2 + teamIndex];

        // Ensure a team was selected
        if (!selectedTeam) return;

        // Determine next round and game index
        const nextRound = round + 1;
        const nextGameIndex = Math.floor(gameIndex / 2);
        const nextTeamIndex = gameIndex % 2;

        // Update the next round with the selected team if within regional rounds (0-3)
        if (nextRound < 4) {
            // Store the currently selected team at this position (if any)
            const previousSelectedTeam = bracket[region][nextRound][nextGameIndex * 2 + nextTeamIndex];

            // Update with the newly selected team
            newBracket[region][nextRound][nextGameIndex * 2 + nextTeamIndex] = selectedTeam;

            // Clear subsequent rounds that might be affected by this change
            for (let r = nextRound + 1; r < 4; r++) {
                const gameIdx = Math.floor(nextGameIndex / Math.pow(2, r - nextRound));
                const teamIdx = (nextGameIndex / Math.pow(2, r - nextRound)) % 1 > 0 ? 1 : 0;
                newBracket[region][r][gameIdx * 2 + teamIdx] = null;
            }

            // Check if the previously selected team reached the Final Four
            const regionFinalFourIndex = getRegionFinalFourIndex(region);
            if (previousSelectedTeam && nextRound === 3 && bracket[region][3][0] === previousSelectedTeam) {
                // Clear the team from Final Four
                newBracket.finalFour[regionFinalFourIndex] = null;

                // Clear championship if necessary
                if (bracket.championship[0] === previousSelectedTeam) {
                    newBracket.championship[0] = null;
                } else if (bracket.championship[1] === previousSelectedTeam) {
                    newBracket.championship[1] = null;
                }

                // Clear champion if necessary
                if (bracket.champion === previousSelectedTeam) {
                    newBracket.champion = null;
                }
            }

            // If team in Elite Eight changes, ensure Final Four is cleared
            if (nextRound === 3 || round === 3) {
                const regionFinalFourIndex = getRegionFinalFourIndex(region);
                newBracket.finalFour[regionFinalFourIndex] = null;

                // Clear championship and champion if affected
                if (regionFinalFourIndex === 0 || regionFinalFourIndex === 1) {
                    newBracket.championship[0] = null;
                } else {
                    newBracket.championship[1] = null;
                }

                // Always clear champion when Elite Eight changes
                newBracket.champion = null;
            }
        }
        // Handle Elite Eight to Final Four advancement
        else if (round === 3) {
            // Update Final Four based on region
            const regionFinalFourIndex = getRegionFinalFourIndex(region);
            newBracket.finalFour[regionFinalFourIndex] = selectedTeam;

            // Clear championship if relevant Final Four team changes
            if (regionFinalFourIndex === 0 || regionFinalFourIndex === 1) {
                newBracket.championship[0] = null;
            } else {
                newBracket.championship[1] = null;
            }

            // Clear champion
            newBracket.champion = null;
        }

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
        // Create a copy of the bracket state
        const newBracket = JSON.parse(JSON.stringify(bracket));

        // Get the selected team from the Final Four
        let selectedTeam;

        if (semifinalIndex === 0) {
            // Left semifinal (South/East)
            selectedTeam = teamIndex === 0 ? bracket.finalFour[2] : bracket.finalFour[1];
            newBracket.championship[0] = selectedTeam;
        } else {
            // Right semifinal (Midwest/West)
            selectedTeam = teamIndex === 0 ? bracket.finalFour[3] : bracket.finalFour[0];
            newBracket.championship[1] = selectedTeam;
        }

        if (!selectedTeam) return;

        // Clear champion if championship teams change
        newBracket.champion = null;

        setBracket(newBracket);
    };

    // Handle Championship team selection
    const handleChampionshipSelect = (teamIndex) => {
        if (!bracket.championship[teamIndex]) return;

        const newBracket = { ...bracket };
        newBracket.champion = bracket.championship[teamIndex];
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

        return (
            <div
                className={`team ${isWinner ? 'winner' : ''}`}
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

                    {/* Champion display - always visible */}
                    <div className="champion-display">
                        <div className="champion-label">CHAMPION</div>
                        <div className="champion-name">
                            {bracket.champion ? bracket.champion.name : "TBD"}
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

    // Main render method
    return (
        <div className="bracket-container">
            <div className="bracket-content">
                {renderRoundHeaders()}

                <div className="bracket">
                    <div className="bracket-left">
                        <div className="region south">
                            <div className="region-label">South</div>
                            <div className="region-rounds">
                                {renderRound('south', 0, 'left')}
                                {renderRound('south', 1, 'left')}
                                {renderRound('south', 2, 'left')}
                                {renderRound('south', 3, 'left')}
                            </div>
                        </div>
                    </div>

                    <div className="bracket-center">
                        {renderFinalFour()}
                    </div>

                    <div className="bracket-right">
                        <div className="region midwest">
                            <div className="region-label">Midwest</div>
                            {renderRightRegion('midwest', 'Midwest')}
                        </div>
                    </div>
                </div>

                <div className="bracket">
                    <div className="bracket-left">
                        <div className="region east">
                            <div className="region-label">East</div>
                            <div className="region-rounds">
                                {renderRound('east', 0, 'left')}
                                {renderRound('east', 1, 'left')}
                                {renderRound('east', 2, 'left')}
                                {renderRound('east', 3, 'left')}
                            </div>
                        </div>
                    </div>

                    <div className="bracket-center">
                        {/* Empty center space to align with top bracket */}
                    </div>

                    <div className="bracket-right">
                        <div className="region west">
                            <div className="region-label">West</div>
                            {renderRightRegion('west', 'West')}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Render the component to the DOM
ReactDOM.createRoot(document.getElementById('root')).render(<MarchMadnessBracket />); 