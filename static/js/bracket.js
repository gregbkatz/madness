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
        finalFour: [null, null],
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
            newBracket[region][nextRound][nextGameIndex * 2 + nextTeamIndex] = selectedTeam;

            // Clear subsequent rounds that might be affected by this change
            for (let r = nextRound + 1; r < 4; r++) {
                const gameIdx = Math.floor(nextGameIndex / Math.pow(2, r - nextRound));
                const teamIdx = (nextGameIndex / Math.pow(2, r - nextRound)) % 1 > 0 ? 1 : 0;
                newBracket[region][r][gameIdx * 2 + teamIdx] = null;
            }

            // Clear Final Four if Elite Eight winners are changed
            if (nextRound === 3) {
                if (region === 'west') newBracket.finalFour[0] = null;
                if (region === 'east') newBracket.finalFour[0] = null;
                if (region === 'south') newBracket.finalFour[1] = null;
                if (region === 'midwest') newBracket.finalFour[1] = null;

                // Also clear championship and champion
                newBracket.championship = [null, null];
                newBracket.champion = null;
            }
        }
        // Handle Elite Eight to Final Four advancement
        else if (round === 3) {
            // Update Final Four based on region
            if (region === 'west') newBracket.finalFour[0] = selectedTeam;
            if (region === 'east') newBracket.finalFour[0] = selectedTeam;
            if (region === 'south') newBracket.finalFour[1] = selectedTeam;
            if (region === 'midwest') newBracket.finalFour[1] = selectedTeam;

            // Clear championship if this region's Final Four team changes
            if ((region === 'west' || region === 'east')) {
                newBracket.championship[0] = null;
            } else {
                newBracket.championship[1] = null;
            }

            // Clear champion
            newBracket.champion = null;
        }

        setBracket(newBracket);
    };

    // Handle Final Four team selection
    const handleFinalFourSelect = (semifinalIndex, teamIndex) => {
        if (!bracket.finalFour[semifinalIndex]) return;

        const newBracket = { ...bracket };
        newBracket.championship[semifinalIndex] = bracket.finalFour[semifinalIndex];
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
    const renderTeam = (team, onClick, isWinner = false) => {
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
    const renderGame = (region, round, gameIndex, topTeam, bottomTeam) => {
        const isWinnerTop = round < 3 && bracket[region][round + 1] &&
            bracket[region][round + 1][Math.floor(gameIndex / 2) * 2 + gameIndex % 2] === topTeam;

        const isWinnerBottom = round < 3 && bracket[region][round + 1] &&
            bracket[region][round + 1][Math.floor(gameIndex / 2) * 2 + gameIndex % 2] === bottomTeam;

        return (
            <div className="game">
                {renderTeam(
                    topTeam,
                    () => handleTeamSelect(region, round, gameIndex, 0),
                    isWinnerTop
                )}
                {renderTeam(
                    bottomTeam,
                    () => handleTeamSelect(region, round, gameIndex, 1),
                    isWinnerBottom
                )}
            </div>
        );
    };

    // Calculate the appropriate spacing for games in each round
    const getGameWrapperStyle = (round) => {
        // Returns empty object for first round, appropriate margins for later rounds
        if (round === 0) return {};

        const spacingFactor = Math.pow(2, round);
        return {
            marginBottom: `${spacingFactor * 20}px`
        };
    };

    // Render a full round of games for a region
    const renderRound = (region, round, alignment) => {
        const games = [];
        const gamesInRound = Math.pow(2, 3 - round);

        for (let i = 0; i < gamesInRound; i++) {
            const gameIndex = i;
            const topTeamIndex = gameIndex * 2;
            const bottomTeamIndex = gameIndex * 2 + 1;

            games.push(
                <div key={`${region}-${round}-${i}`} className="game-wrapper" style={getGameWrapperStyle(round)}>
                    {renderGame(
                        region,
                        round,
                        gameIndex,
                        bracket[region][round][topTeamIndex],
                        bracket[region][round][bottomTeamIndex]
                    )}
                </div>
            );
        }

        return (
            <div className={`round round-${alignment}`}>
                {games}
            </div>
        );
    };

    // Render Final Four and Championship
    const renderFinalFour = () => {
        return (
            <div className="final-four">
                <div className="final-four-matchup">
                    {renderTeam(
                        bracket.finalFour[0],
                        () => handleFinalFourSelect(0, 0),
                        bracket.championship[0] === bracket.finalFour[0]
                    )}
                    {renderTeam(
                        bracket.finalFour[1],
                        () => handleFinalFourSelect(1, 0),
                        bracket.championship[1] === bracket.finalFour[1]
                    )}
                </div>

                <div className="championship">
                    <div className="championship-header">CHAMPIONSHIP</div>
                    <div className="championship-matchup">
                        {renderTeam(
                            bracket.championship[0],
                            () => handleChampionshipSelect(0),
                            bracket.champion === bracket.championship[0]
                        )}
                        {renderTeam(
                            bracket.championship[1],
                            () => handleChampionshipSelect(1),
                            bracket.champion === bracket.championship[1]
                        )}
                    </div>

                    {bracket.champion && (
                        <div className="champion-display">
                            <div className="champion-label">CHAMPION</div>
                            <div className="champion-name">
                                {bracket.champion.name}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        );
    };

    // Render the Round Headers
    const renderRoundHeaders = () => {
        return (
            <div className="round-headers">
                <div className="round-header">1st Round</div>
                <div className="round-header">2nd Round</div>
                <div className="round-header">Sweet 16</div>
                <div className="round-header">Elite Eight</div>
                <div className="round-header">Final Four</div>
                <div className="round-header">Championship</div>
                <div className="round-header">Final Four</div>
                <div className="round-header">Elite Eight</div>
                <div className="round-header">Sweet 16</div>
                <div className="round-header">2nd Round</div>
                <div className="round-header">1st Round</div>
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
                            {renderRound('south', 0, 'left')}
                            {renderRound('south', 1, 'left')}
                            {renderRound('south', 2, 'left')}
                            {renderRound('south', 3, 'left')}
                        </div>
                    </div>

                    <div className="bracket-center">
                        {renderFinalFour()}
                    </div>

                    <div className="bracket-right">
                        <div className="region midwest">
                            <div className="region-label">Midwest</div>
                            {renderRound('midwest', 3, 'right')}
                            {renderRound('midwest', 2, 'right')}
                            {renderRound('midwest', 1, 'right')}
                            {renderRound('midwest', 0, 'right')}
                        </div>
                    </div>
                </div>

                <div className="bracket">
                    <div className="bracket-left">
                        <div className="region east">
                            <div className="region-label">East</div>
                            {renderRound('east', 0, 'left')}
                            {renderRound('east', 1, 'left')}
                            {renderRound('east', 2, 'left')}
                            {renderRound('east', 3, 'left')}
                        </div>
                    </div>

                    <div className="bracket-center">
                        {/* Empty center space to align with top bracket */}
                    </div>

                    <div className="bracket-right">
                        <div className="region west">
                            <div className="region-label">West</div>
                            {renderRound('west', 3, 'right')}
                            {renderRound('west', 2, 'right')}
                            {renderRound('west', 1, 'right')}
                            {renderRound('west', 0, 'right')}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// Render the component to the DOM
ReactDOM.createRoot(document.getElementById('root')).render(<MarchMadnessBracket />); 