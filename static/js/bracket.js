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

    // Fetch initial data
    React.useEffect(() => {
        // Fetch teams
        fetch('/api/teams')
            .then(response => response.json())
            .then(data => {
                setTeams(data);
            })
            .catch(error => console.error('Error fetching teams:', error));

        // Fetch current bracket state
        fetch('/api/bracket')
            .then(response => response.json())
            .then(data => {
                console.log('Bracket fetched:', data);
                setBracket(data);
            })
            .catch(error => console.error('Error fetching bracket:', error));
    }, []);

    // Function to handle team selection in regular rounds
    const handleTeamSelect = (region, round, gameIndex, teamIndex) => {
        fetch('/api/bracket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'select_team',
                region: region,
                round: round,
                gameIndex: gameIndex,
                teamIndex: teamIndex
            })
        })
            .then(response => response.json())
            .then(data => {
                console.log('Updated bracket:', data);
                setBracket(data);
            })
            .catch(error => console.error('Error updating bracket:', error));
    };

    // Handle Final Four team selection
    const handleFinalFourSelect = (semifinalIndex, teamIndex) => {
        fetch('/api/bracket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'select_final_four',
                semifinalIndex: semifinalIndex,
                teamIndex: teamIndex
            })
        })
            .then(response => response.json())
            .then(data => {
                console.log('Updated bracket after Final Four selection:', data);
                setBracket(data);
            })
            .catch(error => console.error('Error updating bracket:', error));
    };

    // Handle Championship team selection
    const handleChampionshipSelect = (teamIndex) => {
        fetch('/api/bracket', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                action: 'select_championship',
                teamIndex: teamIndex
            })
        })
            .then(response => response.json())
            .then(data => {
                console.log('Updated bracket after Championship selection:', data);
                setBracket(data);
            })
            .catch(error => console.error('Error updating bracket:', error));
    };

    // Auto-fill the bracket
    const autoFillBracket = () => {
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
            })
            .catch(error => console.error('Error auto-filling bracket:', error));
    };

    // Reset the bracket
    const resetBracket = () => {
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
            })
            .catch(error => console.error('Error resetting bracket:', error));
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

    // Render a single team box
    const renderTeam = (team, onClick, isWinner = false, isRightRegion = false, teamName = '') => {
        // Create a stable onClick handler even for TBD teams
        const handleClick = (e) => {
            // Stop propagation to prevent parent elements from capturing the click
            e.stopPropagation();

            // Log the click for debugging
            if (team) {
                console.log(`Team clicked: ${team.name} (${team.seed})`);
            } else {
                console.log(`Empty team clicked`);
            }

            // Execute the provided onClick handler
            if (onClick && typeof onClick === 'function') {
                onClick();
            }
        };

        if (!team) {
            return (
                <div
                    className="team empty"
                    style={{
                        cursor: 'pointer',
                        padding: '4px 8px',
                        margin: '2px 0',
                        border: '1px dashed #ccc',
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        backgroundColor: '#f9f9f9',
                        color: '#999',
                        pointerEvents: 'auto',
                        minHeight: '20px'
                    }}
                    onClick={handleClick}
                >
                    <span className="seed"></span>
                    <span className="team-name"></span>
                </div>
            );
        }

        // Apply the winner class if selected
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
        // Determine if each team is the winner by checking if they appear in the next round
        let isWinnerTop = false;
        let isWinnerBottom = false;

        if (round < 3 && bracket[region][round + 1]) {
            // For regular rounds, check next round
            const nextRoundIndex = Math.floor(gameIndex / 2);
            if (topTeam && bracket[region][round + 1][nextRoundIndex] === topTeam) {
                isWinnerTop = true;
            }
            if (bottomTeam && bracket[region][round + 1][nextRoundIndex] === bottomTeam) {
                isWinnerBottom = true;
            }
        } else if (round === 3) {
            // For Elite Eight, check Final Four
            const ffIndex = getRegionFinalFourIndex(region);
            if (topTeam && bracket.finalFour[ffIndex] === topTeam) {
                isWinnerTop = true;
            }
            if (bottomTeam && bracket.finalFour[ffIndex] === bottomTeam) {
                isWinnerBottom = true;
            }
        }

        return (
            <div className="game" key={`game-${region}-${round}-${gameIndex}`}>
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
            <div key={`round-${region}-${round}`} className={`round round-${alignment}`} data-round={round}>
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
            backgroundColor: '#e8f5e9',
            borderRadius: '8px',
            boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
            border: '2px solid #4caf50',
            textAlign: 'center',
            maxWidth: '200px'
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

        // Check if teams are winners in Final Four
        const isSouthWinner = bracket.championship[0] === bracket.finalFour[2];
        const isEastWinner = bracket.championship[0] === bracket.finalFour[1];
        const isMidwestWinner = bracket.championship[1] === bracket.finalFour[3];
        const isWestWinner = bracket.championship[1] === bracket.finalFour[0];

        // Check if teams are winners in Championship
        const isChamp1Winner = bracket.champion === bracket.championship[0];
        const isChamp2Winner = bracket.champion === bracket.championship[1];

        return (
            <div className="final-four" style={{ position: 'relative', zIndex: 1 }}>
                <div className="final-four-content">
                    {/* Champion Display Box - Now positioned ABOVE the championship */}
                    <div style={championDisplayStyle}>
                        <div style={{ marginBottom: '10px' }}>
                            <span role="img" aria-label="trophy" style={{ fontSize: '24px' }}>🏆</span>
                            <div style={{ fontWeight: 'bold', fontSize: '16px', color: '#2e7d32' }}>Champion</div>
                        </div>
                        {bracket.champion ? (
                            <div style={{
                                padding: '10px',
                                backgroundColor: 'white',
                                borderRadius: '4px',
                                border: '1px solid #4caf50'
                            }}>
                                <div style={{ fontWeight: 'bold' }}>{bracket.champion.name}</div>
                                <div>Seed: {bracket.champion.seed}</div>
                            </div>
                        ) : (
                            <div style={{
                                padding: '10px',
                                backgroundColor: 'white',
                                borderRadius: '4px',
                                border: '1px solid #ccc',
                                color: '#999',
                                fontStyle: 'italic'
                            }}>
                                TBD
                            </div>
                        )}
                    </div>

                    {/* Display the Final Four matchups side by side in a pyramid structure */}
                    <div className="semifinal-container">
                        {/* Left side semifinal - South vs East */}
                        <div className="semifinal-matchup left-semifinal" style={semifinalStyle}>
                            <div style={{ textAlign: 'center', fontWeight: 'bold', marginBottom: '10px', fontSize: '14px' }}>South/East Semifinal</div>
                            <div style={{ pointerEvents: 'auto' }}>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        bracket.finalFour[2], // South champion
                                        handleSouthClick,
                                        isSouthWinner
                                    )}
                                </div>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        bracket.finalFour[1], // East champion
                                        handleEastClick,
                                        isEastWinner
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
                                        isChamp1Winner
                                    )}
                                </div>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        bracket.championship[1], // Winner of Midwest/West
                                        handleChampionship2Click,
                                        isChamp2Winner
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
                                        isMidwestWinner
                                    )}
                                </div>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        bracket.finalFour[0], // West champion
                                        handleWestClick,
                                        isWestWinner
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
                            onClick={resetBracket}
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
                            Reset Bracket
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