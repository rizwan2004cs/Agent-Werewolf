// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// Parimutuel betting for Agent Werewolf games.
/// The off-chain orchestrator opens/freezes/resolves markets.
/// Anyone can bet MON; winners split the whole pool proportionally.
contract WerewolfArena {
    struct Market {
        uint256   gameId;
        uint8     numOptions;
        uint256[] pools;        // staked per option
        uint256   totalPool;
        bool      frozen;
        bool      resolved;
        uint8     winningOption;
    }

    address public operator;    // orchestrator wallet, set at deploy
    uint256 public marketCount;
    mapping(uint256 => Market) public markets;
    // marketId => bettor => option => amount staked
    mapping(uint256 => mapping(address => mapping(uint8 => uint256))) public stakeOf;
    mapping(uint256 => mapping(address => bool)) public claimed;

    event MarketOpened(uint256 marketId, uint256 gameId);
    event BetPlaced(uint256 marketId, address bettor, uint8 optionIdx, uint256 amount);
    event MarketFrozen(uint256 marketId);
    event MarketResolved(uint256 marketId, uint8 winningOption);
    event Claimed(uint256 marketId, address bettor, uint256 payout);

    modifier onlyOperator() { require(msg.sender == operator, "not operator"); _; }

    constructor() { operator = msg.sender; }

    function openMarket(uint256 gameId, uint8 numOptions)
        external onlyOperator returns (uint256 marketId)
    {
        marketId = marketCount++;
        Market storage m = markets[marketId];
        m.gameId = gameId;
        m.numOptions = numOptions;
        m.pools = new uint256[](numOptions);
        emit MarketOpened(marketId, gameId);
    }

    function placeBet(uint256 marketId, uint8 optionIdx) external payable {
        Market storage m = markets[marketId];
        require(!m.frozen && !m.resolved, "closed");
        require(optionIdx < m.numOptions, "bad option");
        require(msg.value > 0, "no stake");
        m.pools[optionIdx] += msg.value;
        m.totalPool += msg.value;
        stakeOf[marketId][msg.sender][optionIdx] += msg.value;
        emit BetPlaced(marketId, msg.sender, optionIdx, msg.value);
    }

    function freezeMarket(uint256 marketId) external onlyOperator {
        markets[marketId].frozen = true;
        emit MarketFrozen(marketId);
    }

    function resolveMarket(uint256 marketId, uint8 winningOption) external onlyOperator {
        Market storage m = markets[marketId];
        require(!m.resolved, "resolved");
        m.resolved = true;
        m.winningOption = winningOption;
        emit MarketResolved(marketId, winningOption);
    }

    /// Winners split the entire pool proportional to their stake on the winning option.
    function claimWinnings(uint256 marketId) external {
        Market storage m = markets[marketId];
        require(m.resolved, "unresolved");
        require(!claimed[marketId][msg.sender], "already claimed");
        uint256 myStake = stakeOf[marketId][msg.sender][m.winningOption];
        require(myStake > 0, "nothing to claim");
        uint256 winPool = m.pools[m.winningOption];
        uint256 payout = winPool == 0 ? 0 : (m.totalPool * myStake) / winPool;
        claimed[marketId][msg.sender] = true;
        (bool ok, ) = payable(msg.sender).call{value: payout}("");
        require(ok, "transfer failed");
        emit Claimed(marketId, msg.sender, payout);
    }

    function getPools(uint256 marketId) external view returns (uint256[] memory) {
        return markets[marketId].pools;
    }

    function getMarket(uint256 marketId)
        external view
        returns (uint256 gameId, uint8 numOptions, uint256 totalPool, bool frozen, bool resolved, uint8 winningOption)
    {
        Market storage m = markets[marketId];
        return (m.gameId, m.numOptions, m.totalPool, m.frozen, m.resolved, m.winningOption);
    }
}
