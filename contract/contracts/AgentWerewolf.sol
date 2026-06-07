// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title AgentWerewolf
/// @notice Immutable, operator-written record of an Agent Werewolf game. The
///         orchestrator runs the game off-chain and writes each event here so
///         roles (committed as hashes before the game), kills, votes, and the
///         winner are permanent and auditable on Monad. One operator key signs
///         all writes — the "agents" are not real wallets.
contract AgentWerewolf {
    enum Team { None, Wolves, Village }

    struct Game {
        bytes32[] roleHashes;   // commit: keccak256(abi.encodePacked(role, idx, salt))
        bool[]    alive;
        uint8[]   revealedRole; // 0 = hidden; opened via revealRole
        Team      winner;
        bool      exists;
    }

    address public operator;
    uint256 public gameCount;
    mapping(uint256 => Game) private games;

    event GameCreated(uint256 gameId, uint8 numPlayers);
    event PlayerKilled(uint256 gameId, uint8 victimIdx);
    event VoteRecorded(uint256 gameId, uint8 voterIdx, uint8 targetIdx);
    event RoleRevealed(uint256 gameId, uint8 idx, uint8 role);
    event WinnerDeclared(uint256 gameId, uint8 team);

    modifier onlyOperator() {
        require(msg.sender == operator, "not operator");
        _;
    }

    constructor() {
        operator = msg.sender;
    }

    /// @notice Commit the roster's role hashes before the game starts.
    function createGame(bytes32[] calldata roleHashes)
        external onlyOperator returns (uint256 gameId)
    {
        require(roleHashes.length > 0, "no players");
        gameId = gameCount++;
        Game storage g = games[gameId];
        for (uint256 i = 0; i < roleHashes.length; i++) {
            g.roleHashes.push(roleHashes[i]);
            g.alive.push(true);
            g.revealedRole.push(0);
        }
        g.exists = true;
        emit GameCreated(gameId, uint8(roleHashes.length));
    }

    function recordKill(uint256 gameId, uint8 victimIdx) external onlyOperator {
        Game storage g = games[gameId];
        require(g.exists, "no game");
        require(victimIdx < g.alive.length, "bad idx");
        g.alive[victimIdx] = false;
        emit PlayerKilled(gameId, victimIdx);
    }

    function recordVote(uint256 gameId, uint8 voterIdx, uint8 targetIdx) external onlyOperator {
        Game storage g = games[gameId];
        require(g.exists, "no game");
        require(voterIdx < g.alive.length && targetIdx < g.alive.length, "bad idx");
        emit VoteRecorded(gameId, voterIdx, targetIdx);
    }

    /// @notice Open a role commitment (anyone can verify against the stored hash).
    function revealRole(uint256 gameId, uint8 idx, uint8 role, bytes32 salt) external {
        Game storage g = games[gameId];
        require(g.exists, "no game");
        require(idx < g.roleHashes.length, "bad idx");
        require(
            keccak256(abi.encodePacked(role, idx, salt)) == g.roleHashes[idx],
            "bad reveal"
        );
        g.revealedRole[idx] = role;
        emit RoleRevealed(gameId, idx, role);
    }

    function declareWinner(uint256 gameId, uint8 team) external onlyOperator {
        Game storage g = games[gameId];
        require(g.exists, "no game");
        require(team == uint8(Team.Wolves) || team == uint8(Team.Village), "bad team");
        g.winner = Team(team);
        emit WinnerDeclared(gameId, team);
    }

    // ----------------------------------------------------------------- views --

    function getRoleHashes(uint256 gameId) external view returns (bytes32[] memory) {
        return games[gameId].roleHashes;
    }

    function getAlive(uint256 gameId) external view returns (bool[] memory) {
        return games[gameId].alive;
    }

    function getRevealed(uint256 gameId) external view returns (uint8[] memory) {
        return games[gameId].revealedRole;
    }

    function getWinner(uint256 gameId) external view returns (uint8) {
        return uint8(games[gameId].winner);
    }
}
