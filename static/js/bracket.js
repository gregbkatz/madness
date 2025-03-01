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
        console.log(`Team select: region=${region}, round=${round}, game=${gameIndex}, team=${teamIndex}`);

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
            })
            .catch(error => console.error('Error updating bracket:', error));
    };

    // Handle Final Four Selection
    const handleFinalFourSelect = (semifinalIndex, teamIndex, region) => {
        console.log(`Final Four select: semifinalIndex=${semifinalIndex}, teamIndex=${teamIndex}, region=${region}`);

        // If the team is already in the finalFour array at the correct slot index, then we should be updating the Championship
        const slotIndex = getRegionFinalFourIndex(region);
        const currentTeam = bracket.finalFour[slotIndex];

        if (currentTeam) {
            // Determine which Championship slot this team should go to
            // South/East teams go to Championship slot 0, West/Midwest go to slot 1
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
            })
            .catch(error => console.error('Error updating bracket:', error));
    };

    // Handle Champion selection
    const handleChampionSelect = (slotIndex) => {
        console.log(`Champion select: slotIndex=${slotIndex}`);

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
                console.log('Updated bracket after Champion selection:', data);
                setBracket(data);
            })
            .catch(error => console.error('Error selecting champion:', error));
    };

    // Handle Championship team selection
    const handleChampionshipSelect = (teamIndex) => {
        console.log(`Championship select: teamIndex=${teamIndex}`);

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
                })
                .catch(error => console.error('Error selecting champion:', error));
        }
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

    // Random-fill the bracket (completely random picks)
    const randomFillBracket = () => {
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
            })
            .catch(error => console.error('Error randomly filling bracket:', error));
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

    // Render a team box
    const renderTeam = (team, isWinner, onClick, isTBD = false) => {
        // If no team data, return empty box
        if (!team) {
            return <div className="team tbd">TBD</div>;
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
                <div style={teamStyle} className="team tbd">
                    TBD
                </div>
            );
        }

        return (
            <div
                style={teamStyle}
                className={`team ${isWinner ? 'winner' : ''}`}
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
                        {team.name}
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

        return (
            <div className="game" key={`game-${region}-${round}-${gameIndex}`}>
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
            backgroundColor: '#e8f5e9',
            borderRadius: '8px',
            boxShadow: '0 4px 8px rgba(0,0,0,0.1)',
            border: '2px solid #4caf50',
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

        const handleEastClick = () => {
            console.log("East team clicked in Final Four!");
            // East team will be in finalFour[1]
            if (bracket.finalFour && bracket.finalFour[1]) {
                // If team already exists, this should update the championship
                handleFinalFourSelect(0, 0, 'east');
            } else {
                // Otherwise, get the team from the Elite Eight
                handleFinalFourSelect(0, 0, 'east');
            }
        };

        const handleMidwestClick = () => {
            console.log("Midwest team clicked in Final Four!");
            // Midwest team will be in finalFour[3]
            if (bracket.finalFour && bracket.finalFour[3]) {
                // If team already exists, this should update the championship
                handleFinalFourSelect(1, 0, 'midwest');
            } else {
                // Otherwise, get the team from the Elite Eight
                handleFinalFourSelect(1, 0, 'midwest');
            }
        };

        const handleWestClick = () => {
            console.log("West team clicked in Final Four!");
            // West team will be in finalFour[0]
            if (bracket.finalFour && bracket.finalFour[0]) {
                // If team already exists, this should update the championship
                handleFinalFourSelect(1, 0, 'west');
            } else {
                // Otherwise, get the team from the Elite Eight
                handleFinalFourSelect(1, 0, 'west');
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
        const isEastWinner = bracket.winners && bracket.winners.finalFour && bracket.winners.finalFour.includes(1);
        const isMidwestWinner = bracket.winners && bracket.winners.finalFour && bracket.winners.finalFour.includes(3);
        const isWestWinner = bracket.winners && bracket.winners.finalFour && bracket.winners.finalFour.includes(0);

        // Check if teams are winners in Championship
        const isChamp1Winner = bracket.winners && bracket.winners.championship && bracket.winners.championship.includes(0);
        const isChamp2Winner = bracket.winners && bracket.winners.championship && bracket.winners.championship.includes(1);

        // Safely access Final Four and Championship data with fallbacks
        const finalFour = bracket.finalFour || [null, null, null, null];
        const championship = bracket.championship || [null, null];

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
                                border: '1px solid #4caf50',
                                cursor: 'pointer'
                            }}
                            >
                                <div style={{ fontWeight: 'bold', fontSize: '16px' }}>{bracket.champion.name} ({bracket.champion.seed})</div>
                            </div>
                        ) : (
                            <div style={{
                                padding: '10px',
                                backgroundColor: 'white',
                                borderRadius: '4px',
                                border: '1px solid #ccc',
                                minHeight: '24px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center'
                            }}>
                                <div style={{ fontSize: '16px', color: '#aaa', fontStyle: 'italic' }}>TBD</div>
                            </div>
                        )}
                    </div>

                    {/* Display the Final Four matchups side by side in a pyramid structure */}
                    <div className="semifinal-container">
                        {/* Left side semifinal - South vs East */}
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
                                        finalFour[1], // East champion
                                        isEastWinner,
                                        handleEastClick,
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
                                        championship[0], // Winner of South/East
                                        isChamp1Winner,
                                        handleChampionship1Click,
                                        false
                                    )}
                                </div>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        championship[1], // Winner of Midwest/West
                                        isChamp2Winner,
                                        handleChampionship2Click,
                                        false
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Right side semifinal - Midwest vs West */}
                        <div className="semifinal-matchup right-semifinal" style={semifinalStyle}>
                            <div style={{ textAlign: 'center', fontWeight: 'bold', marginBottom: '10px', fontSize: '14px' }}></div>
                            <div style={{ pointerEvents: 'auto' }}>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        finalFour[3], // Midwest champion
                                        isMidwestWinner,
                                        handleMidwestClick,
                                        false
                                    )}
                                </div>
                                <div style={{ margin: '5px 0' }}>
                                    {renderTeam(
                                        finalFour[0], // West champion
                                        isWestWinner,
                                        handleWestClick,
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
                <div style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    marginBottom: '15px',
                    flexWrap: 'wrap',
                    width: '100%'
                }}>
                    <div style={{
                        display: 'flex',
                        flexDirection: 'row',
                        justifyContent: 'center',
                        flexWrap: 'wrap',
                        gap: '10px'
                    }}>
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
                            Auto-Fill Bracket
                        </button>

                        <button
                            onClick={randomFillBracket}
                            style={{
                                padding: '8px 16px',
                                backgroundColor: '#6a1b9a',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontWeight: 'bold',
                                fontSize: '14px'
                            }}
                        >
                            Random Picks
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