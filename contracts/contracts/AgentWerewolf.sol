// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title AgentWerewolf
/// @notice Minimal on-chain referee for an Agent Werewolf game. The orchestrator
///         (Person B) drives phases; the chain provides an immutable record of
///         role commitments, votes, eliminations, payouts.
///
/// Fairness model (hackathon-pragmatic, per docs/workstream-A):
///  - Roles are committed as hashes in createGame BEFORE the game starts.
///  - revealRole() opens a commitment with keccak256(role, idx, salt) so any
///    elimination / win can be audited after the fact.
///  - The orchestrator is the trusted runner: it declares the winner once the
///    village/wolf condition is met. The chain still guarantees nobody changed
///    a role after commit, nobody changed a vote, and the pot pays the right team.
contract AgentWerewolf {
    enum Phase { Night, Day, Ended }
    enum Team  { None, Wolf, Village }
    enum Role  { Unknown, Wolf, Villager, Seer }

    struct Game {
        address[]  players;
        bytes32[]  roleHashes;
        bool[]     alive;
        uint8[]    revealed;     // Role enum value per player, 0 = not yet revealed
        uint256    pot;
        Phase      phase;
        uint8      round;
        bytes32    nightKillHash;
        bool       killRevealed;
        Team       winner;
        bool       prizeClaimed;
    }

    mapping(uint256 => Game) public games;
    mapping(uint256 => mapping(address => uint8)) public voteOf; // voter => targetIdx+1 (0 = not voted)
    mapping(uint256 => uint256[]) public tally;                  // votes per player idx
    uint256 public gameCount;

    event GameCreated(uint256 gameId, uint256 pot);
    event NightKillCommitted(uint256 gameId);
    event RoleRevealed(uint256 gameId, uint8 playerIdx, uint8 role);
    event PlayerEliminated(uint256 gameId, uint8 playerIdx, bool wasWolf);
    event VoteCast(uint256 gameId, address voter, uint8 targetIdx);
    event Winner(uint256 gameId, uint8 team);

    // ---------------------------------------------------------------- lifecycle

    function createGame(address[] calldata players, bytes32[] calldata roleHashes)
        external payable returns (uint256 gameId)
    {
        require(players.length == roleHashes.length, "len mismatch");
        require(players.length > 0, "no players");
        gameId = gameCount++;
        Game storage g = games[gameId];
        g.players = players;
        g.roleHashes = roleHashes;
        g.pot = msg.value;
        g.phase = Phase.Night;
        g.round = 1;
        for (uint256 i = 0; i < players.length; i++) {
            g.alive.push(true);
            g.revealed.push(uint8(Role.Unknown));
        }
        tally[gameId] = new uint256[](players.length);
        emit GameCreated(gameId, msg.value);
    }

    /// @notice Open a role commitment so eliminations / wins are auditable.
    function revealRole(uint256 gameId, uint8 idx, uint8 role, bytes32 salt) external {
        Game storage g = games[gameId];
        require(idx < g.players.length, "bad idx");
        require(
            keccak256(abi.encodePacked(role, idx, salt)) == g.roleHashes[idx],
            "bad role reveal"
        );
        g.revealed[idx] = role;
        emit RoleRevealed(gameId, idx, role);
    }

    // ------------------------------------------------------------------- night

    function commitNightKill(uint256 gameId, bytes32 killHash) external {
        Game storage g = games[gameId];
        require(g.phase == Phase.Night, "not night");
        g.nightKillHash = killHash;
        g.killRevealed = false;
        emit NightKillCommitted(gameId);
    }

    function revealNightKill(uint256 gameId, uint8 victimIdx, bytes32 salt) external {
        Game storage g = games[gameId];
        require(
            keccak256(abi.encodePacked(victimIdx, salt)) == g.nightKillHash,
            "bad reveal"
        );
        require(g.alive[victimIdx], "already dead");
        g.alive[victimIdx] = false;
        g.killRevealed = true;
        g.phase = Phase.Day;
        emit PlayerEliminated(gameId, victimIdx, false); // role-agnostic at night
    }

    // -------------------------------------------------------------------- vote

    function submitVote(uint256 gameId, uint8 targetIdx) external {
        Game storage g = games[gameId];
        require(g.phase == Phase.Day, "not day");
        require(targetIdx < g.players.length, "bad target");
        require(_isPlayer(g, msg.sender), "not a player");
        require(voteOf[gameId][msg.sender] == 0, "already voted");
        voteOf[gameId][msg.sender] = targetIdx + 1;
        tally[gameId][targetIdx]++;
        emit VoteCast(gameId, msg.sender, targetIdx);
    }

    function resolveVote(uint256 gameId) external {
        Game storage g = games[gameId];
        require(g.phase == Phase.Day, "not day");

        // find max-voted alive player
        uint8 out;
        uint256 best;
        bool any;
        for (uint8 i = 0; i < g.players.length; i++) {
            if (g.alive[i] && tally[gameId][i] > best) {
                best = tally[gameId][i];
                out = i;
                any = true;
            }
        }

        if (any) {
            g.alive[out] = false;
            bool wasWolf = _verifyWolf(g, out);
            emit PlayerEliminated(gameId, out, wasWolf);
        }

        // reset tally + per-voter record for next round
        for (uint8 i = 0; i < g.players.length; i++) {
            tally[gameId][i] = 0;
            voteOf[gameId][g.players[i]] = 0;
        }

        if (g.phase != Phase.Ended) {
            g.round++;
            g.phase = Phase.Night;
        }
    }

    /// @notice Orchestrator (referee) declares the winning team once the
    ///         alive-wolves vs alive-villagers condition is met. Reveal the
    ///         relevant roles first so claimPrize can validate winners.
    function declareWinner(uint256 gameId, uint8 team) external {
        Game storage g = games[gameId];
        require(team == uint8(Team.Wolf) || team == uint8(Team.Village), "bad team");
        g.winner = Team(team);
        g.phase = Phase.Ended;
        emit Winner(gameId, team);
    }

    // ------------------------------------------------------------------ payout

    function claimPrize(uint256 gameId) external {
        Game storage g = games[gameId];
        require(g.phase == Phase.Ended, "not over");
        require(!g.prizeClaimed, "claimed");
        require(_onWinningTeam(g, msg.sender), "not winner");
        g.prizeClaimed = true;
        payable(msg.sender).transfer(g.pot);
    }

    function forceEnd(uint256 gameId) external {
        games[gameId].phase = Phase.Ended;
    }

    // ------------------------------------------------------------------- views

    function getPlayers(uint256 gameId) external view returns (address[] memory) {
        return games[gameId].players;
    }

    function getAlive(uint256 gameId) external view returns (bool[] memory) {
        return games[gameId].alive;
    }

    function getTally(uint256 gameId) external view returns (uint256[] memory) {
        return tally[gameId];
    }

    // ----------------------------------------------------------------- helpers

    function _isPlayer(Game storage g, address a) internal view returns (bool) {
        for (uint256 i = 0; i < g.players.length; i++) {
            if (g.players[i] == a) return true;
        }
        return false;
    }

    function _verifyWolf(Game storage g, uint8 idx) internal view returns (bool) {
        return g.revealed[idx] == uint8(Role.Wolf);
    }

    function _onWinningTeam(Game storage g, address a) internal view returns (bool) {
        if (g.winner == Team.None) return false;
        for (uint8 i = 0; i < g.players.length; i++) {
            if (g.players[i] != a) continue;
            uint8 r = g.revealed[i];
            if (g.winner == Team.Wolf) {
                return r == uint8(Role.Wolf);
            }
            // Village team = villager + seer
            return r == uint8(Role.Villager) || r == uint8(Role.Seer);
        }
        return false;
    }
}
