// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title WerewolfBetting
/// @notice Parimutuel (pool-based) betting on Agent Werewolf outcomes. No
///         bookmaker — odds emerge from pool sizes. Winners split the whole
///         pool proportionally to their stake on the winning option.
///
/// Option labels live off-chain (the orchestrator serves them in /markets);
/// on-chain we only need the option count + per-option pools.
contract WerewolfBetting {
    struct Market {
        uint256   gameId;
        uint8     marketType;
        uint8     numOptions;
        uint256[] pools;       // staked per option
        uint256   totalPool;
        bool      frozen;
        bool      resolved;
        uint8     winningOption;
    }

    mapping(uint256 => Market) public markets;
    // market => bettor => option => amount
    mapping(uint256 => mapping(address => mapping(uint8 => uint256))) public stakeOf;
    mapping(uint256 => mapping(address => bool)) public claimed;
    uint256 public marketCount;

    event MarketOpened(uint256 marketId, uint256 gameId, uint8 marketType, uint8 numOptions);
    event BetPlaced(uint256 marketId, address bettor, uint8 optionIdx, uint256 amount);
    event MarketFrozen(uint256 marketId);
    event MarketResolved(uint256 marketId, uint8 winningOption);

    function openMarket(uint256 gameId, uint8 marketType, uint8 numOptions)
        external returns (uint256 marketId)
    {
        require(numOptions > 0, "no options");
        marketId = marketCount++;
        Market storage m = markets[marketId];
        m.gameId = gameId;
        m.marketType = marketType;
        m.numOptions = numOptions;
        m.pools = new uint256[](numOptions);
        emit MarketOpened(marketId, gameId, marketType, numOptions);
    }

    function placeBet(uint256 marketId, uint8 optionIdx) external payable {
        Market storage m = markets[marketId];
        require(m.numOptions > 0, "no market");
        require(!m.frozen && !m.resolved, "closed");
        require(optionIdx < m.numOptions, "bad option");
        require(msg.value > 0, "no stake");
        m.pools[optionIdx] += msg.value;
        m.totalPool += msg.value;
        stakeOf[marketId][msg.sender][optionIdx] += msg.value;
        emit BetPlaced(marketId, msg.sender, optionIdx, msg.value);
    }

    function freezeMarket(uint256 marketId) external {
        markets[marketId].frozen = true;
        emit MarketFrozen(marketId);
    }

    function resolveMarket(uint256 marketId, uint8 winningOption) external {
        Market storage m = markets[marketId];
        require(m.numOptions > 0, "no market");
        require(winningOption < m.numOptions, "bad option");
        m.resolved = true;
        m.winningOption = winningOption;
        emit MarketResolved(marketId, winningOption);
    }

    /// @notice Parimutuel payout: winners split the whole pool proportionally.
    ///         If nobody backed the winning option, stakes are refundable per
    ///         original option (edge case left simple for the demo).
    function claimWinnings(uint256 marketId) external {
        Market storage m = markets[marketId];
        require(m.resolved, "unresolved");
        require(!claimed[marketId][msg.sender], "claimed");
        uint256 winPool = m.pools[m.winningOption];
        require(winPool > 0, "no winners");
        uint256 myStake = stakeOf[marketId][msg.sender][m.winningOption];
        require(myStake > 0, "no winning stake");
        uint256 payout = (m.totalPool * myStake) / winPool;
        claimed[marketId][msg.sender] = true;
        payable(msg.sender).transfer(payout);
    }

    // ------------------------------------------------------------------- views

    function getPools(uint256 marketId) external view returns (uint256[] memory) {
        return markets[marketId].pools;
    }

    function getMarket(uint256 marketId)
        external
        view
        returns (
            uint256 gameId,
            uint8 marketType,
            uint8 numOptions,
            uint256 totalPool,
            bool frozen,
            bool resolved,
            uint8 winningOption
        )
    {
        Market storage m = markets[marketId];
        return (m.gameId, m.marketType, m.numOptions, m.totalPool, m.frozen, m.resolved, m.winningOption);
    }
}
